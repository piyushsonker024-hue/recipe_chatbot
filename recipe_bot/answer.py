"""Execute a TurnIntent against the data and write the reply.

Replies are built from templates over search/stats results, not written by
the LLM, so every title, ID and number in a reply comes from the database.

No-match rule (CLAUDE.md): if the hard constraints leave nothing, say so,
then show what relaxing each constraint would give, clearly marked as
violating it. Nothing is relaxed silently.
"""

import re
from dataclasses import replace

from . import stats
from .intent import TurnIntent
from .matcher import FORMULA, match_recipes
from .normalizer import clean_line
from .search import SearchQuery, get_recipe, search, violations
from .session import Session
from .substitution import SAFETY_NOTE, substitute

RESULTS_SHOWN = 10
DATA_FIELDS = "title, ingredient lines and instructions"

HELP = (
    "I search 124,483 recipes (Allrecipes, Epicurious, Food Network). Try:\n"
    '  - "vegetarian lasagna without mushrooms"\n'
    '  - "show me the second one"\n'
    '  - "what share of cookie recipes use brown sugar?"\n'
    '  - "recipes with chicken and spinach in at most 3 steps"\n'
    '  - "I have 2 lb chicken, rice, an onion and garlic. What can I make?"\n'
    '  - "I have no buttermilk, what can I use instead?" (after opening a recipe)\n'
    "Restrictions you give (exclusions, step limits) stay on until you remove them.\n"
    "Commands: /state, /reset, /quit"
)


def plural(n: int, word: str) -> str:
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def format_hit(i: int, hit) -> str:
    steps = "unknown steps" if hit.step_count is None else plural(hit.step_count, "step")
    ingredients = plural(hit.n_ingredients, "ingredient") if hit.n_ingredients else "no ingredient list"
    line = f"{i}. {hit.title}  [{hit.recipe_id}]  ({steps}, {ingredients})"
    matched = [f"{term} -> {', '.join(names)}" for term, names in hit.matched.items() if names]
    if matched:
        line += "\n     matched: " + "; ".join(matched)
    return line


def constraint_line(session: Session, only: set[str] | None = None) -> str:
    """Active filters; category expansions are listed for `only` (default: all)."""
    text = f"Active filters: {session.describe()}"
    for category, terms in session.expansions.items():
        if only is not None and category not in only:
            continue
        text += (f"\n  '{category}' was expanded to: {', '.join(terms)} "
                 "(an AI-proposed list; tell me if anything should be added or removed)")
    return text


# ---------- search ----------

def relaxations(conn, q: SearchQuery) -> list[tuple[str, SearchQuery]]:
    """One relaxed query per hard constraint, each labeled with what it violates."""
    out = [(f"allows {term}", replace(q, exclude=[t for t in q.exclude if t != term]))
           for term in q.exclude]
    if q.max_steps is not None:
        out.append((f"more than {q.max_steps} steps", replace(q, max_steps=None)))
    out += [(f"without {term}", replace(q, include=[t for t in q.include if t != term]))
            for term in q.include]
    return out


def no_match_reply(conn, session: Session) -> str:
    q = session.query(limit=3)
    lines = ["No recipe matches all of your constraints."]
    alternatives = []
    for violates, relaxed in relaxations(conn, q):
        r = search(conn, relaxed)
        if r.total:
            titles = "; ".join(f"{h.title} [{h.recipe_id}]" for h in r.hits)
            alternatives.append(f"  - VIOLATES your constraint ({violates}): "
                                f"{plural(r.total, 'recipe')}, e.g. {titles}")
    if alternatives:
        lines.append("Alternatives that break one constraint (not applied unless you say so):")
        lines += alternatives
    else:
        lines.append("Relaxing any single constraint does not help either; try a different dish.")
    return "\n".join(lines)


def search_reply(conn, session: Session) -> str:
    result = search(conn, session.query(limit=RESULTS_SHOWN))
    session.last_ids = [h.recipe_id for h in result.hits]
    if result.total == 0:
        return no_match_reply(conn, session)
    lines = []
    if result.match_mode == "any":
        lines.append("No recipe contains every word of your search, so these match some of the words.")
    shown = len(result.hits)
    lines.append(f"Found {plural(result.total, 'recipe')}; showing {shown} "
                 f"({'best text match first' if session.text else 'fewest steps first'}):")
    lines += [format_hit(i + 1, h) for i, h in enumerate(result.hits)]
    lines.append('Ask for "the 2nd one" to see its ingredients and instructions.')
    return "\n".join(lines)


