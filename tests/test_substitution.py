"""Task 3 substitution over its own small database (the shared fixture has too few
recipes for alternatives, which must be names used by >= 5 recipes).

Country Banana Bread (target recipe) uses butter. Evidence planted:
  ar_m0, ar_m1    Banana Bread, "butter or margarine"       -> direct, same dish
  epi_c0..c3      Sugar Cookies, "butter or margarine"      -> direct, other dishes
  ar_o0, ar_o1    Moist Banana Bread, vegetable oil, no butter -> similar recipes
  fn_g0..g4       butter + heavy cream together              -> conflict flag
  fn_mg0..mg4     margarine on its own (so it is a known name)
"""
import json

import pytest

from recipe_bot.answer import handle
from recipe_bot.data_loader import SOURCE_FILES
from recipe_bot.intent import TurnIntent
from recipe_bot.search import get_recipe
from recipe_bot.session import Session
from recipe_bot.store import build_db, connect
from recipe_bot.substitution import (Candidate, Evidence, ExternalResult, excluded_by, grade,
                                     parse_alternatives, replace_word, substitute)

BASE = ["3 bananas", "2 cups flour", "1 cup sugar", "2 eggs"]


def recipes():
    ar = {"t": {"title": "Country Banana Bread", "ingredients": ["1/2 cup butter"] + BASE,
                "instructions": "Cream the butter and sugar.\nAdd bananas and eggs.\nBake 1 hour."}}
    for i in range(2):
        ar[f"m{i}"] = {"title": "Banana Bread", "ingredients": ["1/2 cup butter or margarine"] + BASE,
                       "instructions": "Mix.\nBake."}
        ar[f"o{i}"] = {"title": "Moist Banana Bread", "ingredients": ["1/3 cup vegetable oil"] + BASE,
                       "instructions": "Mix.\nBake."}
    epi = {f"c{i}": {"title": f"Sugar Cookies {i}",
                     "ingredients": ["1 cup butter or margarine", "2 cups flour", "1 cup sugar"],
                     "instructions": "Cream butter.\nBake."} for i in range(4)}
    epi["pb"] = {"title": "Peanut Butter Toast",
                 "ingredients": ["2 tablespoons peanut butter", "1 slice bread", "1 tablespoon butter"],
                 "instructions": "Butter the bread.\nSpread peanut butter."}
    fn = {f"g{i}": {"title": f"Glazed Cake {i}",
                    "ingredients": ["1/2 cup butter", "1/2 cup heavy cream", "1 cup sugar", "2 cups flour"],
                    "instructions": "Mix.\nBake."} for i in range(5)}
    fn.update({f"mg{i}": {"title": f"Margarine Frosting {i}",
                          "ingredients": ["1/2 cup margarine", "2 cups powdered sugar"],
                          "instructions": "Beat."} for i in range(5)})
    return {"ar": ar, "epi": epi, "fn": fn}


