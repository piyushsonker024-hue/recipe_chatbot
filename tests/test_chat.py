"""Session rules, replies and the full turn, with the LLM replaced by fixed intents.
Recipes come from the 6-recipe fixture in conftest.py."""
from types import SimpleNamespace

from google.genai.types import FinishReason

from recipe_bot.answer import handle
from recipe_bot.chat import turn
from recipe_bot.intent import Expansion, IntentParser, TurnIntent
from recipe_bot.session import Session


def I(**kw):
    return TurnIntent(**kw)


# ---------- session rules (no database) ----------

def test_exclusions_persist_across_topics_but_includes_do_not():
    s = Session()
    s.apply(I(action="search", new_topic=True, text="banana bread", add_include=["banana"],
              add_exclude=["walnut"], max_steps=3))
    s.apply(I(action="search", new_topic=True, text="soup"))
    assert s.text == "soup" and s.include == []
    assert s.exclude == ["walnut"] and s.max_steps == 3          # hard constraints stay


def test_refinement_keeps_text_and_adds_constraints():
    s = Session(text="banana bread")
    s.apply(I(action="search", add_exclude=["Egg "], max_steps=2))
    assert s.text == "banana bread" and s.exclude == ["egg"] and s.max_steps == 2
    s.apply(I(action="search", remove_exclude=["egg"], clear_max_steps=True))
    assert s.exclude == [] and s.max_steps is None


def test_category_expansion_added_and_removed_together():
    s = Session()
    s.apply(I(action="search", exclusion_expansions=[
        Expansion(category="Dairy", terms=["milk", "butter", "cheese"])]))
    assert s.exclude == ["milk", "butter", "cheese"]
    s.apply(I(action="search", remove_exclude=["dairy"]))
    assert s.exclude == [] and s.expansions == {}


def test_show_recipe_and_unsupported_do_not_change_filters():
    s = Session(text="soup", exclude=["peanut"])
    s.apply(I(action="show_recipe", result_number=1, add_exclude=["egg"]))
    s.apply(I(action="unsupported", missing_attribute="nutrition"))
    assert s.exclude == ["peanut"] and s.text == "soup"


def test_reset_clears_everything():
    s = Session(text="soup", exclude=["peanut"], last_ids=["x"])
    s.apply(I(action="reset"))
    assert s == Session()


# ---------- replies (fixture database) ----------

def test_multi_turn_follow_up(conn):
    s = Session()
    r1 = handle(conn, s, I(action="search", new_topic=True, text="banana bread", title_only=True))
    assert "Found 3 recipes" in r1 and "ar_bb1" in r1                 # incl. Bananas on Fruit Bread
    r2 = handle(conn, s, I(action="search", add_exclude=["egg"]))   # "without eggs"
    assert "Found 2 recipes" in r2 and "ar_bb1" not in r2
    assert s.last_ids[0] == "ar_bb2"                                  # exact title phrase first
    assert "excluded: egg" in r2
    r3 = handle(conn, s, I(action="show_recipe", result_number=1))  # "show me the first one"
    assert "Vegan Banana Bread" in r3 and "3 bananas" in r3 and "Instructions (2 steps)" in r3


def test_no_match_offers_marked_alternatives(conn):
    s = Session()
    reply = handle(conn, s, I(action="search", new_topic=True, text="pad thai",
                              add_exclude=["peanut"]))
    assert reply.startswith("No recipe matches all of your constraints.")
    assert "VIOLATES your constraint (allows peanut): 1 recipe," in reply
    assert s.exclude == ["peanut"]                                    # not relaxed


def test_opening_a_violating_recipe_warns(conn):
    s = Session(exclude=["peanut"])
    reply = handle(conn, s, I(action="show_recipe", recipe_id="fn_pt"))
    assert "WARNING: this recipe mentions peanut" in reply


def test_stats_reply_states_filters_and_denominator(conn):
    s = Session(exclude=["peanut"])
    reply = handle(conn, s, I(action="stats", new_topic=True, text="", stat="step_stats"))
    assert "Filters: must exclude: peanut" in reply
    assert "Recipes analyzed: 3" in reply                             # 4 left, 1 without steps
    assert "Excluded: 1 without instructions" in reply


def test_ranking_results_can_be_opened(conn):
    s = Session()
    handle(conn, s, I(action="stats", new_topic=True, text="", stat="fewest_steps", top_n=2))
    assert s.last_ids == ["ar_cs1", "ar_bb2"]
    assert "Chicken Spinach Skillet" in handle(conn, s, I(action="show_recipe", result_number=1))


def test_unsupported_question_is_refused_not_guessed(conn):
    reply = handle(conn, Session(), I(action="unsupported", missing_attribute="nutrition"))
    assert "it has no nutrition" in reply and "won't guess" in reply


