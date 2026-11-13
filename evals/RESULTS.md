# Eval results

Mode: scripted intents (no API key needed). Re-run with `python -m evals.run_eval`.

Checks passed: 55/57

| Case | Covers | Turns | Checks | Outcome |
|---|---|---|---|---|
| [multi_turn_followup](transcripts/multi_turn_followup.md) | Task 1 search; follow-ups; a restriction persists across a topic change | 5 | 13/13 | PASS |
| [aggregate_statistics](transcripts/aggregate_statistics.md) | Task 1 statistics computed in code, with independent recomputation | 4 | 12/12 | PASS |
| [no_match_with_marked_alternatives](transcripts/no_match_with_marked_alternatives.md) | Hard constraint makes the result empty; alternatives are labeled as violating it | 2 | 4/4 | PASS |
| [no_match_cheesecake](transcripts/no_match_cheesecake.md) | No match under three hard constraints (found and fixed by this eval: it used to fall back to any-word matches such as smoothies) | 1 | 2/2 | PASS |
| [ingredient_matching](transcripts/ingredient_matching.md) | Task 2: ranked existing recipes, matched/missing, quantities, constraints added later | 2 | 6/6 | PASS |
| [substitution_weak_conflicting](transcripts/substitution_weak_conflicting.md) | Task 3 with weak and conflicting evidence; web search only on request | 3 | 5/5 | PASS |
| [substitution_respects_exclusion](transcripts/substitution_respects_exclusion.md) | Task 3: best-evidence substitute is excluded by the user, so the next one is used | 4 | 5/5 | PASS |
| [missing_attributes](transcripts/missing_attributes.md) | Nutrition and cooking time are not in the data: refuse, don't estimate | 3 | 6/6 | PASS |
| [known_quantity_not_in_ranking](transcripts/known_quantity_not_in_ranking.md) | KNOWN FAILURE: a recipe needing 4 eggs ranks level with one you can make with your 2 | 1 | 1/2 | FAIL (known, documented) |
| [known_same_dish_by_title_words](transcripts/known_same_dish_by_title_words.md) | KNOWN FAILURE: same-dish evidence relies on title words, so a uniquely named dish has none | 1 | 1/2 | FAIL (known, documented) |

## Failed checks

- **known_quantity_not_in_ranking**: results with a quantity shortfall rank below results without one: results with a shortfall at ranks [2, 3, 4], without at [1, 5]
- **known_same_dish_by_title_words**: at least 5 recipes of the same dish are compared: 0 same-dish recipes compared
