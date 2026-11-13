"""Task 3: substitute an ingredient in a recipe, backed by dataset evidence.

Evidence, strongest first (every item cites recipe IDs or counts):
  1. direct        a recipe author lists the swap: "1 cup butter or margarine",
                   "(spinach may be substituted)". Split into the same dish
                   (titles share this recipe's dish words) and other dishes.
  2. similar       near-identical recipes of the same dish (ingredient overlap
                   >= 50%) that lack the target and use X instead. Indirect.
  3. usage pattern ingredients used with the same other ingredients as the
                   target (PPMI cosine over the co-occurrence table). Weakest,
                   indirect, says nothing about this recipe.

Conflict check: substitutes rarely appear in the same recipe as what they
replace (butter + margarine: 77 recipes; butter + sugar: 14,457). If a
candidate often appears together with the target, it is flagged: the data
also suggests it complements rather than replaces the target.

Verified vs predicted: what the dataset shows (these recipes exist and say
this) is verified. That the swap will work in this recipe is a prediction:
the updated ingredient list and instructions are labeled as such, the same
amount is assumed, and steps whose technique depends on the original
ingredient are flagged for review. Nothing here is a medical or allergy
safety claim.

External web search (search_web) is optional and secondary: only on request,
labeled as external, with links.
"""

import math
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from .normalizer import alternatives, clean_line, name_from_segment, normalize_ingredient, strip_noise
from .search import MODIFIED_PRODUCTS, SearchQuery, all_names, db_file, find_matches, name_matches

STAPLES = {"salt", "black pepper", "water"}
SIMILAR_MIN_OVERLAP = 0.5        # Jaccard overlap for "near-identical" recipes
SIMILAR_MAX_EXTRAS = 3           # a similar recipe may differ by at most this many names
SAME_DISH_LIMIT = 400            # recipes compared for the same-dish evidence
SAME_DISH_MIN = 5                # fewer than this: fall back to a shorter dish name
ALT_MIN_RECIPES = 5              # an alternative must be a name used by >= this many recipes
FORM_WORDS = {"dried", "dry", "fresh", "frozen", "canned", "powdered", "free-range", "organic",
              "raw", "cooked", "whole", "large", "small", "homemade", "store-bought", "prepared"}
TOGETHER_CONFLICT = 0.2          # used together in >= 20% of the rarer one's recipes
GENERIC_TITLE_WORDS = {"easy", "best", "quick", "simple", "classic", "homemade", "my", "the",
                       "perfect", "favorite", "delicious", "ultimate", "old", "fashioned",
                       "world's", "mom's", "grandma's", "a", "an", "and", "with", "of", "ii",
                       "iii", "iv", "recipe", "style", "super", "amazing"}
TECHNIQUE_WORDS = {"cream", "creamed", "creaming", "melt", "melted", "soften", "softened",
                   "brown", "browned", "whip", "whipped", "beat", "beaten", "knead", "rise",
                   "sear", "fry", "fried", "emulsify", "temper", "caramelize", "toast",
                   "render", "set", "chill", "whisk", "fold", "rub", "cut in"}
SAFETY_NOTE = ("Recipe text alone cannot show that a substitution is safe for an allergy or a "
               "medical diet. Check product labels, and ask a professional if it matters.")


@dataclass
class Evidence:
    kind: str                       # direct_same_dish | direct_other_dish | similar | usage_pattern
    count: int
    recipe_ids: list[str]           # examples to cite (up to 5)
    detail: str


@dataclass
class Candidate:
    name: str
    evidence: list[Evidence] = field(default_factory=list)
    together: int = 0               # recipes that use both the target and this
    together_rate: float = 0.0
    strength: str = "none"          # strong | moderate | weak | none
    flags: list[str] = field(default_factory=list)
    violates: list[str] = field(default_factory=list)   # user exclusions it breaks

    def count(self, kind: str) -> int:
        return sum(e.count for e in self.evidence if e.kind.startswith(kind))


@dataclass
class Line:
    text: str
    changed: bool = False
    was: str | None = None
    review: str | None = None       # why a changed step should be checked


@dataclass
class SubstitutionResult:
    recipe_id: str
    title: str
    target: str
    target_lines: list[str]         # original ingredient lines being replaced
    same_dish: int                  # same-dish recipes compared
    candidates: list[Candidate]
    chosen: Candidate | None
    ingredients: list[Line] = field(default_factory=list)
    steps: list[Line] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ---------- helpers ----------

