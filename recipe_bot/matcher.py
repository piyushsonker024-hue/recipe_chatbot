"""Task 2: rank existing recipes for the ingredients a user has.

Only recipes in the dataset are ranked; nothing is generated.

Steps
  1. Hard filters (exclude, max_steps, sources, optional dish text) give the
     allowed set, using the same search.find_matches as search and stats.
  2. Candidates: allowed recipes that use at least one of the user's
     ingredients. A user ingredient matches a recipe name in either
     direction of search.name_matches: "chicken" covers "chicken breast",
     and a user's "chicken breast" covers a recipe's "chicken".
  3. Score every candidate in SQL/pandas with a transparent formula:

        coverage = matched / required      share of the recipe you already have
        usage    = used / have             share of your ingredients it uses
        score    = (coverage + usage) / 2 - 0.03 x missing

     required = the recipe's unique ingredient names, minus assumed pantry
                staples (salt, black pepper, water) the user did not list
     matched  = required names covered by the user's ingredients
     missing  = required - matched (what the user would have to buy)
     used     = user ingredients the recipe uses (unused = have - used)

     Coverage alone favours tiny recipes ("Coconut Rice", 2 of 2, using 2 of
     your 5 items); averaging with usage penalises unused ingredients, and
     the per-item penalty separates recipes needing more shopping. Ties:
     fewer missing, fewer steps, title, ID (deterministic).
  4. For the top results only: merge exact duplicates (same title and
     ingredient names; the dataset repeats some recipes), label each match
     exact or variant ("sugar" -> "powdered sugar"), and check quantities
     where both sides are comparable (quantities.py); otherwise "not verified".
"""

import json
from dataclasses import dataclass, field, replace
from functools import lru_cache

import pandas as pd

from .normalizer import normalize_ingredient
from .quantities import parse_quantity, sufficiency, total_quantity
from .search import SearchQuery, all_names, db_file, find_matches, name_matches

STAPLES = ("salt", "black pepper", "water")
MISSING_PENALTY = 0.03
MIN_REQUIRED = 2          # recipes with 0-1 required ingredients are not meaningful matches

FORMULA = (f"score = (coverage + usage) / 2 - {MISSING_PENALTY} x missing, where coverage = "
           "share of the recipe's ingredients you have and usage = share of your ingredients "
           "it uses; pantry staples (salt, black pepper, water) are assumed unless you say "
           "otherwise; ties: fewer missing, fewer steps, title")


@dataclass
class UserIngredient:
    said: str                       # as the user wrote it: "2 lb chicken"
    name: str                       # normalized: "chicken"


@dataclass
class IngredientCheck:
    recipe_name: str
    user_ingredient: str
    exact: bool                     # same normalized name; False = variant ("sugar" -> "brown sugar")
    quantity: str                   # "enough: ...", "not enough: ...", "quantity not verified (...)"


@dataclass
class RecipeMatch:
    recipe_id: str
    title: str
    step_count: int | None
    score: float
    required: int
    matched: list[IngredientCheck]
    missing: list[str]
    staples_assumed: list[str]
    unused: list[str]
    have_count: int
    duplicates: list[str] = field(default_factory=list)   # identical recipes merged into this one

    def reason(self) -> str:
        m, r = len(self.matched), self.required
        used = self.have_count - len(self.unused)
        return (f"coverage {m}/{r} = {m / r:.2f}, usage {used}/{self.have_count} = "
                f"{used / self.have_count:.2f}; ({m / r:.2f} + {used / self.have_count:.2f}) / 2 "
                f"- {MISSING_PENALTY} x {len(self.missing)} missing = {self.score:.2f}")


@dataclass
class MatchResult:
    have: list[UserIngredient]
    filters: SearchQuery
    allowed: int                    # recipes passing the hard filters
    candidates: int                 # of those, recipes using >= 1 of the user's ingredients
    matches: list[RecipeMatch]
    staples: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ---------- user ingredients ----------