def test_bad_reference_asks_back(conn):
    reply = handle(conn, Session(last_ids=["ar_bb1"]), I(action="show_recipe", result_number=5))
    assert "can't tell which recipe" in reply


# ---------- full turn with a fake Gemini client ----------

class FakeModels:
    """Stands in for client.models: returns `text` as the model's JSON reply."""
    def __init__(self, text, finish_reason=FinishReason.STOP):
        self.text, self.finish_reason, self.calls = text, finish_reason, []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(text=self.text,
                               candidates=[SimpleNamespace(finish_reason=self.finish_reason)])


def fake_parser(intent, finish_reason=FinishReason.STOP, text=None):
    models = FakeModels(text if text is not None else
                        (intent.model_dump_json() if intent else ""), finish_reason)
    return IntentParser(client=SimpleNamespace(models=models), model="test-model"), models


def test_turn_sends_session_context_and_schema(conn):
    s = Session(last_ids=["ar_bb2"], exclude=["egg"])
    parser, models = fake_parser(I(action="show_recipe", result_number=1))
    reply = turn(conn, s, parser, "show me the first one")
    assert "Vegan Banana Bread" in reply
    call = models.calls[0]
    assert call["model"] == "test-model"
    assert call["config"].response_json_schema == TurnIntent.model_json_schema()
    assert call["config"].response_mime_type == "application/json"
    assert '"excluded": ["egg"]' in call["contents"] and "Vegan Banana Bread" in call["contents"]


def test_blocked_or_invalid_output_gives_rephrase_message(conn):
    parser, _ = fake_parser(None, finish_reason=FinishReason.SAFETY)
    assert "couldn't interpret" in turn(conn, Session(), parser, "???")
    parser, _ = fake_parser(None, text='{"action": "dance"}')      # fails TurnIntent validation
    assert "couldn't interpret" in turn(conn, Session(), parser, "???")


def test_local_commands_skip_the_llm(conn):
    parser, models = fake_parser(I(action="help"))
    assert "Active filters" in turn(conn, Session(), parser, "/state")
    assert models.calls == []


def test_expansion_shown_when_added_then_only_in_state(conn):
    s = Session()
    exp = [Expansion(category="nuts", terms=["walnut", "peanut", "almond"])]
    first = handle(conn, s, I(action="search", new_topic=True, text="banana", exclusion_expansions=exp))
    assert "'nuts' was expanded to: walnut, peanut, almond" in first
    second = handle(conn, s, I(action="search", max_steps=3))
    assert "expanded to" not in second and "excluded: walnut, peanut, almond" in second
    assert "expanded to" in handle(conn, s, I(action="show_state"))


# ---------- ingredient matching in the chat ----------

def test_pantry_updates():
    s = Session()
    s.apply(I(action="match", add_have=["2 lb chicken", "rice", "1 onion"]))
    s.apply(I(action="match", add_have=["3 lb chicken"], remove_have=["onions"]))
    assert s.have == ["rice", "3 lb chicken"]                    # same name: new amount replaces old
    s.apply(I(action="match", add_have=["chicken breasts"]))
    assert s.have == ["rice", "3 lb chicken", "chicken breasts"] # different name: both kept
    s.apply(I(action="match", add_have=["eggs"], replace_have=True))
    assert s.have == ["eggs"]


def test_match_reply_shows_matched_missing_and_reason(conn):
    s = Session()
    reply = handle(conn, s, I(action="match", new_topic=True, add_have=["3 bananas", "flour", "2 eggs"]))
    assert reply.startswith("Ranked 3 existing recipes")
    assert "1. Classic Banana Bread  [ar_bb1]" in reply
    assert "banana  <- your '3 bananas' [exact]; enough: you have 3, recipe needs 3" in reply
    assert "flour  <- your 'flour' [exact]; quantity not verified (you gave no amount)" in reply
    assert "missing: walnut" in reply and "why this rank: coverage 3/4" in reply
    assert "your ingredients: 3 bananas, flour, 2 eggs" in reply
    assert s.last_ids[0] == "ar_bb1"


def test_match_keeps_exclusions_and_reports_no_match(conn):
    s = Session(exclude=["egg", "banana"])
    reply = handle(conn, s, I(action="match", add_have=["3 bananas", "2 eggs"]))
    assert reply.startswith("No existing recipe uses any of your ingredients")
    assert "VIOLATES your constraint (allows banana)" in reply
    assert s.exclude == ["egg", "banana"]


def test_warns_when_own_ingredient_contains_excluded_word(conn):
    s = Session(exclude=["milk", "butter"])
    reply = handle(conn, s, I(action="match", add_have=["1 can coconut milk", "3 bananas", "flour"]))
    assert "your '1 can coconut milk' contains the excluded word(s) milk" in reply
    assert "'flour' contains" not in reply