def same_thing(target: str, name: str) -> bool:
    """The recipe's name counts as the target ('butter' -> 'unsalted butter' is already 'butter')."""
    return name == target or name_matches(target, name)


def recipe_names(conn, recipe_id: str) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT name FROM ingredients WHERE recipe_id = ? ORDER BY line_no", (recipe_id,))]


def dish_words(title: str) -> str:
    words = [w for w in re.findall(r"[a-z']+", title.lower()) if w not in GENERIC_TITLE_WORDS]
    return " ".join(words)


def same_dish_ids(conn, title: str, recipe_id: str) -> list[str]:
    """Recipes of the same dish: titles containing all of this title's dish words, or,
    if too few, of its last words ("Country Banana Bread" -> "banana bread")."""
    words = dish_words(title).split()
    for start in range(len(words)):
        text = " ".join(words[start:])
        rows, mode = find_matches(conn, SearchQuery(text=text, title_only=True))
        ids = [r[0] for r in rows if r[0] != recipe_id] if mode == "all" else []
        if len(ids) >= SAME_DISH_MIN or start == len(words) - 1:
            return ids[:SAME_DISH_LIMIT]
    return []


def plural(n: int, word: str) -> str:
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def verb(n: int, singular: str, many: str) -> str:
    return singular if n == 1 else many


def excluded_by(name: str, exclude: list[str]) -> list[str]:
    words = {w.rstrip("s") for w in name.split()}
    return [t for t in exclude if {w.rstrip("s") for w in t.split()} <= words]


# ---------- evidence 1: authors' stated alternatives ----------

def parse_alternatives(raw: str) -> list[list[str]]:
    """Groups of interchangeable names stated in one ingredient line."""
    text = clean_line(raw).lower()
    text = re.sub(r"\((?:or|or use|or substitute)\s+([^)]*)\)", r" or \1 ", text)
    groups = []
    m = re.search(r"\(([^()]*?)\s+(?:may|can|could) be substituted[^)]*\)", text)
    if m:
        main = name_from_segment(strip_noise(text[:m.start()]).split(",")[0])
        alt = name_from_segment(m.group(1))
        if main and alt:
            groups.append([main, alt])
    for segment in strip_noise(text).split(","):
        parts = alternatives(segment)
        if len(parts) > 1:
            names = [n for n in (name_from_segment(p) for p in parts) if n]
            if len(set(names)) > 1:
                groups.append(names)
    return groups


def varieties_removed(group: list[str], target: str, every: set[str], common: set[str]) -> list[str]:
    """Drop single words that describe the target rather than replace it:
      - "chicken or duck eggs": "chicken egg" is itself a name, so chicken is a kind of egg
      - "dried or powdered egg whites", "free-range or organic eggs": the word is rarely an
        ingredient on its own (< 50 recipes), so it is an adjective
    "milk or heavy cream" keeps milk: milk is a common ingredient and "milk cream" is not a name."""
    def describes(word: str) -> bool:
        return len(word.split()) == 1 and (word in FORM_WORDS or f"{word} {target}" in every
                                           or word not in common)
    return [n for n in group if not describes(n)]


@lru_cache(maxsize=1)
def known_names(db_path: str) -> frozenset[str]:
    """Names used by enough recipes to be real ingredients (filters parser noise)."""
    conn = sqlite3.connect(db_path)
    try:
        return frozenset(r[0] for r in conn.execute(
            "SELECT name FROM names WHERE n_recipes >= ?", (ALT_MIN_RECIPES,)))
    finally:
        conn.close()


def direct_alternatives(conn, target: str) -> dict[str, list[str]]:
    """alternative name -> recipe IDs whose lines list it as an alternative to the target."""
    word = target.split()[-1]
    rows = conn.execute(
        "SELECT DISTINCT recipe_id, raw FROM ingredients WHERE raw LIKE ? AND "
        "(raw LIKE '% or %' OR raw LIKE '%(or %' OR raw LIKE '%substitut%')", (f"%{word}%",))
    found: dict[str, list[str]] = defaultdict(list)
    known = known_names(db_file(conn))
    every = set(all_names(db_file(conn)))
    common = set(role_matrix(db_file(conn))[0])          # names used by >= 50 recipes
    for recipe_id, raw in rows:
        for group in parse_alternatives(raw):
            if not any(same_thing(target, n) for n in group):
                continue
            for alt in varieties_removed(group, target, every, common):
                if not same_thing(target, alt) and not name_matches(alt, target) \
                        and alt in known and recipe_id not in found[alt]:
                    found[alt].append(recipe_id)
    return found