def parse_have(items: list[str]) -> list[UserIngredient]:
    out = []
    for said in items:
        names = normalize_ingredient(said) or [said.strip().lower()]
        out += [UserIngredient(said=said.strip(), name=n) for n in names]
    return out


def covers(user_name: str, recipe_name: str) -> bool:
    return name_matches(user_name, recipe_name) or name_matches(recipe_name, user_name)


@lru_cache(maxsize=1)
def names_by_word(db_path: str) -> dict[str, list[str]]:
    """word -> names containing it, so matching checks a few hundred names, not 67k."""
    index: dict[str, list[str]] = {}
    for name in all_names(db_path):
        for word in set(name.split()):
            index.setdefault(word, []).append(name)
    return index


def names_covered(conn, user: UserIngredient) -> list[str]:
    """Names a user ingredient covers. Any covered name shares a word with it."""
    index = names_by_word(db_file(conn))
    candidates = {n for w in user.name.split() for n in index.get(w, [])}
    return sorted(n for n in candidates if covers(user.name, n))


# ---------- scoring ----------

def load_allowed(conn, q: SearchQuery) -> int:
    rows, _ = find_matches(conn, replace(q, include=[]))
    conn.execute("DROP TABLE IF EXISTS temp.allowed")
    conn.execute("CREATE TEMP TABLE allowed (recipe_id TEXT PRIMARY KEY)")
    conn.executemany("INSERT INTO allowed VALUES (?)", ((r[0],) for r in rows))
    return len(rows)


def score_candidates(conn, have: list[UserIngredient], staples: tuple[str, ...]) -> pd.DataFrame:
    """One row per candidate recipe with matched / required / missing / unused / score."""
    pairs = [(i, n) for i, u in enumerate(have) for n in names_covered(conn, u)]
    conn.execute("DROP TABLE IF EXISTS temp.have_names")
    conn.execute("CREATE TEMP TABLE have_names (user_idx INTEGER, name TEXT)")
    conn.executemany("INSERT INTO have_names VALUES (?, ?)", pairs)
    conn.execute("CREATE INDEX temp.idx_have_names ON have_names(name)")

    df = pd.read_sql(
        """
        SELECT i.recipe_id,
               COUNT(DISTINCT i.name)                       AS matched,
               COUNT(DISTINCT h.user_idx)                   AS users_used
        FROM have_names h
        CROSS JOIN ingredients i ON i.name = h.name     -- CROSS JOIN fixes the join order:
        CROSS JOIN allowed a ON a.recipe_id = i.recipe_id  -- start from the user's names (index)
        GROUP BY i.recipe_id
        """, conn)
    if df.empty:
        return df
    # Staples in the recipe that the user did not list are assumed, not required.
    staple_rows = pd.read_sql(
        f"""
        SELECT i.recipe_id, COUNT(DISTINCT i.name) AS staples
        FROM json_each(?) j
        CROSS JOIN ingredients i ON i.name = j.value
        CROSS JOIN allowed a ON a.recipe_id = i.recipe_id
        WHERE 1
          AND i.name NOT IN (SELECT name FROM have_names)
        GROUP BY i.recipe_id
        """, conn, params=(json.dumps(list(staples)),))
    meta = pd.read_sql("SELECT r.recipe_id, r.title, r.step_count, r.n_ingredients "
                       "FROM recipes r JOIN allowed USING (recipe_id)", conn)
    df = df.merge(meta, on="recipe_id").merge(staple_rows, on="recipe_id", how="left")
    df["staples"] = pd.to_numeric(df["staples"]).fillna(0).astype(int)
    df["required"] = df["n_ingredients"] - df["staples"]
    df["missing"] = df["required"] - df["matched"]
    df["unused"] = len(have) - df["users_used"]
    df = df[df["required"] >= MIN_REQUIRED].copy()
    coverage = df["matched"] / df["required"]
    usage = df["users_used"] / len(have)
    df["score"] = ((coverage + usage) / 2 - MISSING_PENALTY * df["missing"]).round(4)
    df["steps_sort"] = df["step_count"].fillna(10**6)
    df["title"] = df["title"].str.strip()
    return df.sort_values(["score", "missing", "steps_sort", "title", "recipe_id"],
                          ascending=[False, True, True, True, True])


