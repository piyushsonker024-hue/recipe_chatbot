"""Recipe search over the SQLite store.

search(conn, SearchQuery(...)) returns ranked recipes plus the total number
of recipes that match, so answers can say "showing 10 of 342".

How a query is answered
  1. Hard filters, applied exactly in SQL. A recipe that fails one is never
     returned:
       include  each ingredient must be among the recipe's normalized names
                (see name_matches: "chicken" matches "chicken breast" but not
                "chicken broth"; "butter" does not match "peanut butter")
       exclude  the term must not appear anywhere in the recipe: title,
                normalized names, raw ingredient lines (including "or"
                alternatives the normalizer drops) or instructions. This is
                deliberately strict: "peanut" also removes recipes with peanut
                oil, and one that only says "serve without peanuts".
       max_steps (recipes with unknown step count never pass) / sources
  2. Text match: every query word must appear (match_mode "all") in the
     title, ingredient names or instructions; with title_only, in the title.
     Use title_only for dish-type questions ("cookies"), otherwise "place on
     a cookie sheet" counts as a cookie recipe. If no
     recipe in the whole dataset has all words, any word is enough
     (match_mode "any") and the result says so. If recipes with all words
     exist but the hard filters remove them, the result is empty: falling
     back would hide a no-match behind other dishes.
  3. Ranking: titles containing the query words as an exact phrase come
     first ("banana bread" -> "Best Banana Bread" before "Bananas on Fruit
     Bread"), then BM25 (SQLite FTS5) weighting title matches 10x, ingredient
     names 3x, instructions 1x. Without text: fewest steps first, then title.

Limits: words are porter-stemmed ("tomatoes" = "tomato"); there is no
synonym or category expansion ("dairy" does not become milk, butter,
cheese). That belongs in the request-parsing layer and must be shown to
the user.
"""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from functools import lru_cache

from .normalizer import normalize_ingredient

TITLE_WEIGHT, NAMES_WEIGHT, RAW_WEIGHT, INSTRUCTIONS_WEIGHT = 10.0, 3.0, 0.0, 1.0

STOPWORDS = {"a", "an", "and", "the", "with", "of", "for", "to", "in", "on",
             "recipe", "recipes", "me", "some", "i", "want", "make", "how",
             "find", "show", "give", "any", "or", "that", "is", "are"}

# Words naming a part or cut of an ingredient. "chicken breast" counts as
# chicken; "chicken broth" and "garlic powder" do not (not in this list).
PART_WORDS = {"breast", "thigh", "leg", "wing", "drumstick", "tender", "tenderloin",
              "cutlet", "fillet", "filet", "steak", "chop", "loin", "rib",
              "shoulder", "meat", "half", "piece", "chunk", "cube", "strip",
              "slice", "wedge", "kernel", "floret", "leaf", "sprig", "stem",
              "clove", "bulb", "cap", "head", "spear", "juice", "zest", "peel",
              "yolk", "white", "segment"}

# Names ending in an ingredient word that are nonetheless a different product:
# including "butter" must not match "peanut butter".
MODIFIED_PRODUCTS = {
    "peanut butter", "almond butter", "cashew butter", "nut butter",
    "sunflower seed butter", "apple butter", "cocoa butter",
    "coconut milk", "almond milk", "soy milk", "soymilk", "oat milk",
    "rice milk", "cashew milk", "sour cream", "ice cream", "coconut cream",
    "almond flour", "coconut flour", "rice flour", "chickpea flour",
    "corn flour", "almond meal", "coconut water", "rose water",
    "orange flower water", "egg substitute", "cream of tartar",
    "green onion", "spring onion", "sweet potato",
}


@dataclass
class SearchQuery:
    text: str = ""
    title_only: bool = False        # match text in titles only (dish-type questions)
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    max_steps: int | None = None
    sources: list[str] = field(default_factory=list)
    limit: int = 10


