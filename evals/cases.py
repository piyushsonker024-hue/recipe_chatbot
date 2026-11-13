"""Eval conversations. Each turn has:

  user    what the user types
  intent  the structured intent the parser *should* produce. In scripted mode it is
          executed directly, so the deterministic system (filters, search, stats,
          matching, substitution, replies) is evaluated without an API key. In live
          mode the real parser runs on `user` and is scored against the keys in `intent`.
  checks  what the reply and session must satisfy (evals/checks.py)

`expect_fail` marks a case kept on purpose to document a known failure.
"""

from .checks import (aggregate_fields, contains, ids_exist, no_number_for, not_contains,
                     quantity_shortfalls_rank_lower, results_respect_exclusions,
                     results_within_steps, same_dish_found, share_matches_sql, state,
                     step_stats_match_raw, titles_contain)

NUTS = {"category": "nuts", "terms": ["walnut", "pecan", "almond", "hazelnut", "peanut",
                                      "cashew", "pistachio", "macadamia", "nut"]}
DAIRY = {"category": "dairy", "terms": ["milk", "butter", "cheese", "cream", "yogurt",
                                        "cream cheese", "sour cream", "buttermilk"]}
SHELLFISH = {"category": "shellfish", "terms": ["shrimp", "prawn", "crab", "lobster", "scallop",
                                                "clam", "mussel", "oyster", "crawfish"]}
COUNTRY_BANANA_BREAD = "ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi"
BANANA_BANANA_BREAD = "ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC"
CHICKEN_VALDOSTANO = "ar_BnEOdvcvT7mEOpAkTGYs.dv17W33eCG"

