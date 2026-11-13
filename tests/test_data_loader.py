import json

import pytest

from recipe_bot.data_loader import SOURCE_FILES, load_recipes, make_recipe_id

AR = {
    "k1": {"title": "Pancakes", "ingredients": ["1 cup flour", "ADVERTISEMENT"],
           "instructions": "Mix.\nCook.", "picture_link": None},
    "k2": {},                                                     # empty record
    "k3": {"title": None, "ingredients": ["salt"], "instructions": "x"},
    "k4": {"title": "Nothing", "ingredients": [], "instructions": ""},
}
EPI = {"k1": {"title": "Soup", "ingredients": ["water"], "instructions": "Boil."}}
FN = {"z9": {"title": "Toast", "ingredients": ["bread"], "instructions": "Toast it."}}


@pytest.fixture
def data_dir(tmp_path):
    for source, payload in {"ar": AR, "epi": EPI, "fn": FN}.items():
        (tmp_path / SOURCE_FILES[source]).write_text(json.dumps(payload))
    return tmp_path


def test_stable_ids_and_sources(data_dir):
    df, _ = load_recipes(data_dir)
    assert sorted(df["recipe_id"]) == ["ar_k1", "epi_k1", "fn_z9"]
    assert make_recipe_id("ar", "k1") == "ar_k1"
    # Same key in two files stays distinct thanks to the source prefix.
    assert df.loc["ar_k1", "title"] == "Pancakes"
    assert df.loc["epi_k1", "title"] == "Soup"


def test_originals_untouched(data_dir):
    df, _ = load_recipes(data_dir)
    row = df.loc["ar_k1"]
    assert row["ingredients"] == ["1 cup flour", "ADVERTISEMENT"]
    assert row["instructions"] == "Mix.\nCook."


def test_skip_report(data_dir):
    _, report = load_recipes(data_dir)
    assert report.loaded == {"ar": 1, "epi": 1, "fn": 1}
    assert report.skipped["ar"] == {"missing_title": 2, "no_ingredients_or_instructions": 1}
    assert report.total_skipped() == 3


def test_ids_stable_across_loads(data_dir):
    first, _ = load_recipes(data_dir)
    second, _ = load_recipes(data_dir)
    assert list(first["recipe_id"]) == list(second["recipe_id"])


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="recipes_raw_nosource_ar.json"):
        load_recipes(tmp_path)
