"""Aggregate statistics, computed in SQL/pandas over the complete filtered set.

Every function takes the same SearchQuery the search uses, so "recipes with
chicken and no peanuts" means exactly the same set in both. Every function
returns a StatResult that carries what an aggregate answer must state:
filters applied, recipes analyzed, the denominator, what was excluded and
why, the calculation, and the normalization / step-counting rules used.
The LLM only phrases StatResult.explain(); it never computes a number.

Population: all recipes returned by search.find_matches (no limit). It is
written to a TEMP table `pop`, and the aggregates join against it.
"""

import sqlite3
from dataclasses import dataclass, field, replace

import pandas as pd

from .search import SearchQuery, find_matches, include_names

# ---------- rule texts quoted in every answer that depends on them ----------

RULES = {
    "normalization": (
        "Ingredient names are normalized by rule: lowercase; quantities, units, "
        "parentheticals and prep/size words removed; first 'or' alternative kept; "
        "last word singularized; small synonym map (e.g. kosher salt -> salt). "
        "Distinct products stay distinct (butter vs peanut butter)."),
    "unique_names": (
        "Each recipe counts an ingredient name once, even if it is listed twice."),
    "include": (
        "An ingredient term matches a normalized name if it is the name's last "
        "word(s) ('spinach' -> 'baby spinach') or is followed only by part words "
        "('chicken' -> 'chicken breast'); derived products do not match "
        "('chicken broth', 'peanut butter' for 'butter')."),
    "exclude": (
        "Excluded terms are checked in title, ingredient lines (including 'or' "
        "alternatives) and instructions; any mention removes the recipe."),
    "steps": (
        "A step is one non-empty paragraph of the original instructions. Sources "
        "split steps differently (Allrecipes: one action per line; Food Network "
        "and Epicurious: paragraphs with several actions), so cross-source "
        "comparisons are rough. Recipes without instructions have unknown steps "
        "and are excluded, never counted as 0."),
    "ingredient_count": (
        "Ingredient count = number of unique normalized names in the recipe. "
        "Recipes with no ingredient list are excluded as unknown."),
    "text": (
        "Text search requires every query word (stemmed) in the title, ingredient "
        "names or instructions; if none match, any word is accepted and this is "
        "stated."),
}


@dataclass
class StatResult:
    question: str
    filters: str
    n_analyzed: int                 # recipes the calculation actually used
    denominator: str                # what the percentages / averages divide by
    calculation: str
    rules: list[str]
    value: object = None            # headline number(s)
    rows: list[dict] = field(default_factory=list)   # rankings / breakdowns
    excluded: dict = field(default_factory=dict)     # reason -> count
    notes: list[str] = field(default_factory=list)

    def explain(self) -> str:
        """Plain-text block with everything an aggregate answer must state."""
        lines = [f"Question: {self.question}",
                 f"Filters: {self.filters}",
                 f"Recipes analyzed: {self.n_analyzed:,}",
                 f"Denominator: {self.denominator}"]
        if self.excluded:
            lines.append("Excluded: " + "; ".join(f"{n:,} {why}" for why, n in self.excluded.items()))
        lines.append(f"Calculation: {self.calculation}")
        if self.value is not None:
            lines.append(f"Result: {self.value}")
        for row in self.rows:
            lines.append("  " + ", ".join(f"{k}={v}" for k, v in row.items()))
        lines += [f"Note: {n}" for n in self.notes]
        lines += [f"Rule ({r}): {RULES[r]}" for r in self.rules]
        return "\n".join(lines)


# ---------- population ----------

def describe_filters(q: SearchQuery, mode: str | None) -> str:
    parts = []
    if q.text:
        where = "title" if q.title_only else "title, ingredients or instructions"
        parts.append(f'text "{q.text}" ({"every word" if mode == "all" else "any word"} in {where})')
    if q.include:
        parts.append("must include: " + ", ".join(q.include))
    if q.exclude:
        parts.append("must exclude: " + ", ".join(q.exclude))
    if q.max_steps is not None:
        parts.append(f"at most {q.max_steps} steps")
    if q.sources:
        parts.append("sources: " + ", ".join(q.sources))
    return "; ".join(parts) or "none (all recipes)"


