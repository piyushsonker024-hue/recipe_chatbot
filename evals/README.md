# Eval set

A small, reproducible set of multi-turn conversations run against the real dataset.
The bot's answers are checked automatically. Where a number is involved, it is
recomputed by a **different path** from the one the bot uses (raw JSON, or plain SQL instead of the stats engine).

```bash
python -m evals.run_eval              # scripted mode: no API key needed (~15 s)
python -m evals.run_eval --live       # the real LLM parser reads each message and is scored too
python -m evals.run_eval --case ingredient_matching
python -m evals.one_shot              # one-shot LLM baseline (needs ANTHROPIC_API_KEY)
```

Outputs: [RESULTS.md](RESULTS.md) (the summary table and failed checks) and
[transcripts/](transcripts/) (every turn, with its intent, the bot's reply and each check's result).

## How it works

Each turn in [cases.py](cases.py) has the user's message, the **intent the parser should
produce**, and a set of checks ([checks.py](checks.py)).

- **Scripted mode** executes the expected intent. This evaluates everything after parsing:
  session rules, filters, search, statistics, matching, substitution and the reply text. It is deterministic and needs no key.
- **Live mode** runs the real parser on the message, reports any field that differs
  from the expected intent, and then executes the parsed intent, so the parser and the system are judged together.

The checks:

| Check | What it verifies |
|---|---|
| `aggregate_fields` | Every statistic states filters, n analyzed, denominator, calculation and rules |
| `share_matches_sql` | An ingredient share agrees with a plain-SQL recount (within the part-word difference, shown) |
| `step_stats_match_raw` | Step mean and median by source agree with a recount from the **raw JSON files** |
| `results_respect_exclusions` | Each listed recipe is re-checked on its own: none mentions an excluded term |
| `results_within_steps` | Each listed recipe is within the step limit (unknown counts fail) |
| `ids_exist` | Every recipe ID cited in the reply exists in the dataset |
| `state` | A restriction persists across turns and topic changes |
| `titles_contain` | Results are actually the requested dish, or the reply says nothing matches |
| `no_number_for` | No value is stated for an attribute the data lacks (calories, minutes) |

## The conversations

| Case | What it shows |
|---|---|
| multi_turn_followup | Search, then a nut allergy, a step limit, "the second one", and a new topic. Exclusions and the step limit persist. |
| aggregate_statistics | Garlic share (26.4%, checked against SQL), the same share restricted to chicken recipes, steps by source (checked against raw JSON), and top cookie ingredients |
| no_match_with_marked_alternatives | Lobster bisque with a shellfish allergy: says no match, then offers 14 lobster bisques labeled "VIOLATES your constraint" |
| no_match_cheesecake | Vegan cheesecake with no dairy, no eggs and at most 2 steps: no match, and says that relaxing one constraint doesn't help |
| ingredient_matching | Ranked matches with coverage/usage arithmetic and quantity checks, then constraints added later. The user's ingredients are kept. |
| substitution_weak_conflicting | Eggs in Country Banana Bread: every candidate is weak, conflicts are flagged, web search is used only on request |
| substitution_respects_exclusion | Butter in Banana Banana Bread with "no margarine": the strongest candidate is shown as violating, olive oil is used, and an explicit request for margarine gets a warning |
| missing_attributes | Calories and cooking time: refused, with no number given |
| known_quantity_not_in_ranking | **Known failure**, see below |
| known_same_dish_by_title_words | **Known failure**, see below |

## What worked

- Every number checked agrees with an independent recount. The garlic share is 32,908 of 124,483. A plain-SQL recount using only the last-word rule gets 32,716; the 192 extra recipes are part-word names such as "garlic clove". Step stats by source match a recount from the raw files exactly.
- Hard constraints held in every case: no listed recipe mentioned an excluded term or broke the step limit, including after a topic change.
- Weak and conflicting substitution evidence is labeled as such and never shown as strong.

## What failed, and why

1. **Found by this eval and fixed: a no-match was hidden by the any-word fallback.**
   "Lobster bisque" with shellfish excluded returned tomato and pumpkin bisques, and
   "vegan cheesecake, no dairy or eggs, 2 steps" returned smoothies and dressings. The reply did say
   "these match some of the words", but this breaks the rule that when nothing matches, the bot says so.
   *Cause:* `find_matches` fell back to any-word matching whenever the result was empty,
   including when the hard filters had emptied it. *Fix:* fall back only when the words
   never occur together anywhere in the dataset. Otherwise the result stays empty and
   the no-match reply lists alternatives labeled as violating a constraint
   (regression test: `tests/test_search.py::test_no_fallback_when_filters_remove_the_dish`).
2. **Known: quantity shortfalls do not affect the ranking.** With "2 eggs", Dessert Crepes
   (needs 4) ties with Butterscotch Pudding (needs 2) at score 1.00, and ranks above a result
   the user can make. The shortfall is reported ("not enough: you have 2, recipe needs 4"),
   but the score is name-level only. *Why it was left:* quantities are comparable for only some
   lines, and scoring them only where parseable would rank recipes with unparseable amounts
   above ones with a known shortfall. A fair option is a tie-breaker: "fewer known shortfalls" first.
3. **Known: same-dish evidence depends on title words.** "Chicken Valdostano" has no other
   recipe with that name, so 0 same-dish recipes are compared. Only other-dish (indirect)
   evidence remains, and it is labeled as such. *Why:* there's no dish or category label in the data. Finding similar
   recipes by ingredient overlap would fix it, at the cost of a slower lookup.

## One-shot LLM vs this system

`python -m evals.one_shot` asks the same model the same questions with **no data**, then
grades the answers against the computed results. It writes [ONE_SHOT.md](ONE_SHOT.md) with each
answer verbatim. **It has not been run yet:** there was no API key on the build machine. Until it runs, these
are the computed answers it will be graded against:

| Question | Grounded answer (this system) | Why a one-shot answer fails |
|---|---|---|
| Share of recipes with garlic | 26.4% (32,908 of 124,483) | The model has never counted this dataset, so any figure is an estimate |
| 3 banana bread recipes with IDs | e.g. `ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC` | Keys are random 32-character strings. The model can't know them, so an ID it gives is invented unless it declines (`ids_exist` grades this). |
| Mean steps in Allrecipes recipes | 3.32 over 39,522 recipes (one paragraph per step) | It depends on a counting rule the model doesn't know |
| Lobster bisque with a shellfish allergy | 0 recipes. The bot says so and offers violating alternatives, labeled. | A helpful one-shot answer tends to adapt a recipe instead of saying none exists in the data |

The ID question is the clearest case: a one-shot answer cannot be both specific and
grounded. This system can, because it only cites IDs it retrieved, and the eval checks that every one exists.

## Limits of this eval

- It is small (10 conversations, 26 turns, 57 checks) and was written by the developer, who also chose the expected intents.
- Scripted mode doesn't test the parser. Live mode does, but it hasn't been run yet (no key).
- Substitution checks verify labeling and constraints, not whether the cooked result would be good. That would need cooking it.
