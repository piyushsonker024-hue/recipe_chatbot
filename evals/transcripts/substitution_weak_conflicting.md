# substitution_weak_conflicting

Covers: Task 3 with weak and conflicting evidence; web search only on request

Mode: scripted intents

## Turn 1

**User:** show me recipe ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi

**Intent:** `{"action":"show_recipe","recipe_id":"ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi"}`

**Bot:**

```
Country Banana Bread  [ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi]
Ingredients (as written in the source):
  - 1 (18.25 ounce) package yellow cake mix
  - 3 eggs
  - 1 1/3 cups vegetable oil
  - 4 bananas, mashed
Instructions (3 steps):
  1. Preheat oven to 350 degrees F (175 degrees C). Grease a 9x13 inch pan.
  2. In a mixing bowl, combine cake mix, eggs, oil, and bananas. Pour mixture into the prepared pan.
  3. Bake in preheated 350 degrees F (175 degrees C) for 35 to 40 minutes.
Nutrition and cooking times are not in the dataset.

Active filters: no filters
```

**Checks:**

- PASS: contains 'Country Banana Bread', '3 eggs' (reply contains ('Country Banana Bread', '3 eggs'))

_0.0 s_

## Turn 2

**User:** I'm out of eggs. What can I use instead?

**Intent:** `{"action":"substitute","sub_target":"eggs"}`

**Bot:**

```
Substituting egg in Country Banana Bread  [ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi]
This recipe uses: 3 eggs
Compared against 191 recipes of the same dish.
Dataset evidence (verified: these recipes exist and say this):
1. egg substitute: WEAK evidence
   - [stated in other dishes] 9 recipes of other dishes list it as an alternative: epi_E7kbb7yJ9.Js.63QkaAtpdmez6u06zC, epi_LSm1hzr0Vqt1sNp2f5ml93JmmG7Qm2C, epi_cTG4e2s8RON5swgZSMmn6Omhx7Q9MGi, epi_n7sI/6SVOyP.oVvxZUXCbp1i4ojElOW, fn_.Dokq9ZQytANkB9crH.B1B2He.IwG4m
   - used together with egg in 0 recipes (0% of the rarer one's recipes)
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
2. meringue powder: WEAK evidence
   - [stated in other dishes] 5 recipes of other dishes list it as an alternative: fn_5CSzXV5oHJVBgOs1fQh4ZsO2aXwjelC, fn_85LTrUI81yGJrm/DqMT8wa19/nY.kL6, fn_9zKDNB6o9lgFAP1Alv.ZHE1AivMyR/K, fn_CYOSQPjy.wBNSm2amVvYD3Kcs.AYRSK, fn_f.IdqGLJukYPIBzUOZn.d99I5aWU.6e
   - used together with egg in 34 recipes (51% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 34 recipes (51% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
3. evaporated milk: WEAK evidence
   - [stated in other dishes] 1 recipe of other dishes lists it as an alternative: epi_DiKM3xoQccTZ7paC.XGMVpHMD8gchRm
   - used together with egg in 395 recipes (50% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 395 recipes (50% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
4. heavy cream: WEAK evidence
   - [stated in other dishes] 1 recipe of other dishes lists it as an alternative: epi_LE5Hd9OzRb.jSQi7BnLqOHBCbIKqcpO
   - used together with egg in 2,841 recipes (28% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 2,841 recipes (28% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
5. milk: WEAK evidence
   - [stated in other dishes] 1 recipe of other dishes lists it as an alternative: fn_JLC5AaIxURarKNvxDd2ne2JWekCS4oC
   - [usage pattern (indirect)] used with similar ingredients as the target (similarity 0.66 on a 0-1 scale)
   - used together with egg in 4,987 recipes (51% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 4,987 recipes (51% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
Updated recipe with egg substitute instead of egg (PREDICTION: not tested; picked because it has the strongest dataset evidence):
  Ingredients:
    - 1 (18.25 ounce) package yellow cake mix
    - 3 egg substitute   [changed; was '3 eggs'; same amount assumed]
    - 1 1/3 cups vegetable oil
    - 4 bananas, mashed
  Instructions:
    1. Preheat oven to 350 degrees F (175 degrees C). Grease a 9x13 inch pan.
    2. In a mixing bowl, combine cake mix, egg substitute, oil, and bananas. Pour mixture into the prepared pan.   [changed]
    3. Bake in preheated 350 degrees F (175 degrees C) for 35 to 40 minutes.
  Verified: the dataset has recipes that use egg substitute where others use egg (IDs above).
  Predicted, not verified: that this recipe works with egg substitute at the same amount; texture, taste and cooking time may change.
Note: Dataset evidence is weak for this substitution. You can ask me to search the web; those results are shown separately and are not verified.
Safety: Recipe text alone cannot show that a substitution is safe for an allergy or a medical diet. Check product labels, and ask a professional if it matters.
External sources: not used. Say "search the web" to see outside sources (shown separately, with links).

Active filters: no filters
```

