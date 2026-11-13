import pytest

from recipe_bot.search import SearchQuery, get_recipe, name_matches, search


def ids(result):
    return [h.recipe_id for h in result.hits]


def test_text_search_requires_all_words_and_counts_total(conn):
    r = search(conn, SearchQuery(text="banana bread"))
    assert r.match_mode == "all"
    assert r.total == 3
    # exact title phrase first: both real banana breads before "Bananas on Fruit Bread"
    assert set(ids(r)[:2]) == {"ar_bb1", "ar_bb2"}
    assert ids(r)[2] == "epi_fruit"


def test_falls_back_to_any_word_and_says_so(conn):
    r = search(conn, SearchQuery(text="banana quinoa"))
    assert r.match_mode == "any"
    assert r.total == 3


def test_no_fallback_when_filters_remove_the_dish(conn):
    # Banana bread exists, but excluding banana removes it. The answer must be an empty
    # "all words" result (-> no-match reply), not an "any word" list of other dishes.
    r = search(conn, SearchQuery(text="banana bread", title_only=True, exclude=["banana"]))
    assert r.match_mode == "all" and r.total == 0


def test_no_match_returns_zero(conn):
    r = search(conn, SearchQuery(text="xyzzy"))
    assert r.total == 0 and r.hits == []


def test_exclude_is_strict_across_all_fields(conn):
    # egg and walnut are only in the classic recipe's ingredients
    assert ids(search(conn, SearchQuery(text="banana bread", exclude=["egg", "walnut"]))) \
        == ["ar_bb2", "epi_fruit"]
    # "peanut" also excludes the soup, where it only appears as an "or" alternative
    r = search(conn, SearchQuery(include=["spinach"], exclude=["peanut"]))
    assert ids(r) == ["ar_cs1"]


def test_include_ignores_derived_products(conn):
    r = search(conn, SearchQuery(include=["chicken"]))
    assert ids(r) == ["ar_cs1"]                     # soup has only chicken broth
    assert r.hits[0].matched == {"chicken": ["chicken breast"]}
    assert ids(search(conn, SearchQuery(include=["chicken broth"]))) == ["epi_soup"]


def test_max_steps_excludes_unknown_step_counts(conn):
    r = search(conn, SearchQuery(text="banana", max_steps=2))
    assert ids(r) == ["ar_bb2"]                     # fruit bread has no instructions


def test_source_filter(conn):
    assert ids(search(conn, SearchQuery(text="spinach", sources=["epi"]))) == ["epi_soup"]


def test_fts_syntax_in_user_text_is_harmless(conn):
    search(conn, SearchQuery(text='banana" OR title:* NEAR('))   # must not raise


def test_get_recipe_returns_originals(conn):
    rec = get_recipe(conn, "ar_bb1")
    assert rec["ingredients"][0] == "3 ripe bananas ADVERTISEMENT"
    assert rec["step_count"] == 3
    assert get_recipe(conn, "ar_missing") is None


@pytest.mark.parametrize("term,name,expected", [
    ("chicken", "chicken breast", True),
    ("chicken", "chicken broth", False),
    ("chicken broth", "low-sodium chicken broth", True),
    ("garlic", "garlic powder", False),
    ("chicken", "boneless chicken thigh", True),
    ("chicken", "chicken breast half", True),
    ("chicken", "chicken sausage", False),
    ("spinach", "baby spinach", True),
    ("lemon", "lemon juice", True),
    ("butter", "butter", True),
    ("butter", "peanut butter", False),       # CLAUDE.md: distinct products
    ("butter", "creamy peanut butter", False),
    ("peanut butter", "creamy peanut butter", True),
    ("peanut", "peanut butter", False),
    ("flour", "almond flour", False),
    ("flour", "whole wheat flour", True),
    ("milk", "coconut milk", False),
    ("egg", "eggplant", False),
    ("onion", "green onion", False),
    ("onion", "red onion", True),
])
def test_name_matches(term, name, expected):
    assert name_matches(term, name) is expected


def test_title_only_ignores_instruction_mentions(conn):
    # "noodles" appears only in the Pad Thai ingredients and instructions, not its title
    assert search(conn, SearchQuery(text="noodles")).total == 1
    assert search(conn, SearchQuery(text="noodles", title_only=True)).total == 0
    assert search(conn, SearchQuery(text="soup", title_only=True)).total == 1