# ---------- ingredient matching (Task 2) ----------

MATCHES_SHOWN = 5


def format_match(i: int, m) -> list[str]:
    steps = "unknown steps" if m.step_count is None else plural(m.step_count, "step")
    lines = [f"{i}. {m.title}  [{m.recipe_id}]  ({steps}; score {m.score:.2f})"]
    lines.append(f"   you have {len(m.matched)} of {m.required} ingredients:")
    for c in m.matched:
        kind = "exact" if c.exact else "variant"
        lines.append(f"     - {c.recipe_name}  <- your '{c.user_ingredient}' [{kind}]; {c.quantity}")
    lines.append("   missing: " + (", ".join(m.missing) if m.missing else "nothing"))
    if m.staples_assumed:
        lines.append("   assumed pantry staples: " + ", ".join(m.staples_assumed))
    if m.unused:
        lines.append("   not used from your list: " + ", ".join(m.unused))
    lines.append(f"   why this rank: {m.reason()}")
    if m.duplicates:
        lines.append("   identical copies in the dataset: " + ", ".join(m.duplicates))
    return lines


def match_reply(conn, session: Session) -> str:
    if not session.have:
        return "Tell me which ingredients you have, e.g. \"2 lb chicken, rice, an onion\"."
    q = replace(session.query(), include=[])
    result = match_recipes(conn, session.have, q, limit=MATCHES_SHOWN,
                           assume_staples=session.assume_staples)
    session.last_ids = [m.recipe_id for m in result.matches]
    if not result.matches:
        lines = [f"No existing recipe uses any of your ingredients within your constraints "
                 f"({result.allowed:,} recipes allowed)."]
        for violates, relaxed in relaxations(conn, q):
            alt = match_recipes(conn, session.have, relaxed, limit=1,
                                assume_staples=session.assume_staples)
            if alt.matches:
                lines.append(f"  - VIOLATES your constraint ({violates}): {alt.candidates:,} "
                             f"recipes, best: {alt.matches[0].title} [{alt.matches[0].recipe_id}]")
        return "\n".join(lines)
    lines = [f"Ranked {result.candidates:,} existing recipes that use at least one of your "
             f"ingredients (of {result.allowed:,} that pass your constraints). Top {len(result.matches)}:"]
    for i, m in enumerate(result.matches):
        lines += format_match(i + 1, m)
    lines.append(f"Scoring: {FORMULA}.")
    lines += [f"Note: {n}" for n in result.notes]
    lines += pantry_conflicts(session)
    return "\n".join(lines)


def pantry_conflicts(session: Session) -> list[str]:
    """Warn when one of the user's ingredients contains an excluded word: exclusion is strict
    and word-based, so 'milk' (from 'dairy') also removes recipes with their coconut milk."""
    out = []
    for said in session.have:
        words = set(re.findall(r"[a-z]+", said.lower()))
        hits = [t for t in session.exclude if set(t.split()) <= words
                or set(t.rstrip("s").split()) <= {w.rstrip("s") for w in words}]
        if hits:
            out.append(f"Warning: your '{said}' contains the excluded word(s) {', '.join(hits)}, "
                       "so recipes using it are excluded too. Tell me if that exclusion should "
                       "not apply to it.")
    return out


# ---------- show a recipe ----------

def resolve_recipe(session: Session, intent: TurnIntent) -> str | None:
    if intent.recipe_id:
        return intent.recipe_id
    if intent.result_number and 1 <= intent.result_number <= len(session.last_ids):
        return session.last_ids[intent.result_number - 1]
    if intent.result_number is None:
        return session.last_recipe
    return None