**Checks:**

- PASS: contains 'WEAK evidence', 'conflicting', 'PREDICTION', 'same amount assumed', 'Safety:', 'Dataset evidence is weak' (reply contains ('WEAK evidence', 'conflicting', 'PREDICTION', 'same amount assumed', 'Safety:', 'Dataset evidence is weak'))
- PASS: does not contain 'STRONG evidence', 'WEB SEARCH' (none present)
- PASS: every cited recipe ID exists in the dataset (1 IDs, all exist)

_1.0 s_

## Turn 3

**User:** can you search the web for that?

**Intent:** `{"action":"substitute","sub_target":"eggs","use_web":true}`

**Bot:**

```
Substituting egg in Country Banana Bread  [ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi]
This recipe uses: 3 eggs
Compared against 191 recipes of the same dish.
Dataset evidence (verified: these recipes exist and say this):
1. egg substitute: WEAK evidence
   - [stated in other dishes] 9 recipes of other dishes list it as an alternative: epi_E7kbb7yJ9.Js.63QkaAtpdmez6u06zC, epi_LSm1hzr0Vqt1sNp2f5ml93JmmG7Qm2C, epi_cTG4e2s8RON5swgZSMmn6Omhx7Q9MGi, epi_n7sI/6SVOyP.oVvxZUXCbp1i4ojElOW, fn_.Dokq9ZQytANkB9crH.B1B2He.IwG4m
   - used together with egg in 0 recipes (0% of the rarer one's recipes)
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
2. meringue powder: WEAK evidence
   - [stated in other dishes] 5 recipes of other dishes list it as an alternative: fn_5CSzXV5oHJVBgOs1fQh4ZsO2aXwjelC, fn_85LTrUI81yGJrm/DqMT8wa19/nY.kL6, fn_9zKDNB6o9lgFAP1Alv.ZHE1AivMyR/K, fn_CYOSQPjy.wBNSm2amVvYD3Kcs.AYRSK, fn_f.IdqGLJukYPIBzUOZn.d99I5aWU.6e
   - used together with egg in 34 recipes (51% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 34 recipes (51% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
3. evaporated milk: WEAK evidence
   - [stated in other dishes] 1 recipe of other dishes lists it as an alternative: epi_DiKM3xoQccTZ7paC.XGMVpHMD8gchRm
   - used together with egg in 395 recipes (50% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 395 recipes (50% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
4. heavy cream: WEAK evidence
   - [stated in other dishes] 1 recipe of other dishes lists it as an alternative: epi_LE5Hd9OzRb.jSQi7BnLqOHBCbIKqcpO
   - used together with egg in 2,841 recipes (28% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 2,841 recipes (28% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
5. milk: WEAK evidence
   - [stated in other dishes] 1 recipe of other dishes lists it as an alternative: fn_JLC5AaIxURarKNvxDd2ne2JWekCS4oC
   - [usage pattern (indirect)] used with similar ingredients as the target (similarity 0.66 on a 0-1 scale)
   - used together with egg in 4,987 recipes (51% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 4,987 recipes (51% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
   - note: weak: little or only indirect evidence
Updated recipe with egg substitute instead of egg (PREDICTION: not tested; picked because it has the strongest dataset evidence):
  Ingredients:
    - 1 (18.25 ounce) package yellow cake mix
    - 3 egg substitute   [changed; was '3 eggs'; same amount assumed]
    - 1 1/3 cups vegetable oil
    - 4 bananas, mashed
  Instructions:
    1. Preheat oven to 350 degrees F (175 degrees C). Grease a 9x13 inch pan.
    2. In a mixing bowl, combine cake mix, egg substitute, oil, and bananas. Pour mixture into the prepared pan.   [changed]
    3. Bake in preheated 350 degrees F (175 degrees C) for 35 to 40 minutes.
  Verified: the dataset has recipes that use egg substitute where others use egg (IDs above).
  Predicted, not verified: that this recipe works with egg substitute at the same amount; texture, taste and cooking time may change.
Note: Dataset evidence is weak for this substitution. You can ask me to search the web; those results are shown separately and are not verified.
Safety: Recipe text alone cannot show that a substitution is safe for an allergy or a medical diet. Check product labels, and ask a professional if it matters.
External web search is not available in this session.

Active filters: no filters
```

**Checks:**

- PASS: contains 'External' (reply contains ('External',))

_0.5 s_
