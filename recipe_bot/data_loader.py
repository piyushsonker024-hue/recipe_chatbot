"""Load the three Recipe Box JSON files into one table with stable IDs.

Each source file is a JSON object mapping an opaque key to a recipe dict:
    {"<key>": {"title": str, "ingredients": [str], "instructions": str,
               "picture_link": str | None}, ...}

Every loaded recipe gets the stable ID ``<source>_<key>`` (e.g. ``ar_abc123``).
The original title, ingredients and instructions are kept exactly as they
appear in the file. Normalized fields are added later by the normalizer and
stored in separate columns/tables, never over the originals.

Records that cannot be used (no title, or neither ingredients nor
instructions) are skipped and counted in the LoadReport, so the size of the
dataset behind every statistic is known.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# source code -> file name. The source code is the ID prefix.
SOURCE_FILES = {
    "ar": "recipes_raw_nosource_ar.json",   # Allrecipes
    "epi": "recipes_raw_nosource_epi.json",  # Epicurious
    "fn": "recipes_raw_nosource_fn.json",   # Food Network
}

COLUMNS = ["recipe_id", "source", "source_key", "title", "ingredients",
           "instructions", "picture_link"]


@dataclass
class LoadReport:
    """What was loaded and what was skipped, per source."""
    loaded: dict = field(default_factory=dict)    # source -> count
    skipped: dict = field(default_factory=dict)   # source -> {reason: count}

    def total_loaded(self) -> int:
        return sum(self.loaded.values())

    def total_skipped(self) -> int:
        return sum(sum(r.values()) for r in self.skipped.values())


def make_recipe_id(source: str, key: str) -> str:
    """Stable ID: source prefix plus the key from the original file."""
    return f"{source}_{key}"


def skip_reason(record) -> str | None:
    """Return why a raw record is unusable, or None if it is usable."""
    if not isinstance(record, dict):
        return "not_a_dict"
    title = record.get("title")
    if not isinstance(title, str) or not title.strip():
        return "missing_title"
    has_ingredients = bool(record.get("ingredients"))
    instructions = record.get("instructions")
    has_instructions = isinstance(instructions, str) and bool(instructions.strip())
    if not has_ingredients and not has_instructions:
        return "no_ingredients_or_instructions"
    return None


def to_row(source: str, key: str, record: dict) -> dict:
    """Build one table row, keeping the original fields untouched."""
    ingredients = record.get("ingredients") or []
    return {
        "recipe_id": make_recipe_id(source, key),
        "source": source,
        "source_key": key,
        "title": record["title"],
        "ingredients": list(ingredients),
        "instructions": record.get("instructions") or "",
        "picture_link": record.get("picture_link"),
    }


def load_source(source: str, path: Path, report: LoadReport) -> list[dict]:
    """Load one JSON file into a list of rows and update the report."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    rows, skipped = [], {}
    for key, record in raw.items():
        reason = skip_reason(record)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        rows.append(to_row(source, key, record))

    report.loaded[source] = len(rows)
    report.skipped[source] = skipped
    return rows


def load_recipes(data_dir: Path | str = DEFAULT_DATA_DIR) -> tuple[pd.DataFrame, LoadReport]:
    """Load all three source files. Raises FileNotFoundError if any is missing."""
    data_dir = Path(data_dir)
    missing = [name for name in SOURCE_FILES.values() if not (data_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing dataset files in {data_dir}: {', '.join(missing)}. "
            "Download them from https://eightportions.com/datasets/Recipes/"
        )

    report = LoadReport()
    rows = []
    for source, name in SOURCE_FILES.items():
        rows.extend(load_source(source, data_dir / name, report))

    df = pd.DataFrame(rows, columns=COLUMNS)
    # IDs are unique by construction (keys are unique within a JSON object);
    # assert it so a future change to the ID scheme cannot break it silently.
    assert df["recipe_id"].is_unique, "recipe_id collision"
    return df.set_index("recipe_id", drop=False), report


if __name__ == "__main__":
    recipes, rep = load_recipes()
    print(f"Loaded {rep.total_loaded()} recipes, skipped {rep.total_skipped()}")
    for src in SOURCE_FILES:
        print(f"  {src}: loaded {rep.loaded[src]}, skipped {rep.skipped[src]}")