def recipe_reply(conn, session: Session, intent: TurnIntent) -> str:
    recipe_id = resolve_recipe(session, intent)
    recipe = get_recipe(conn, recipe_id) if recipe_id else None
    if recipe is None:
        n = len(session.last_ids)
        return (f"I can't tell which recipe you mean (the last results had {n}). "
                "Give its number in the list or its ID.")
    session.last_recipe = recipe_id
    lines = [f"{recipe['title'].strip()}  [{recipe_id}]"]
    bad = violations(conn, recipe_id, session.exclude)
    if bad:
        lines.append(f"WARNING: this recipe mentions {', '.join(bad)}, which you excluded.")
    if intent.show in ("ingredients", "both"):
        lines.append("Ingredients (as written in the source):")
        lines += [f"  - {clean_line(i)}" for i in recipe["ingredients"] if clean_line(i)]
        if not recipe["ingredients"]:
            lines.append("  (the dataset has no ingredient list for this recipe)")
    if intent.show in ("instructions", "both"):
        steps = recipe["step_count"]
        lines.append(f"Instructions ({steps} steps):" if steps else "Instructions:")
        paragraphs = [p.strip() for p in recipe["instructions"].split("\n") if p.strip()]
        lines += [f"  {i + 1}. {p}" for i, p in enumerate(paragraphs)]
        if not paragraphs:
            lines.append("  (the dataset has no instructions for this recipe)")
    lines.append("Nutrition and cooking times are not in the dataset.")
    return "\n".join(lines)


# ---------- substitution (Task 3) ----------

OPTIONS_SHOWN = 5
KIND_LABEL = {"direct_same_dish": "stated in this dish", "direct_other_dish": "stated in other dishes",
              "similar": "near-identical recipes", "usage_pattern": "usage pattern (indirect)"}


def format_candidate(i: int, c, target: str) -> list[str]:
    lines = [f"{i}. {c.name}: {c.strength.upper()} evidence"]
    for e in c.evidence:
        ids = f": {', '.join(e.recipe_ids)}" if e.recipe_ids else ""
        lines.append(f"   - [{KIND_LABEL[e.kind]}] {e.detail}{ids}")
    if not c.evidence:
        lines.append(f"   - no recipe in the dataset uses {c.name} in place of {target}")
    lines.append(f"   - used together with {target} in {c.together:,} recipes "
                 f"({c.together_rate:.0%} of the rarer one's recipes)")
    lines += [f"   - note: {f}" for f in c.flags]
    if c.violates:
        lines.append(f"   - BREAKS your exclusion: {', '.join(c.violates)}")
    return lines


def rewritten_recipe(result, proposed: bool) -> list[str]:
    c = result.chosen
    why = "you chose it" if proposed else "it has the strongest dataset evidence"
    lines = [f"Updated recipe with {c.name} instead of {result.target} "
             f"(PREDICTION: not tested; picked because {why}):",
             "  Ingredients:"]
    for line in result.ingredients:
        mark = f"   [changed; was '{line.was}'; same amount assumed]" if line.changed else ""
        lines.append(f"    - {line.text}{mark}")
    lines.append("  Instructions:")
    for i, step in enumerate(result.steps):
        mark = "   [changed]" if step.changed else ""
        lines.append(f"    {i + 1}. {step.text}{mark}")
        if step.review:
            lines.append(f"       REVIEW: {step.review}")
    verified = (f"the dataset has recipes that use {c.name} where others use {result.target} (IDs above)"
                if c.evidence else f"nothing: no recipe in the dataset makes this swap")
    lines += [f"  Verified: {verified}.",
              f"  Predicted, not verified: that this recipe works with {c.name} at the same amount; "
              "texture, taste and cooking time may change."]
    if c.violates:
        lines.append(f"  WARNING: {c.name} breaks your exclusion ({', '.join(c.violates)}).")
    return lines


def external_section(web, result, target: str) -> list[str]:
    sub = result.chosen.name if result.chosen else None
    try:
        ext = web(result.title, target, sub)
    except Exception as e:                       # external search is optional; never fatal
        return [f"External web search failed ({type(e).__name__}); only dataset evidence is shown."]
    lines = ["External sources (WEB SEARCH, not from the dataset, not verified by this system):",
             "  " + (ext.text or "(no summary returned)").replace("\n", "\n  ")]
    lines += [f"  - {title}: {url}" for title, url in ext.sources[:8]] or ["  (no links returned)"]
    return lines