def query_rules(q: SearchQuery) -> list[str]:
    rules = []
    if q.text:
        rules.append("text")
    if q.include:
        rules += ["normalization", "include"]
    if q.exclude:
        rules.append("exclude")
    if q.max_steps is not None:
        rules.append("steps")
    return rules


def load_population(conn: sqlite3.Connection, q: SearchQuery) -> tuple[int, str]:
    """Fill TEMP table `pop` with every matching recipe. Returns (size, filters text)."""
    rows, mode = find_matches(conn, replace(q, limit=0))
    conn.execute("DROP TABLE IF EXISTS temp.pop")
    conn.execute("CREATE TEMP TABLE pop (recipe_id TEXT PRIMARY KEY)")
    conn.executemany("INSERT INTO pop VALUES (?)", ((r[0],) for r in rows))
    return len(rows), describe_filters(q, mode)


def pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def merge_rules(*groups) -> list[str]:
    """Rule names in order, without duplicates."""
    return list(dict.fromkeys(r for g in groups for r in g))


# ---------- statistics ----------

def count_recipes(conn, q: SearchQuery, by_source: bool = False) -> StatResult:
    """How many recipes match, optionally per source."""
    n, filters = load_population(conn, q)
    rows = []
    if by_source:
        for src, c in conn.execute("SELECT r.source, COUNT(*) FROM pop JOIN recipes r "
                                   "USING (recipe_id) GROUP BY r.source ORDER BY r.source"):
            rows.append({"source": src, "recipes": c, "pct_of_matches": pct(c, n)})
    return StatResult(question="Number of matching recipes", filters=filters,
                      n_analyzed=n, denominator=f"{n:,} matching recipes",
                      calculation="COUNT of recipes passing all filters",
                      rules=query_rules(q), value=n, rows=rows)


def ingredient_share(conn, q: SearchQuery, term: str, show_variants: int = 5) -> StatResult:
    """Share of matching recipes that contain an ingredient."""
    n, filters = load_population(conn, q)
    conn.execute("DROP TABLE IF EXISTS temp.term_names")
    conn.execute("CREATE TEMP TABLE term_names (name TEXT PRIMARY KEY)")
    conn.executemany("INSERT INTO term_names VALUES (?)", ((x,) for x in include_names(conn, term)))
    with_term = conn.execute(
        "SELECT COUNT(DISTINCT i.recipe_id) FROM ingredients i JOIN pop USING (recipe_id) "
        "JOIN term_names USING (name)").fetchone()[0]
    variants = conn.execute(
        "SELECT i.name, COUNT(DISTINCT i.recipe_id) AS c FROM ingredients i JOIN pop USING (recipe_id) "
        "JOIN term_names USING (name) GROUP BY i.name ORDER BY c DESC, i.name LIMIT ?",
        (show_variants,)).fetchall()
    return StatResult(
        question=f"Share of recipes containing '{term}'", filters=filters,
        n_analyzed=n, denominator=f"{n:,} matching recipes",
        calculation=f"recipes with a name matching '{term}' / matching recipes x 100",
        rules=merge_rules(query_rules(q), ["normalization", "include"]),
        value=f"{with_term:,} of {n:,} = {pct(with_term, n)}%",
        rows=[{"counted_name": name, "recipes": c} for name, c in variants],
        notes=["Most common names counted as this ingredient are listed above."])


def top_ingredients(conn, q: SearchQuery, n: int = 10, skip: list[str] = ()) -> StatResult:
    """Most common normalized ingredient names among matching recipes."""
    size, filters = load_population(conn, q)
    counts = conn.execute(
        "SELECT name, COUNT(DISTINCT recipe_id) AS c FROM ingredients JOIN pop USING (recipe_id) "
        "GROUP BY name ORDER BY c DESC, name").fetchall()
    counts = [(name, c) for name, c in counts if name not in set(skip)]
    top = counts[:n]
    notes = []
    if len(counts) > n and top and counts[n][1] == top[-1][1]:
        tied = sum(1 for _, c in counts[n:] if c == top[-1][1])
        notes.append(f"{tied} more names tie with #{n} at {top[-1][1]} recipes; "
                     "ties are ordered alphabetically.")
    if skip:
        notes.append("Left out of the ranking on request: " + ", ".join(skip))
    return StatResult(
        question=f"Top {n} ingredients", filters=filters, n_analyzed=size,
        denominator=f"{size:,} matching recipes (each percentage = recipes using the name / this)",
        calculation="COUNT DISTINCT recipes per normalized name, sorted descending",
        rules=merge_rules(query_rules(q), ["normalization", "unique_names"]),
        rows=[{"rank": i + 1, "ingredient": name, "recipes": c, "pct": pct(c, size)}
              for i, (name, c) in enumerate(top)],
        notes=notes)


