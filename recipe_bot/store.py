"""Build and open the SQLite store (data/recipes.db).

Tables
  recipes      one row per recipe. Original title, ingredients (JSON list,
               exactly as in the source file) and instructions, plus derived
               columns: step_count (NULL = no instructions) and n_ingredients
               (unique normalized names).
  ingredients  one row per normalized ingredient: recipe_id, line_no, raw
               line, name, is_duplicate. Every name traces back to its raw line.
  recipes_fts  contentless FTS5 index (porter stemming, BM25 ranking) over
               title, normalized ingredient names, cleaned raw ingredient lines
               and instructions; rowid = recipes.rid. Used for search and for
               exclusion checks.
  names        each distinct normalized name with the number of recipes using it.
  cooccur      for common names: how many recipes use each pair together
               (used by substitution.py to find ingredients with a similar role).
  meta         build information (schema version, load report).

Build once with:  python -m recipe_bot.store   (add --rebuild to rebuild)
"""

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

from .data_loader import DEFAULT_DATA_DIR, load_recipes
from .normalizer import build_ingredient_table, clean_line
from .steps import count_steps

DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "recipes.db"
SCHEMA_VERSION = "5"   # bump when the schema or the normalizer output changes

SCHEMA = """
CREATE TABLE recipes (
    rid           INTEGER PRIMARY KEY, -- internal row id, joins to recipes_fts.rowid
    recipe_id     TEXT NOT NULL UNIQUE,
    source        TEXT NOT NULL,
    source_key    TEXT NOT NULL,
    title         TEXT NOT NULL,
    ingredients   TEXT NOT NULL,      -- JSON list, original lines
    instructions  TEXT NOT NULL,      -- original text
    picture_link  TEXT,
    step_count    INTEGER,            -- NULL when instructions are empty
    n_ingredients INTEGER NOT NULL    -- unique normalized names
);
CREATE TABLE ingredients (
    recipe_id    TEXT NOT NULL REFERENCES recipes(recipe_id),
    line_no      INTEGER NOT NULL,
    raw          TEXT NOT NULL,
    name         TEXT NOT NULL,
    is_duplicate INTEGER NOT NULL
);
CREATE INDEX idx_ingredients_name ON ingredients(name, recipe_id);  -- covering for include filters
CREATE INDEX idx_ingredients_recipe ON ingredients(recipe_id);
-- Contentless: stores only the index (the text already lives in recipes).
CREATE VIRTUAL TABLE recipes_fts USING fts5(
    title, ingredient_names, ingredients_raw, instructions,
    content = '', tokenize = 'porter unicode61'
);
CREATE TABLE names (
    name       TEXT PRIMARY KEY,
    n_recipes  INTEGER NOT NULL     -- recipes that list this name at least once
);
CREATE TABLE cooccur (
    a TEXT NOT NULL,                -- a < b; both are names used by >= COOCCUR_MIN_RECIPES recipes
    b TEXT NOT NULL,
    n INTEGER NOT NULL,             -- recipes that use both
    PRIMARY KEY (a, b)
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

COOCCUR_MIN_RECIPES = 50            # 1,622 names on the full dataset


def recipe_rows(recipes, names_by_recipe):
    """Rows for the recipes table."""
    for rid, r in enumerate(recipes.itertuples(index=False), start=1):
        yield (rid, r.recipe_id, r.source, r.source_key, r.title,
               json.dumps(r.ingredients, ensure_ascii=False), r.instructions,
               r.picture_link, count_steps(r.instructions),
               len(names_by_recipe.get(r.recipe_id, ())))


def fts_rows(recipes, names_by_recipe):
    """Rows for the full-text index."""
    for rid, r in enumerate(recipes.itertuples(index=False), start=1):
        names = " | ".join(names_by_recipe.get(r.recipe_id, ()))
        raw = " | ".join(clean_line(line) for line in r.ingredients)
        yield (rid, r.title, names, raw, r.instructions)


def cooccur_rows(unique: pd.DataFrame, min_recipes: int):
    """(a, b, n) for every pair of common names used together in n recipes."""
    counts = unique.groupby("name")["recipe_id"].nunique()
    common = unique[unique["name"].isin(counts[counts >= min_recipes].index)]
    common = common[["recipe_id", "name"]].drop_duplicates()
    pairs = common.merge(common, on="recipe_id")
    pairs = pairs[pairs["name_x"] < pairs["name_y"]]
    grouped = pairs.groupby(["name_x", "name_y"]).size()
    return ((a, b, int(n)) for (a, b), n in grouped.items())


def build_db(db_path: Path | str = DEFAULT_DB_PATH,
             data_dir: Path | str = DEFAULT_DATA_DIR,
             cooccur_min: int = COOCCUR_MIN_RECIPES) -> None:
    """Load the JSON files, normalize, and write a fresh database."""
    db_path = Path(db_path)
    tmp_path = db_path.with_suffix(".tmp")
    tmp_path.unlink(missing_ok=True)

    recipes, report = load_recipes(data_dir)
    ingredients = build_ingredient_table(recipes)
    unique = ingredients[~ingredients["is_duplicate"]]
    names_by_recipe = unique.groupby("recipe_id")["name"].apply(list).to_dict()

    conn = sqlite3.connect(tmp_path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO recipes VALUES (?,?,?,?,?,?,?,?,?,?)",
                         recipe_rows(recipes, names_by_recipe))
        conn.executemany(
            "INSERT INTO ingredients VALUES (?,?,?,?,?)",
            ingredients.astype({"is_duplicate": int}).itertuples(index=False, name=None))
        conn.executemany("INSERT INTO recipes_fts (rowid, title, ingredient_names, "
                         "ingredients_raw, instructions) VALUES (?,?,?,?,?)",
                         fts_rows(recipes, names_by_recipe))
        conn.execute("INSERT INTO names SELECT name, COUNT(DISTINCT recipe_id) "
                     "FROM ingredients GROUP BY name")
        conn.executemany("INSERT INTO cooccur VALUES (?,?,?)", cooccur_rows(unique, cooccur_min))
        meta = {"schema_version": SCHEMA_VERSION,
                "loaded": json.dumps(report.loaded),
                "skipped": json.dumps(report.skipped)}
        conn.executemany("INSERT INTO meta VALUES (?,?)", meta.items())
        conn.commit()
    finally:
        conn.close()
    tmp_path.replace(db_path)   # only replace the old DB once the build succeeded


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open the database, failing clearly if it is missing or outdated."""
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"{db_path} not found. Build it with: python -m recipe_bot.store")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    version = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    if version is None or version["value"] != SCHEMA_VERSION:
        conn.close()
        raise RuntimeError(f"{db_path} is outdated. Rebuild: python -m recipe_bot.store --rebuild")
    return conn


if __name__ == "__main__":
    if DEFAULT_DB_PATH.exists() and "--rebuild" not in sys.argv:
        print(f"{DEFAULT_DB_PATH} already exists. Use --rebuild to rebuild it.")
        sys.exit(0)
    build_db()
    with connect() as c:
        n = c.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
        m = c.execute("SELECT COUNT(*) FROM ingredients").fetchone()[0]
    print(f"Built {DEFAULT_DB_PATH}: {n} recipes, {m} ingredient rows")