# ---------- evidence 2: near-identical recipes of the same dish ----------

def similar_swaps(conn, names: list[str], target: str, dish_ids: list[str]) -> dict[str, list[str]]:
    """extra name -> same-dish recipe IDs that lack the target and use it instead."""
    base = {n for n in names if not same_thing(target, n)} - STAPLES
    if not base or not dish_ids:
        return {}
    marks = ",".join("?" * len(dish_ids))
    by_recipe: dict[str, set[str]] = defaultdict(set)
    for rid, name in conn.execute(f"SELECT recipe_id, name FROM ingredients WHERE recipe_id IN ({marks})",
                                  dish_ids):
        by_recipe[rid].add(name)
    found: dict[str, list[str]] = defaultdict(list)
    for rid in dish_ids:
        other = by_recipe.get(rid, set())
        if any(same_thing(target, n) for n in other):
            continue
        other = other - STAPLES
        overlap = len(base & other) / len(base | other) if other else 0.0
        extras = other - base
        if overlap >= SIMILAR_MIN_OVERLAP and 1 <= len(extras) <= SIMILAR_MAX_EXTRAS:
            for e in extras:
                found[e].append(rid)
    return found


# ---------- evidence 3: usage pattern (PPMI cosine over co-occurrence) ----------

@lru_cache(maxsize=1)
def role_matrix(db_path: str):
    """(names, index, PPMI rows normalized to unit length, recipe counts, co-occurrence counts)."""
    conn = sqlite3.connect(db_path)
    try:
        pairs = conn.execute("SELECT a, b, n FROM cooccur").fetchall()
        names = sorted({a for a, _, _ in pairs} | {b for _, b, _ in pairs})
        index = {n: i for i, n in enumerate(names)}
        counts = dict(conn.execute(
            f"SELECT name, n_recipes FROM names WHERE name IN ({','.join('?' * len(names))})", names))
        total = conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    finally:
        conn.close()
    co = np.zeros((len(names), len(names)), dtype=np.float32)
    for a, b, n in pairs:
        co[index[a], index[b]] = co[index[b], index[a]] = n
    n_vec = np.array([counts[n] for n in names], dtype=np.float64)
    with np.errstate(divide="ignore"):
        pmi = np.log((co * total) / np.outer(n_vec, n_vec))
    ppmi = np.where(co > 0, np.maximum(pmi, 0), 0).astype(np.float32)
    norms = np.linalg.norm(ppmi, axis=1, keepdims=True)
    return names, index, ppmi / np.where(norms == 0, 1, norms), n_vec, co


def usage_pattern(conn, target: str, k: int = 8) -> list[tuple[str, float]]:
    """Names whose company of ingredients is most like the target's."""
    names, index, unit, _, _ = role_matrix(db_file(conn))
    if target not in index:
        return []
    sims = unit @ unit[index[target]]
    order = np.argsort(-sims)
    out = []
    for i in order:
        name = names[i]
        if name == target or name in STAPLES or same_thing(target, name) or name_matches(name, target):
            continue
        out.append((name, round(float(sims[i]), 3)))
        if len(out) == k:
            break
    return out


def together_stats(conn, target: str, name: str) -> tuple[int, float]:
    """Recipes using both, and that as a share of the rarer one's recipes."""
    row = conn.execute(
        "SELECT COUNT(DISTINCT a.recipe_id) FROM ingredients a JOIN ingredients b "
        "ON a.recipe_id = b.recipe_id WHERE a.name = ? AND b.name = ?", (target, name)).fetchone()
    counts = dict(conn.execute("SELECT name, n_recipes FROM names WHERE name IN (?, ?)", (target, name)))
    rarer = min(counts.get(target, 0), counts.get(name, 0))
    return row[0], (row[0] / rarer if rarer else 0.0)


# ---------- combining evidence ----------

