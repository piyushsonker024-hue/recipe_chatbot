# aggregate_statistics

Covers: Task 1 statistics computed in code, with independent recomputation

Mode: scripted intents

## Turn 1

**User:** What percentage of recipes use garlic?

**Intent:** `{"action":"stats","new_topic":true,"stat":"ingredient_share","stat_term":"garlic"}`

**Bot:**

```
Computed in code over the full filtered set:
Question: Share of recipes containing 'garlic'
Filters: none (all recipes)
Recipes analyzed: 124,483
Denominator: 124,483 matching recipes
Calculation: recipes with a name matching 'garlic' / matching recipes x 100
Result: 32,908 of 124,483 = 26.4%
  counted_name=garlic, recipes=31806
  counted_name=granulated garlic, recipes=412
  counted_name=roasted garlic, recipes=207
  counted_name=whole garlic clove, recipes=63
  counted_name=whole cloves garlic, recipes=43
Note: Most common names counted as this ingredient are listed above.
Rule (normalization): Ingredient names are normalized by rule: lowercase; quantities, units, parentheticals and prep/size words removed; first 'or' alternative kept; last word singularized; small synonym map (e.g. kosher salt -> salt). Distinct products stay distinct (butter vs peanut butter).
Rule (include): An ingredient term matches a normalized name if it is the name's last word(s) ('spinach' -> 'baby spinach') or is followed only by part words ('chicken' -> 'chicken breast'); derived products do not match ('chicken broth', 'peanut butter' for 'butter').

Active filters: no filters
```

**Checks:**

- PASS: states filters, n analyzed, denominator, calculation and rules (reply contains ('Filters:', 'Recipes analyzed:', 'Denominator:', 'Calculation:', 'Rule ('))
- PASS: 'garlic' share agrees with an independent SQL count (bot 32,908/124,483; plain SQL (last-word rule only) 32,716/124,483; difference 192 from part-word names)
- PASS: contains '26.4%' (reply contains ('26.4%',))

_3.8 s_

## Turn 2

**User:** And among chicken recipes?

**Intent:** `{"action":"stats","add_include":["chicken"],"stat":"ingredient_share","stat_term":"garlic"}`

**Bot:**

```
Computed in code over the full filtered set:
Question: Share of recipes containing 'garlic'
Filters: must include: chicken
Recipes analyzed: 9,364
Denominator: 9,364 matching recipes
Calculation: recipes with a name matching 'garlic' / matching recipes x 100
Result: 4,287 of 9,364 = 45.8%
  counted_name=garlic, recipes=4149
  counted_name=granulated garlic, recipes=78
  counted_name=roasted garlic, recipes=16
  counted_name=whole garlic clove, recipes=9
  counted_name=bulb garlic, recipes=8
Note: Most common names counted as this ingredient are listed above.
Rule (normalization): Ingredient names are normalized by rule: lowercase; quantities, units, parentheticals and prep/size words removed; first 'or' alternative kept; last word singularized; small synonym map (e.g. kosher salt -> salt). Distinct products stay distinct (butter vs peanut butter).
Rule (include): An ingredient term matches a normalized name if it is the name's last word(s) ('spinach' -> 'baby spinach') or is followed only by part words ('chicken' -> 'chicken breast'); derived products do not match ('chicken broth', 'peanut butter' for 'butter').

Active filters: must include: chicken
```

**Checks:**

- PASS: states filters, n analyzed, denominator, calculation and rules (reply contains ('Filters:', 'Recipes analyzed:', 'Denominator:', 'Calculation:', 'Rule ('))
- PASS: contains 'chicken' (reply contains ('chicken',))
- PASS: does not contain '124,483 matching' (none present)

_0.6 s_

## Turn 3

**User:** What's the average and median number of steps for each source?

**Intent:** `{"action":"stats","new_topic":true,"stat":"step_stats","by_source":true}`

**Bot:**