CONVERSATIONS = [
    {
        "name": "multi_turn_followup",
        "covers": "Task 1 search; follow-ups; a restriction persists across a topic change",
        "turns": [
            {"user": "Show me banana bread recipes",
             "intent": {"action": "search", "new_topic": True, "text": "banana bread", "title_only": True},
             "checks": [contains("Banana Bread"), ids_exist(), titles_contain("banana bread")]},
            {"user": "I'm allergic to nuts",
             "intent": {"action": "search", "exclusion_expansions": [NUTS]},
             "checks": [state(text="banana bread", exclude=["walnut", "pecan", "nut"]),
                        results_respect_exclusions()]},
            {"user": "only ones with 5 steps or fewer",
             "intent": {"action": "search", "max_steps": 5},
             "checks": [results_within_steps(), results_respect_exclusions()]},
            {"user": "show me the second one",
             "intent": {"action": "show_recipe", "result_number": 2},
             "checks": [contains("Ingredients (as written in the source):", "Instructions"),
                        not_contains("WARNING")]},
            {"user": "now muffins instead",
             "intent": {"action": "search", "new_topic": True, "text": "muffins", "title_only": True},
             "checks": [state(text="muffins", max_steps=5, exclude=["walnut", "nut"]),
                        results_respect_exclusions(), results_within_steps(),
                        contains("excluded: walnut")]},
        ],
    },
    {
        "name": "aggregate_statistics",
        "covers": "Task 1 statistics computed in code, with independent recomputation",
        "turns": [
            {"user": "What percentage of recipes use garlic?",
             "intent": {"action": "stats", "new_topic": True, "stat": "ingredient_share",
                        "stat_term": "garlic"},
             "checks": [aggregate_fields(), share_matches_sql("garlic"), contains("26.4%")]},
            {"user": "And among chicken recipes?",
             "intent": {"action": "stats", "stat": "ingredient_share", "stat_term": "garlic",
                        "add_include": ["chicken"]},
             "checks": [aggregate_fields(), contains("chicken"), not_contains("124,483 matching")]},
            {"user": "What's the average and median number of steps for each source?",
             "intent": {"action": "stats", "new_topic": True, "stat": "step_stats", "by_source": True},
             "checks": [aggregate_fields(), step_stats_match_raw(),
                        contains("without instructions (unknown steps)")]},
            {"user": "Top 10 ingredients in cookie recipes, not counting salt",
             "intent": {"action": "stats", "new_topic": True, "text": "cookies", "title_only": True,
                        "stat": "top_ingredients", "top_n": 10, "stat_skip": ["salt"]},
             "checks": [aggregate_fields(), contains("butter", "flour"), not_contains("name=salt,")]},
        ],
    },
    {
        "name": "no_match_with_marked_alternatives",
        "covers": "Hard constraint makes the result empty; alternatives are labeled as violating it",
        "turns": [
            {"user": "Lobster bisque, but I'm allergic to shellfish",
             "intent": {"action": "search", "new_topic": True, "text": "lobster bisque",
                        "title_only": True, "exclusion_expansions": [SHELLFISH]},
             "checks": [contains("No recipe matches all of your constraints", "VIOLATES your constraint"),
                        state(exclude=["lobster"])]},
            {"user": "ok what about any bisque then",
             "intent": {"action": "search", "new_topic": True, "text": "bisque", "title_only": True},
             "checks": [results_respect_exclusions(), state(exclude=["lobster", "shrimp"])]},
        ],
    },
    {
        "name": "no_match_cheesecake",
        "covers": "No match under three hard constraints (found and fixed by this eval: it used "
                  "to fall back to any-word matches such as smoothies)",
        "turns": [
            {"user": "vegan cheesecake with no dairy or eggs, 2 steps max",
             "intent": {"action": "search", "new_topic": True, "text": "vegan cheesecake",
                        "exclusion_expansions": [DAIRY], "add_exclude": ["egg"], "max_steps": 2},
             "checks": [titles_contain("cheesecake"), results_respect_exclusions()]},
        ],
    },
    {
        "name": "ingredient_matching",
        "covers": "Task 2: ranked existing recipes, matched/missing, quantities, constraints added later",
        "turns": [
            {"user": "I have 2 lb chicken breast, 1 onion, 3 cloves garlic, rice and a can of coconut milk. What can I make?",
             "intent": {"action": "match", "new_topic": True,
                        "add_have": ["2 lb chicken breast", "1 onion", "3 cloves garlic", "rice",
                                     "1 can coconut milk"]},
             "checks": [ids_exist(), contains("coverage", "missing", "score ="),
                        contains("not verified")]},
            {"user": "no dairy please, and at most 4 steps",
             "intent": {"action": "match", "exclusion_expansions": [DAIRY], "max_steps": 4},
             "checks": [results_respect_exclusions(), results_within_steps(),
                        state(have=["2 lb chicken breast", "rice"])]},
        ],
    },
    {
        "name": "substitution_weak_conflicting",
        "covers": "Task 3 with weak and conflicting evidence; web search only on request",
        "turns": [
            {"user": f"show me recipe {COUNTRY_BANANA_BREAD}",
             "intent": {"action": "show_recipe", "recipe_id": COUNTRY_BANANA_BREAD},
             "checks": [contains("Country Banana Bread", "3 eggs")]},
            {"user": "I'm out of eggs. What can I use instead?",
             "intent": {"action": "substitute", "sub_target": "eggs"},
             "checks": [contains("WEAK evidence", "conflicting", "PREDICTION", "same amount assumed",
                                 "Safety:", "Dataset evidence is weak"),
                        not_contains("STRONG evidence", "WEB SEARCH"), ids_exist()]},
            {"user": "can you search the web for that?",
             "intent": {"action": "substitute", "sub_target": "eggs", "use_web": True},
             "checks": [contains("External")]},
        ],
    },
    {
        "name": "substitution_respects_exclusion",
        "covers": "Task 3: best-evidence substitute is excluded by the user, so the next one is used",
        "turns": [
            {"user": f"show me recipe {BANANA_BANANA_BREAD}",
             "intent": {"action": "show_recipe", "recipe_id": BANANA_BANANA_BREAD},
             "checks": [contains("Banana Banana Bread")]},
            {"user": "no margarine in anything please",
             "intent": {"action": "search", "add_exclude": ["margarine"]},
             "checks": [state(exclude=["margarine"])]},
            {"user": "what can I use instead of butter in it?",
             "intent": {"action": "substitute", "sub_target": "butter", "recipe_id": BANANA_BANANA_BREAD},
             "checks": [contains("margarine: STRONG evidence", "BREAKS your exclusion: margarine",
                                 "Updated recipe with olive oil", "REVIEW:"),
                        not_contains("Updated recipe with margarine")]},
            {"user": "what about margarine anyway?",
             "intent": {"action": "substitute", "sub_target": "butter", "sub_candidate": "margarine",
                        "recipe_id": BANANA_BANANA_BREAD},
             "checks": [contains("WARNING: margarine breaks your exclusion")]},
        ],
    },
    {
        "name": "missing_attributes",
        "covers": "Nutrition and cooking time are not in the data: refuse, don't estimate",
        "turns": [
            {"user": f"show me recipe {BANANA_BANANA_BREAD}",
             "intent": {"action": "show_recipe", "recipe_id": BANANA_BANANA_BREAD},
             "checks": [contains("Nutrition and cooking times are not in the dataset")]},
            {"user": "How many calories per slice?",
             "intent": {"action": "unsupported", "missing_attribute": "calories"},
             "checks": [contains("can't answer"), no_number_for("calories"), no_number_for("kcal")]},
            {"user": "What's the average cooking time of soups?",
             "intent": {"action": "unsupported", "missing_attribute": "cooking time"},
             "checks": [contains("can't answer"), no_number_for("minutes")]},
        ],
    },
    {
        "name": "known_quantity_not_in_ranking",
        "covers": "KNOWN FAILURE: a recipe needing 4 eggs ranks level with one you can make with your 2",
        "expect_fail": True,
        "turns": [
            {"user": "I have flour, sugar, butter, 2 eggs and milk",
             "intent": {"action": "match", "new_topic": True,
                        "add_have": ["flour", "sugar", "butter", "2 eggs", "milk"]},
             "checks": [contains("not enough: you have 2, recipe needs 4"),
                        quantity_shortfalls_rank_lower()]},
        ],
    },
    {
        "name": "known_same_dish_by_title_words",
        "covers": "KNOWN FAILURE: same-dish evidence relies on title words, so a uniquely named dish has none",
        "expect_fail": True,
        "turns": [
            {"user": "what can I use instead of butter in Chicken Valdostano?",
             "intent": {"action": "substitute", "sub_target": "butter", "recipe_id": CHICKEN_VALDOSTANO},
             "checks": [contains("indirect"), same_dish_found(5)]},
        ],
    },
]