# ---------- details for the top results ----------

def recipe_detail(conn, row, have: list[UserIngredient], staples: tuple[str, ...]) -> RecipeMatch:
    lines: dict[str, list[str]] = {}
    for name, raw in conn.execute("SELECT name, raw FROM ingredients WHERE recipe_id = ? "
                                  "ORDER BY line_no", (row.recipe_id,)):
        lines.setdefault(name, []).append(raw)

    matched, used = [], set()
    for name, raws in lines.items():
        users = [u for u in have if covers(u.name, name)]
        if not users:
            continue
        user = users[0]
        used.update(u.said for u in users)
        matched.append(IngredientCheck(
            recipe_name=name, user_ingredient=user.said, exact=(name == user.name),
            quantity=sufficiency(parse_quantity(user.said), total_quantity(raws))))
    matched_names = {m.recipe_name for m in matched}
    assumed = [n for n in lines if n in staples and n not in matched_names]
    missing = [n for n in lines if n not in matched_names and n not in assumed]
    unused = list(dict.fromkeys(u.said for u in have if u.said not in used))
    return RecipeMatch(recipe_id=row.recipe_id, title=row.title,
                       step_count=None if pd.isna(row.step_count) else int(row.step_count),
                       score=float(row.score), required=int(row.required), matched=matched,
                       missing=missing, staples_assumed=assumed, unused=unused,
                       have_count=len({u.said for u in have}))


def recipe_key(conn, recipe_id: str, title: str) -> tuple:
    """Identity for duplicate detection: title plus the exact ingredient lines."""
    raw = conn.execute("SELECT ingredients FROM recipes WHERE recipe_id = ?", (recipe_id,)).fetchone()[0]
    return title.lower(), raw


def top_unique(conn, scored: pd.DataFrame, have, staples, limit: int) -> list[RecipeMatch]:
    """Best `limit` recipes, merging exact duplicates into the first occurrence."""
    out, seen = [], {}
    for row in scored.itertuples():
        key = recipe_key(conn, row.recipe_id, row.title)
        if key in seen:
            seen[key].duplicates.append(row.recipe_id)
            continue
        if len(out) == limit:
            if len(seen) > limit + 20:        # stop scanning far past the cut-off
                break
            continue
        match = recipe_detail(conn, row, have, staples)
        seen[key] = match
        out.append(match)
    return out


def match_recipes(conn, have_items: list[str], q: SearchQuery = SearchQuery(),
                  limit: int = 5, assume_staples: bool = True) -> MatchResult:
    """Rank existing recipes for the user's ingredients under hard constraints `q`."""
    have = parse_have(have_items)
    staples = STAPLES if assume_staples else ()
    allowed = load_allowed(conn, q)
    scored = score_candidates(conn, have, staples) if have else pd.DataFrame()
    top = top_unique(conn, scored.head(limit * 5), have, staples, limit)
    notes = []
    if any(m.duplicates for m in top):
        notes.append("Some recipes appear more than once in the dataset with identical "
                     "ingredients; duplicates are merged and their IDs listed.")
    if any(not c.exact for m in top for c in m.matched):
        notes.append("'variant' means your ingredient matched a more specific name in the recipe "
                     "(e.g. sugar -> brown sugar); check that what you have works.")
    if top and any("not verified" in c.quantity for m in top for c in m.matched):
        notes.append("Where quantities say 'not verified', only the ingredient name was matched; "
                     "whether you have enough was not checked.")
    return MatchResult(have=have, filters=q, allowed=allowed, candidates=len(scored),
                       matches=top, staples=list(staples), notes=notes)