def grade(c: Candidate) -> None:
    """strong   : the same dish states it twice, or states it once and a near-identical
                  recipe uses it
       moderate : the same dish states it once, 2+ near-identical recipes use it, or 10+
                  other dishes state it
       weak     : a few other dishes, one near-identical recipe, or usage pattern only"""
    same, other, similar = c.count("direct_same"), c.count("direct_other"), c.count("similar")
    if same >= 2 or (same >= 1 and similar >= 1):
        c.strength = "strong"
    elif same == 1 or similar >= 2 or other >= 10:
        c.strength = "moderate"
    elif other or similar or c.count("usage"):
        c.strength = "weak"
    if c.strength != "none" and c.together_rate >= TOGETHER_CONFLICT:
        c.flags.append(f"conflicting: also used together with the target in {plural(c.together, 'recipe')} "
                       f"({c.together_rate:.0%} of the rarer one's recipes), which suggests a "
                       "complement rather than a replacement")
    if other and not same:
        c.flags.append("indirect: the stated alternative comes from other dishes, not this one")
    if c.strength == "weak":
        c.flags.append("weak: little or only indirect evidence")


RANK = {"strong": 0, "moderate": 1, "weak": 2, "none": 3}


def find_candidates(conn, recipe_id: str, title: str, names: list[str], target: str,
                    exclude: list[str], proposed: str | None) -> tuple[list[Candidate], int]:
    dish = same_dish_ids(conn, title, recipe_id)
    dish_set = set(dish)
    cands: dict[str, Candidate] = {}

    def get(name):
        return cands.setdefault(name, Candidate(name=name))

    for alt, ids in direct_alternatives(conn, target).items():
        same = [i for i in ids if i in dish_set]
        other = [i for i in ids if i not in dish_set]
        if same:
            get(alt).evidence.append(Evidence("direct_same_dish", len(same), same[:5],
                                              f"{plural(len(same), 'recipe')} of this dish {verb(len(same), 'lists', 'list')} it as an alternative"))
        if other:
            get(alt).evidence.append(Evidence("direct_other_dish", len(other), other[:5],
                                              f"{plural(len(other), 'recipe')} of other dishes {verb(len(other), 'lists', 'list')} it as an alternative"))
    for extra, ids in similar_swaps(conn, names, target, dish).items():
        get(extra).evidence.append(Evidence("similar", len(ids), ids[:5],
                                            f"{plural(len(ids), 'near-identical recipe')} of this dish "
                                            f"{verb(len(ids), 'uses it and does', 'use it and do')} not use the target"))
    in_recipe = set(names)
    for name, sim in usage_pattern(conn, target):
        if name in in_recipe:                # already in this recipe: not a replacement
            continue
        get(name).evidence.append(Evidence("usage_pattern", 1, [],
                                           f"used with similar ingredients as the target "
                                           f"(similarity {sim:.2f} on a 0-1 scale)"))
    if proposed:
        proposed = (normalize_ingredient(proposed) or [proposed.lower().strip()])[0]
        get(proposed)

    for c in cands.values():
        c.together, c.together_rate = together_stats(conn, target, c.name)
        c.violates = excluded_by(c.name, exclude)
        grade(c)
    ordered = sorted(cands.values(), key=lambda c: (RANK[c.strength], -c.count("direct"),
                                                    -c.count("similar"), c.name))
    return ordered, len(dish)


# ---------- rewriting the recipe ----------

def target_pattern(target: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(target)}(?:s|es)?\b", re.IGNORECASE)


def replace_word(text: str, target: str, sub: str) -> str:
    """Replace the target word, but not inside a different product ('peanut butter')."""
    def swap(m):
        before = text[:m.start()].split()
        if before and f"{before[-1].lower()} {target}" in MODIFIED_PRODUCTS:
            return m.group(0)
        return sub
    return target_pattern(target).sub(swap, text)


def rewrite(conn, recipe: dict, target: str, sub: str) -> tuple[list[Line], list[Line]]:
    """Updated ingredient lines and steps, marking what changed."""
    names_by_line = defaultdict(list)
    for line_no, name in conn.execute("SELECT line_no, name FROM ingredients WHERE recipe_id = ?",
                                      (recipe["recipe_id"],)):
        names_by_line[line_no].append(name)
    ingredients = []
    for i, raw in enumerate(recipe["ingredients"]):
        text = clean_line(raw)
        if not text:
            continue
        if names_by_line[i] and same_thing(target, names_by_line[i][0]):
            new = replace_word(text, target, sub)
            if new == text:                      # target word not literally present
                new = f"{text} -> use {sub} instead"
            ingredients.append(Line(new, changed=True, was=text))
        else:
            ingredients.append(Line(text))
    steps = []
    for para in (p.strip() for p in recipe["instructions"].split("\n")):
        if not para:
            continue
        new = replace_word(para, target, sub)
        if new == para:
            steps.append(Line(para))
            continue
        plain = re.sub(r"\bbrown (sugar|rice|bread)\b", " ", para.lower())   # colour, not technique
        words = set(re.findall(r"[a-z]+", plain))
        technique = sorted(w for w in TECHNIQUE_WORDS if w in words)
        review = (f"this step uses '{', '.join(technique)}', written for {target}; {sub} may not "
                  "behave the same way" if technique else None)
        steps.append(Line(new, changed=True, was=para, review=review))
    return ingredients, steps