@dataclass
class Hit:
    recipe_id: str
    title: str
    step_count: int | None
    n_ingredients: int
    score: float | None             # BM25, higher is better; None without text
    matched: dict[str, list[str]]   # include term -> recipe names that matched it


@dataclass
class SearchResult:
    query: SearchQuery
    match_mode: str | None          # "all", "any", or None when there is no text
    total: int                      # recipes passing every filter and the text match
    hits: list[Hit]


# ---------- include: term -> set of normalized names ----------

def normalize_term(term: str) -> str:
    """User term -> the normalizer's form ("Mushrooms" -> "mushroom")."""
    names = normalize_ingredient(term)
    return names[0] if names else term.lower().strip()


def ends_with(words: list[str], tail: list[str]) -> bool:
    return len(words) >= len(tail) and words[len(words) - len(tail):] == tail


def is_modified_product(term: list[str], name: list[str]) -> bool:
    """Name ends with a product that is longer than the term and ends with it
    ("butter" vs "creamy peanut butter")."""
    for product in MODIFIED_PRODUCTS:
        p = product.split()
        if len(p) > len(term) and ends_with(p, term) and ends_with(name, p):
            return True
    return False


def name_matches(term: str, name: str) -> bool:
    """Does normalized `name` count as the ingredient `term`?

    Yes if the term is the head (last words) of the name ("spinach" ->
    "baby spinach"), unless the name is a different product ("butter" ->
    "peanut butter"). Also yes if the term is followed only by part words
    ("chicken" -> "chicken breast half", "lemon" -> "lemon juice").
    """
    t, n = term.split(), name.split()
    if ends_with(n, t):
        return not is_modified_product(t, n)
    for i in range(len(n) - len(t)):
        rest = n[i + len(t):]
        if n[i:i + len(t)] == t and all(w in PART_WORDS for w in rest):
            return True
    return False


@lru_cache(maxsize=1)
def all_names(db_path: str) -> tuple[str, ...]:
    """Distinct normalized names (about 67k), cached per database file."""
    conn = sqlite3.connect(db_path)
    try:
        return tuple(r[0] for r in conn.execute("SELECT name FROM names"))
    finally:
        conn.close()


def db_file(conn: sqlite3.Connection) -> str:
    return conn.execute("PRAGMA database_list").fetchone()[2]


def include_names(conn: sqlite3.Connection, term: str) -> list[str]:
    """All normalized names in the dataset that count as `term`."""
    t = normalize_term(term)
    return [n for n in all_names(db_file(conn)) if name_matches(t, n)]


# ---------- SQL ----------

def fts_phrase(term: str) -> str:
    """Quote a term as an FTS5 phrase so user text cannot inject FTS syntax."""
    return '"' + term.replace('"', '""').strip() + '"'


def query_words(text: str) -> list[str]:
    return [w for w in re.findall(r"[\w'-]+", text.lower()) if w not in STOPWORDS]


def text_to_fts(words: list[str], mode: str, title_only: bool = False) -> str:
    """Words -> FTS5 query over title, names and instructions (or title only)."""
    joiner = " AND " if mode == "all" else " OR "
    columns = "title" if title_only else "{title ingredient_names instructions}"
    return f"{columns} : (" + joiner.join(fts_phrase(w) for w in words) + ")"