def substitution_reply(conn, session: Session, intent: TurnIntent, web=None) -> str:
    if not intent.sub_target:
        return "Which ingredient would you like to replace?"
    recipe_id = resolve_recipe(session, intent)
    recipe = get_recipe(conn, recipe_id) if recipe_id else None
    if recipe is None:
        return "Which recipe? Give its number in the last results or its ID."
    session.last_recipe = recipe_id
    result = substitute(conn, recipe, intent.sub_target, session.exclude, intent.sub_candidate)
    lines = [f"Substituting {result.target} in {result.title}  [{recipe_id}]"]
    if not result.target_lines:
        return "\n".join(lines + result.notes)
    lines.append("This recipe uses: " + "; ".join(result.target_lines))
    lines.append(f"Compared against {plural(result.same_dish, 'recipe')} of the same dish.")
    shown = [c for c in result.candidates if c.evidence or c is result.chosen][:OPTIONS_SHOWN]
    if result.chosen and result.chosen not in shown:
        shown.append(result.chosen)
    session.last_substitution = {"recipe_id": recipe_id, "target": result.target,
                                 "options": [c.name for c in shown]}
    lines.append("Dataset evidence (verified: these recipes exist and say this):")
    for i, c in enumerate(shown):
        lines += format_candidate(i + 1, c, result.target)
    if not shown:
        lines.append(f"  No recipe in the dataset suggests a replacement for {result.target}.")
    if result.chosen:
        lines += rewritten_recipe(result, proposed=bool(intent.sub_candidate))
    lines += [f"Note: {n}" for n in result.notes]
    lines.append(f"Safety: {SAFETY_NOTE}")
    if intent.use_web and web is not None:
        lines += external_section(web, result, result.target)
    elif intent.use_web:
        lines.append("External web search is not available in this session.")
    else:
        lines.append('External sources: not used. Say "search the web" to see outside sources '
                     "(shown separately, with links).")
    return "\n".join(lines)


# ---------- statistics ----------

def stats_reply(conn, session: Session, intent: TurnIntent) -> str:
    q = session.query()
    n = intent.top_n or 10
    calls = {
        "count": lambda: stats.count_recipes(conn, q, by_source=intent.by_source),
        "step_stats": lambda: stats.step_stats(conn, q, by_source=intent.by_source),
        "ingredient_count_stats": lambda: stats.ingredient_count_stats(conn, q, by_source=intent.by_source),
        "top_ingredients": lambda: stats.top_ingredients(conn, q, n=n, skip=intent.stat_skip),
        "fewest_steps": lambda: stats.rank_recipes(conn, q, "step_count", True, n),
        "most_steps": lambda: stats.rank_recipes(conn, q, "step_count", False, n),
        "fewest_ingredients": lambda: stats.rank_recipes(conn, q, "n_ingredients", True, n),
        "most_ingredients": lambda: stats.rank_recipes(conn, q, "n_ingredients", False, n),
    }
    if intent.stat == "ingredient_share":
        if not intent.stat_term:
            return "Which ingredient should I compute the share for?"
        result = stats.ingredient_share(conn, q, intent.stat_term)
    elif intent.stat in calls:
        result = calls[intent.stat]()
    else:
        return "I couldn't tell which statistic you want. Try: count, share of an ingredient, " \
               "top ingredients, average steps, or fewest steps."
    if intent.stat in ("fewest_steps", "most_steps", "fewest_ingredients", "most_ingredients"):
        session.last_ids = [row["recipe_id"] for row in result.rows]
    return "Computed in code over the full filtered set:\n" + result.explain()


# ---------- dispatch ----------

def unsupported_reply(intent: TurnIntent) -> str:
    missing = intent.missing_attribute or "that information"
    return (f"I can't answer that from the dataset: it has no {missing}. Each recipe only has a "
            f"{DATA_FIELDS}, and I won't guess values that aren't there. I can search by dish "
            "or ingredient, count steps, or compute ingredient statistics instead.")


def handle(conn, session: Session, intent: TurnIntent | None, web=None) -> str:
    """Apply the intent to the session, run it, and return the reply text."""
    if intent is None:
        return "Sorry, I couldn't interpret that. Could you rephrase it?"
    before = dict(session.expansions)
    session.apply(intent)
    changed = {c for c, t in session.expansions.items() if before.get(c) != t}
    if intent.action == "search":
        body = search_reply(conn, session)
    elif intent.action == "match":
        body = match_reply(conn, session)
    elif intent.action == "substitute":
        body = substitution_reply(conn, session, intent, web)
    elif intent.action == "stats":
        body = stats_reply(conn, session, intent)
    elif intent.action == "show_recipe":
        body = recipe_reply(conn, session, intent)
    elif intent.action == "unsupported":
        body = unsupported_reply(intent)
    elif intent.action == "reset":
        return "Cleared all filters and results. What would you like to cook?"
    elif intent.action == "show_state":
        return constraint_line(session)
    else:
        return HELP
    return f"{body}\n\n{constraint_line(session, only=changed)}"
