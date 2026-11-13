"""Stats over the 6-recipe fixture in conftest.py. Expected values worked out by hand:

recipe        source  steps  unique names
ar_bb1        ar      3      banana, egg, walnut, flour          (4)
ar_bb2        ar      2      banana, flour, vegetable oil        (3)
ar_cs1        ar      1      chicken breast, spinach, olive oil  (3)
epi_soup      epi     4      chicken broth, spinach, almond butter (3)
epi_fruit     epi     None   banana, fruit bread                 (2)
fn_pt         fn      3      rice noodle, shrimp, peanut         (3)
"""
from recipe_bot.search import SearchQuery
from recipe_bot.stats import (count_recipes, ingredient_count_stats, ingredient_share,
                              rank_recipes, step_stats, top_ingredients)

ALL = SearchQuery()


def test_count_by_source(conn):
    r = count_recipes(conn, ALL, by_source=True)
    assert r.value == 6
    assert [(row["source"], row["recipes"]) for row in r.rows] == [("ar", 3), ("epi", 2), ("fn", 1)]
    assert r.filters == "none (all recipes)"


def test_count_uses_same_filters_as_search(conn):
    assert count_recipes(conn, SearchQuery(exclude=["peanut"])).value == 4   # soup + pad thai out
    assert count_recipes(conn, SearchQuery(text="banana bread")).value == 3


def test_step_stats_excludes_unknown(conn):
    r = step_stats(conn, ALL)
    assert r.n_analyzed == 5
    assert r.value == {"mean": 2.6, "median": 3.0, "min": 1, "max": 4}
    assert r.excluded == {"without instructions (unknown steps)": 1}
    assert "steps" in r.rules


def test_step_stats_by_source(conn):
    rows = {row["source"]: row for row in step_stats(conn, ALL, by_source=True).rows}
    assert rows["ar"]["mean"] == 2.0 and rows["ar"]["recipes"] == 3
    assert rows["epi"]["median"] == 4.0 and rows["epi"]["recipes"] == 1


def test_ingredient_count_stats(conn):
    r = ingredient_count_stats(conn, ALL)
    assert r.value == {"mean": 3.0, "median": 3.0, "min": 2, "max": 4}
    assert r.n_analyzed == 6 and r.excluded == {}


def test_top_ingredients_with_ties(conn):
    r = top_ingredients(conn, ALL, n=2)
    assert [(row["ingredient"], row["recipes"], row["pct"]) for row in r.rows] == \
        [("banana", 3, 50.0), ("flour", 2, 33.3)]
    assert any("1 more names tie" in note for note in r.notes)      # spinach also has 2


def test_top_ingredients_skip(conn):
    r = top_ingredients(conn, ALL, n=1, skip=["banana"])
    assert r.rows[0]["ingredient"] == "flour"
    assert any("banana" in note for note in r.notes)


def test_ingredient_share(conn):
    r = ingredient_share(conn, ALL, "chicken")
    assert r.value == "1 of 6 = 16.7%"                  # chicken broth does not count
    assert r.rows == [{"counted_name": "chicken breast", "recipes": 1}]
    r = ingredient_share(conn, SearchQuery(text="banana"), "egg")
    assert r.value == "1 of 3 = 33.3%"


def test_rank_recipes_fewest_steps_with_tie(conn):
    r = rank_recipes(conn, ALL, by="step_count", ascending=True, n=3)
    assert [row["recipe_id"] for row in r.rows] == ["ar_cs1", "ar_bb2", "ar_bb1"]
    assert any("1 more recipes tie at 3" in note for note in r.notes)   # Shrimp Pad Thai
    assert r.excluded == {"with unknown steps": 1}


def test_rank_recipes_most_ingredients(conn):
    r = rank_recipes(conn, ALL, by="n_ingredients", ascending=False, n=1)
    assert r.rows[0]["recipe_id"] == "ar_bb1"


def test_empty_population_is_safe(conn):
    r = step_stats(conn, SearchQuery(text="xyzzy"))
    assert r.n_analyzed == 0 and r.value == "no recipes with a known step count"
    assert ingredient_share(conn, SearchQuery(text="xyzzy"), "egg").value == "0 of 0 = 0.0%"


def test_explain_states_required_fields(conn):
    text = step_stats(conn, SearchQuery(include=["spinach"])).explain()
    for required in ["Filters: must include: spinach", "Recipes analyzed: 2",
                     "Denominator:", "Calculation:", "Rule (steps):", "Rule (include):"]:
        assert required in text