@pytest.fixture(scope="module")
def sconn(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("subdb")
    for source, payload in recipes().items():
        (tmp / SOURCE_FILES[source]).write_text(json.dumps(payload))
    build_db(tmp / "sub.db", tmp, cooccur_min=1)
    c = connect(tmp / "sub.db")
    yield c
    c.close()


def by_name(result):
    return {c.name: c for c in result.candidates}


def test_evidence_tiers_and_grades(sconn):
    r = substitute(sconn, get_recipe(sconn, "ar_t"), "butter")
    assert r.target_lines == ["1/2 cup butter"] and r.same_dish == 4
    c = by_name(r)
    marg = c["margarine"]
    assert marg.strength == "strong" and marg.flags == []
    assert [(e.kind, e.count) for e in marg.evidence] == [("direct_same_dish", 2), ("direct_other_dish", 4)]
    assert marg.evidence[0].recipe_ids == ["ar_m0", "ar_m1"]
    oil = c["vegetable oil"]
    assert oil.strength == "moderate"
    assert oil.evidence[0].kind == "similar" and oil.evidence[0].recipe_ids == ["ar_o0", "ar_o1"]
    assert r.candidates[0] is marg and r.chosen is marg


def test_conflict_flag_and_recipe_ingredients_not_offered(sconn):
    c = by_name(substitute(sconn, get_recipe(sconn, "ar_t"), "butter"))
    cream = c["heavy cream"]                      # always used together with butter here
    assert cream.strength == "weak" and cream.together == 5
    assert any(f.startswith("conflicting") for f in cream.flags)
    assert not {"sugar", "flour", "egg", "banana"} & set(c)   # already in the recipe


def test_rewrite_marks_changes_and_review(sconn):
    r = substitute(sconn, get_recipe(sconn, "ar_t"), "butter")
    first = r.ingredients[0]
    assert (first.text, first.changed, first.was) == ("1/2 cup margarine", True, "1/2 cup butter")
    assert [l.changed for l in r.ingredients[1:]] == [False] * 4
    cream_step = r.steps[0]
    assert cream_step.text == "Cream the margarine and sugar." and "cream" in cream_step.review
    assert not r.steps[1].changed


def test_exclusions_are_respected_and_proposals_kept(sconn):
    recipe = get_recipe(sconn, "ar_t")
    r = substitute(sconn, recipe, "butter", exclude=["margarine"])
    assert by_name(r)["margarine"].violates == ["margarine"]
    assert r.chosen.name == "vegetable oil"
    r = substitute(sconn, recipe, "butter", proposed="olive oil")   # no evidence at all
    assert r.chosen.name == "olive oil" and r.chosen.strength == "none"
    assert r.ingredients[0].text == "1/2 cup olive oil"


def test_target_not_in_recipe(sconn):
    r = substitute(sconn, get_recipe(sconn, "ar_t"), "milk")
    assert r.candidates == [] and r.chosen is None
    assert r.notes[0].startswith("This recipe does not list milk")


def test_reply_separates_verified_predicted_and_external(sconn):
    session = Session(last_recipe="ar_t")
    calls = []

    def web(title, target, sub):
        calls.append((title, target, sub))
        return ExternalResult("Use 1:1.", [("Kitchen guide", "https://example.org/x")])

    intent = TurnIntent(action="substitute", sub_target="butter")
    reply = handle(sconn, session, intent, web=web)
    assert "Dataset evidence (verified" in reply and "ar_m0" in reply
    assert "PREDICTION" in reply and "same amount assumed" in reply
    assert "Safety:" in reply and calls == []                 # web only on request
    assert session.last_substitution["options"][0] == "margarine"

    reply = handle(sconn, session, intent.model_copy(update={"use_web": True}), web=web)
    assert calls == [("Country Banana Bread", "butter", "margarine")]
    assert "WEB SEARCH, not from the dataset" in reply and "https://example.org/x" in reply


def test_reply_warns_when_proposal_breaks_exclusion(sconn):
    session = Session(last_recipe="ar_t", exclude=["margarine"])
    reply = handle(sconn, session, TurnIntent(action="substitute", sub_target="butter",
                                              sub_candidate="margarine"))
    assert "BREAKS your exclusion: margarine" in reply and "WARNING" in reply


# ---------- pure helpers ----------

def test_parse_alternatives():
    assert parse_alternatives("1 cup butter or margarine, softened") == [["butter", "margarine"]]
    assert parse_alternatives("2 cups kale (spinach may be substituted)")[0] == ["kale", "spinach"]
    assert parse_alternatives("1 cup butter") == []


def test_replace_word_skips_other_products():
    assert replace_word("Melt the butter and peanut butter.", "butter", "oil") == \
        "Melt the oil and peanut butter."
    assert replace_word("Add the eggs.", "egg", "flax egg") == "Add the flax egg."


def test_grade_rules():
    def graded(*ev, rate=0.0):
        c = Candidate("x", evidence=[Evidence(k, n, [], "") for k, n in ev], together_rate=rate)
        grade(c)
        return c
    assert graded(("direct_same_dish", 1), ("similar", 1)).strength == "strong"
    assert graded(("direct_other_dish", 10)).strength == "moderate"
    weak = graded(("direct_other_dish", 3))
    assert weak.strength == "weak" and any(f.startswith("indirect") for f in weak.flags)
    assert any(f.startswith("conflicting") for f in graded(("similar", 2), rate=0.5).flags)
    assert graded().strength == "none"


def test_excluded_by():
    assert excluded_by("unsalted butter", ["butter"]) == ["butter"]
    assert excluded_by("peanut butter", ["peanut"]) == ["peanut"]
    assert excluded_by("olive oil", ["butter"]) == []


def test_brown_sugar_is_not_a_technique(sconn):
    from recipe_bot.substitution import rewrite
    recipe = {"recipe_id": "ar_t", "ingredients": ["1/2 cup butter"],
              "instructions": "Mix butter and brown sugar.\nCream butter."}
    _, steps = rewrite(sconn, recipe, "butter", "oil")
    assert steps[0].changed and steps[0].review is None
    assert "cream" in steps[1].review