def summarize(values: pd.Series) -> dict:
    return {"mean": round(float(values.mean()), 2), "median": float(values.median()),
            "min": int(values.min()), "max": int(values.max())}


def numeric_stats(conn, q: SearchQuery, column: str, label: str, rule: str,
                  unknown_sql: str, unknown_reason: str, by_source: bool) -> StatResult:
    """Mean/median/min/max of a numeric recipe column over matching recipes."""
    n, filters = load_population(conn, q)
    df = pd.read_sql(f"SELECT r.source, r.{column} AS v FROM pop JOIN recipes r USING (recipe_id)", conn)
    unknown = df.query(unknown_sql)
    known = df.drop(unknown.index)
    excluded = {unknown_reason: len(unknown)} if len(unknown) else {}
    rows = []
    if by_source:
        for src, grp in known.groupby("source"):
            rows.append({"source": src, "recipes": len(grp), **summarize(grp["v"])})
    value = summarize(known["v"]) if len(known) else f"no recipes with a known {label.lower()}"
    return StatResult(
        question=f"{label} statistics", filters=filters, n_analyzed=len(known),
        denominator=f"{len(known):,} matching recipes with a known {label.lower()}",
        calculation=f"mean, median, min, max of {label.lower()} (pandas)",
        rules=merge_rules(query_rules(q), [rule]), value=value, rows=rows, excluded=excluded)


def step_stats(conn, q: SearchQuery, by_source: bool = False) -> StatResult:
    return numeric_stats(conn, q, "step_count", "Step count", "steps",
                         "v.isna()", "without instructions (unknown steps)", by_source)


def ingredient_count_stats(conn, q: SearchQuery, by_source: bool = False) -> StatResult:
    return numeric_stats(conn, q, "n_ingredients", "Ingredient count", "ingredient_count",
                         "v == 0", "without an ingredient list (unknown)", by_source)


def rank_recipes(conn, q: SearchQuery, by: str = "step_count", ascending: bool = True,
                 n: int = 10) -> StatResult:
    """Recipes with the fewest/most steps or ingredients, with tie reporting."""
    if by not in ("step_count", "n_ingredients"):
        raise ValueError("by must be 'step_count' or 'n_ingredients'")
    size, filters = load_population(conn, q)
    known = f"r.{by} IS NOT NULL AND r.{by} > 0"
    direction = "ASC" if ascending else "DESC"
    rows = conn.execute(
        f"SELECT r.recipe_id, r.title, r.{by} FROM pop JOIN recipes r USING (recipe_id) "
        f"WHERE {known} ORDER BY r.{by} {direction}, r.title, r.recipe_id").fetchall()
    top = rows[:n]
    notes = []
    if len(rows) > n and top and rows[n][2] == top[-1][2]:
        tied = sum(1 for r in rows[n:] if r[2] == top[-1][2])
        notes.append(f"{tied} more recipes tie at {top[-1][2]}; ties are ordered by title.")
    label = "steps" if by == "step_count" else "ingredients"
    rule = "steps" if by == "step_count" else "ingredient_count"
    return StatResult(
        question=f"Recipes with the {'fewest' if ascending else 'most'} {label}",
        filters=filters, n_analyzed=len(rows),
        denominator=f"{len(rows):,} matching recipes with a known {label} count",
        calculation=f"sort by {label} {'ascending' if ascending else 'descending'}, then title",
        rules=merge_rules(query_rules(q), [rule]),
        rows=[{"recipe_id": rid, "title": t.strip(), label: v} for rid, t, v in top],
        excluded={f"with unknown {label}": size - len(rows)} if size > len(rows) else {},
        notes=notes)