```
Computed in code over the full filtered set:
Question: Step count statistics
Filters: none (all recipes)
Recipes analyzed: 124,450
Denominator: 124,450 matching recipes with a known step count
Excluded: 33 without instructions (unknown steps)
Calculation: mean, median, min, max of step count (pandas)
Result: {'mean': 4.0, 'median': 4.0, 'min': 1, 'max': 71}
  source=ar, recipes=39522, mean=3.32, median=3.0, min=1, max=22
  source=epi, recipes=25300, mean=5.02, median=4.0, min=2, max=71
  source=fn, recipes=59628, mean=4.02, median=4.0, min=1, max=63
Rule (steps): A step is one non-empty paragraph of the original instructions. Sources split steps differently (Allrecipes: one action per line; Food Network and Epicurious: paragraphs with several actions), so cross-source comparisons are rough. Recipes without instructions have unknown steps and are excluded, never counted as 0.

Active filters: no filters
```

**Checks:**

- PASS: states filters, n analyzed, denominator, calculation and rules (reply contains ('Filters:', 'Recipes analyzed:', 'Denominator:', 'Calculation:', 'Rule ('))
- PASS: steps by source agree with a recount from the raw JSON files (ar: bot n=39,522 mean=3.32 median=3.0; raw n=39,522 mean=3.32 median=3.0; epi: bot n=25,300 mean=5.02 median=4.0; raw n=25,300 mean=5.02 median=4.0; fn: bot n=59,628 mean=4.02 median=4.0; raw n=59,628 mean=4.02 median=4.0)
- PASS: contains 'without instructions (unknown steps)' (reply contains ('without instructions (unknown steps)',))

_0.8 s_

## Turn 4

**User:** Top 10 ingredients in cookie recipes, not counting salt

**Intent:** `{"action":"stats","new_topic":true,"text":"cookies","title_only":true,"stat":"top_ingredients","top_n":10,"stat_skip":["salt"]}`

**Bot:**

```
Computed in code over the full filtered set:
Question: Top 10 ingredients
Filters: text "cookies" (every word in title)
Recipes analyzed: 3,113
Denominator: 3,113 matching recipes (each percentage = recipes using the name / this)
Calculation: COUNT DISTINCT recipes per normalized name, sorted descending
  rank=1, ingredient=flour, recipes=2325, pct=74.7
  rank=2, ingredient=butter, recipes=2121, pct=68.1
  rank=3, ingredient=sugar, recipes=2086, pct=67.0
  rank=4, ingredient=egg, recipes=2071, pct=66.5
  rank=5, ingredient=vanilla extract, recipes=1899, pct=61.0
  rank=6, ingredient=baking soda, recipes=1448, pct=46.5
  rank=7, ingredient=brown sugar, recipes=1227, pct=39.4
  rank=8, ingredient=baking powder, recipes=926, pct=29.7
  rank=9, ingredient=powdered sugar, recipes=661, pct=21.2
  rank=10, ingredient=cinnamon, recipes=616, pct=19.8
Note: Left out of the ranking on request: salt
Rule (text): Text search requires every query word (stemmed) in the title, ingredient names or instructions; if none match, any word is accepted and this is stated.
Rule (normalization): Ingredient names are normalized by rule: lowercase; quantities, units, parentheticals and prep/size words removed; first 'or' alternative kept; last word singularized; small synonym map (e.g. kosher salt -> salt). Distinct products stay distinct (butter vs peanut butter).
Rule (unique_names): Each recipe counts an ingredient name once, even if it is listed twice.

Active filters: search "cookies" (titles only)
```

**Checks:**

- PASS: states filters, n analyzed, denominator, calculation and rules (reply contains ('Filters:', 'Recipes analyzed:', 'Denominator:', 'Calculation:', 'Rule ('))
- PASS: contains 'butter', 'flour' (reply contains ('butter', 'flour'))
- PASS: does not contain 'name=salt,' (none present)

_0.3 s_