# ---------- entry point ----------

def substitute(conn, recipe: dict, target: str, exclude: list[str] = (),
               proposed: str | None = None) -> SubstitutionResult:
    """Evidence-ranked substitutes for `target` in `recipe`, plus the rewritten recipe."""
    target = (normalize_ingredient(target) or [target.lower().strip()])[0]
    names = recipe_names(conn, recipe["recipe_id"])
    title = recipe["title"].strip()
    lines = [clean_line(raw) for raw, n in zip(recipe["ingredients"], _line_names(conn, recipe))
             if n and same_thing(target, n)]
    result = SubstitutionResult(recipe_id=recipe["recipe_id"], title=title, target=target,
                                target_lines=lines, same_dish=0, candidates=[], chosen=None)
    if not lines:
        result.notes.append(f"This recipe does not list {target}. Its ingredients are: "
                            + ", ".join(names))
        return result

    result.candidates, result.same_dish = find_candidates(
        conn, recipe["recipe_id"], title, names, target, list(exclude), proposed)
    allowed = [c for c in result.candidates if not c.violates]
    if proposed:
        p = (normalize_ingredient(proposed) or [proposed.lower().strip()])[0]
        result.chosen = next(c for c in result.candidates if c.name == p)
    elif allowed and allowed[0].strength != "none":
        result.chosen = allowed[0]
    if result.chosen:
        result.ingredients, result.steps = rewrite(conn, recipe, target, result.chosen.name)
    if not any(c.strength in ("strong", "moderate") for c in allowed):
        result.notes.append("Dataset evidence is weak for this substitution. You can ask me to "
                            "search the web; those results are shown separately and are not verified.")
    return result


def _line_names(conn, recipe: dict) -> list[str | None]:
    """First normalized name of each ingredient line (None for ad/header lines)."""
    first = {}
    for line_no, name in conn.execute("SELECT line_no, name FROM ingredients WHERE recipe_id = ? "
                                      "ORDER BY line_no", (recipe["recipe_id"],)):
        first.setdefault(line_no, name)
    return [first.get(i) for i in range(len(recipe["ingredients"]))]


# ---------- optional external search (secondary, labeled) ----------

@dataclass
class ExternalResult:
    text: str
    sources: list[tuple[str, str]]  # (title, url)


EXTERNAL_PROMPT = (
    "Find cooking guidance from reputable sources on substituting {target} with {sub} in "
    "\"{title}\". Report briefly what the sources say (ratio, effect on texture or taste, "
    "technique changes). Say when sources disagree. Do not say a substitution is safe for "
    "allergies or medical diets.")


def search_web(client, title: str, target: str, sub: str | None, model: str) -> ExternalResult:
    """Ask Claude with the web search tool; collect text and source links."""
    messages = [{"role": "user", "content": EXTERNAL_PROMPT.format(
        target=target, sub=sub or "a suitable replacement", title=title)}]
    for _ in range(3):                                   # resume on pause_turn
        response = client.messages.create(
            model=model, max_tokens=4096, output_config={"effort": "low"},
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}],
            messages=messages)
        if response.stop_reason != "pause_turn":
            break
        messages = messages[:1] + [{"role": "assistant", "content": response.content}]
    text, sources = [], []
    for block in response.content:
        if block.type == "text":
            text.append(block.text)
            for cite in getattr(block, "citations", None) or []:
                if getattr(cite, "url", None):
                    sources.append((getattr(cite, "title", "") or cite.url, cite.url))
        elif block.type == "web_search_tool_result" and isinstance(block.content, list):
            sources += [(r.title, r.url) for r in block.content if getattr(r, "url", None)]
    return ExternalResult(text="".join(text).strip(), sources=list(dict.fromkeys(sources)))
