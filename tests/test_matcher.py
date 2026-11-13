"""Matcher over the 6-recipe fixture (conftest.py). Scores worked out by hand:

have = 3 bananas, flour, 2 eggs   (3 user ingredients)
  ar_bb1  banana, egg, walnut, flour   coverage 3/4, usage 3/3 -> (0.75 + 1) / 2 - 0.03 x 1 = 0.845
  ar_bb2  banana, flour, vegetable oil coverage 2/3, usage 2/3 -> 0.6667 - 0.03 x 1     = 0.6367
  epi_fruit banana, fruit bread        coverage 1/2, usage 1/3 -> 0.4167 - 0.03 x 1     = 0.3867
"""
import pytest

from recipe_bot.matcher import covers, match_recipes, parse_have
from recipe_bot.search import SearchQuery

HAVE = ["3 bananas", "flour", "2 eggs"]


def by_id(result):
    return {m.recipe_id: m for m in result.matches}


def test_ranking_and_scores(conn):
    r = match_recipes(conn, HAVE)
    assert [m.recipe_id for m in r.matches] == ["ar_bb1", "ar_bb2", "epi_fruit"]
    assert [m.score for m in r.matches] == pytest.approx([0.845, 0.6367, 0.3867], abs=1e-4)
    assert r.candidates == 3 and r.allowed == 6


def test_matched_missing_unused_and_reason(conn):
    bb1, bb2 = by_id(match_recipes(conn, HAVE))["ar_bb1"], by_id(match_recipes(conn, HAVE))["ar_bb2"]
    assert {c.recipe_name for c in bb1.matched} == {"banana", "egg", "flour"}
    assert bb1.missing == ["walnut"] and bb1.unused == []
    assert bb2.missing == ["vegetable oil"] and bb2.unused == ["2 eggs"]
    assert bb1.reason() == ("coverage 3/4 = 0.75, usage 3/3 = 1.00; (0.75 + 1.00) / 2 "
                            "- 0.03 x 1 missing = 0.84")


def test_quantities_compared_only_when_comparable(conn):
    bb1 = by_id(match_recipes(conn, HAVE))["ar_bb1"]
    q = {c.recipe_name: c.quantity for c in bb1.matched}
    assert q["banana"].startswith("enough: you have 3, recipe needs 3")
    assert q["egg"].startswith("enough")
    assert q["flour"] == "quantity not verified (you gave no amount)"
    short = by_id(match_recipes(conn, ["1 banana", "flour", "2 eggs"]))["ar_bb1"]
    assert {c.recipe_name: c.quantity for c in short.matched}["banana"].startswith("not enough")


def test_hard_constraints_are_never_relaxed(conn):
    r = match_recipes(conn, HAVE, SearchQuery(exclude=["egg"]))
    assert "ar_bb1" not in by_id(r)
    r = match_recipes(conn, HAVE, SearchQuery(max_steps=2))
    assert [m.recipe_id for m in r.matches] == ["ar_bb2"]   # fruit bread: unknown steps


def test_derived_products_do_not_count_and_variants_are_labeled(conn):
    r = by_id(match_recipes(conn, ["chicken", "spinach", "olive oil", "banana"]))
    skillet = r["ar_cs1"]
    assert skillet.score == pytest.approx((1 + 0.75) / 2)
    assert [(c.recipe_name, c.exact) for c in skillet.matched if c.user_ingredient == "chicken"] \
        == [("chicken breast", False)]
    soup = r["epi_soup"]                      # chicken broth is not chicken
    assert {c.recipe_name for c in soup.matched} == {"spinach"}
    assert "chicken broth" in soup.missing


def test_no_ingredients_or_no_candidates(conn):
    assert match_recipes(conn, []).matches == []
    r = match_recipes(conn, ["saffron"])
    assert r.candidates == 0 and r.matches == []


def test_covers_both_directions():
    assert covers("chicken", "chicken breast")          # recipe more specific
    assert covers("chicken breast", "chicken")          # user more specific
    assert not covers("butter", "peanut butter")
    assert not covers("peanut butter", "butter")
    assert [u.name for u in parse_have(["2 lb chicken breasts", "Salt and pepper"])] == \
        ["chicken breast", "salt", "black pepper"]