def build_sql(conn: sqlite3.Connection, q: SearchQuery,
              mode: str | None) -> tuple[str, list]:
    """Compose the SQL and parameters for a query. Kept separate so it can be printed."""
    where, params = [], []
    words = query_words(q.text)
    if mode:
        score = (f"-bm25(recipes_fts, {TITLE_WEIGHT}, {NAMES_WEIGHT}, "
                 f"{RAW_WEIGHT}, {INSTRUCTIONS_WEIGHT})")
        from_clause = "recipes_fts JOIN recipes r ON r.rid = recipes_fts.rowid"
        where.append("recipes_fts MATCH ?")
        params.append(text_to_fts(words, mode, q.title_only))
        order = "instr(lower(r.title), ?) > 0 DESC, score DESC"
    else:
        score = "NULL"
        from_clause = "recipes r"
        order = "r.step_count IS NULL, r.step_count, r.title"

    for term in q.include:
        where.append("r.recipe_id IN (SELECT recipe_id FROM ingredients "
                     "WHERE name IN (SELECT value FROM json_each(?)))")
        params.append(json.dumps(include_names(conn, term)))
    for term in q.exclude:
        where.append("r.rid NOT IN (SELECT rowid FROM recipes_fts WHERE recipes_fts MATCH ?)")
        params.append(fts_phrase(term))   # every column
    if q.max_steps is not None:
        where.append("r.step_count <= ?")
        params.append(q.max_steps)
    if q.sources:
        where.append(f"r.source IN ({','.join('?' * len(q.sources))})")
        params.extend(q.sources)

    sql = (f"SELECT r.recipe_id, r.title, r.step_count, r.n_ingredients, {score} AS score "
           f"FROM {from_clause}")
    if where:
        sql += " WHERE " + " AND ".join(where)
    if mode:
        params.append(" ".join(words))      # phrase for the title boost in ORDER BY
    return sql + f" ORDER BY {order}", params


# ---------- search ----------

def matched_names(conn: sqlite3.Connection, recipe_id: str, terms: list[str]) -> dict:
    """For each include term, the recipe's names that satisfied it."""
    names = [r[0] for r in conn.execute(
        "SELECT DISTINCT name FROM ingredients WHERE recipe_id = ?", (recipe_id,))]
    return {t: [n for n in names if name_matches(normalize_term(t), n)] for t in terms}


def run(conn: sqlite3.Connection, q: SearchQuery, mode: str | None) -> list:
    sql, params = build_sql(conn, q, mode)
    return conn.execute(sql, params).fetchall()


def find_matches(conn: sqlite3.Connection, q: SearchQuery) -> tuple[list, str | None]:
    """Every recipe matching the query, ranked, plus the text match mode used.
    Search and statistics both use this, so they always agree on the set."""
    mode = "all" if query_words(q.text) else None
    rows = run(conn, q, mode)
    if mode == "all" and not rows and len(query_words(q.text)) > 1 \
            and not run(conn, SearchQuery(text=q.text, title_only=q.title_only), "all"):
        mode = "any"                     # the words never occur together in the data
        rows = run(conn, q, mode)
    return rows, mode


def search(conn: sqlite3.Connection, q: SearchQuery) -> SearchResult:
    """Run a query. Counts every match; returns the top `limit` hits."""
    rows, mode = find_matches(conn, q)

    hits = [Hit(recipe_id=r[0], title=r[1].strip(), step_count=r[2], n_ingredients=r[3],
                score=None if r[4] is None else round(r[4], 3),
                matched=matched_names(conn, r[0], q.include))
            for r in rows[:q.limit]]
    return SearchResult(query=q, match_mode=mode, total=len(rows), hits=hits)


def get_recipe(conn: sqlite3.Connection, recipe_id: str) -> dict | None:
    """Full recipe with original fields, for "show me the ingredients"."""
    row = conn.execute("SELECT * FROM recipes WHERE recipe_id = ?", (recipe_id,)).fetchone()
    if row is None:
        return None
    recipe = dict(row)
    recipe.pop("rid")
    recipe["ingredients"] = json.loads(recipe["ingredients"])
    return recipe


def violations(conn: sqlite3.Connection, recipe_id: str, terms: list[str]) -> list[str]:
    """Which excluded terms this recipe mentions (same strict check as `exclude`)."""
    row = conn.execute("SELECT rid FROM recipes WHERE recipe_id = ?", (recipe_id,)).fetchone()
    if row is None:
        return []
    return [t for t in terms if conn.execute(
        "SELECT 1 FROM recipes_fts WHERE recipes_fts MATCH ? AND rowid = ?",
        (fts_phrase(t), row[0])).fetchone()]
