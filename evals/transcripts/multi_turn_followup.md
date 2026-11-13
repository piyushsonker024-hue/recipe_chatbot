# multi_turn_followup

Covers: Task 1 search; follow-ups; a restriction persists across a topic change

Mode: scripted intents

## Turn 1

**User:** Show me banana bread recipes

**Intent:** `{"action":"search","new_topic":true,"text":"banana bread","title_only":true}`

**Bot:**

```
Found 192 recipes; showing 10 (best text match first):
1. Banana Bread Chocolate Chip  [fn_3vZMKCWMnF0soLgT6Xio.1.jUzfJ8M2]  (1 step, no ingredient list)
2. Country Banana Bread  [ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi]  (3 steps, 4 ingredients)
3. Banana Banana Bread  [ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC]  (3 steps, 7 ingredients)
4. Rich and Delicious Banana Bread  [ar_TJFqS5qmSUVcBw7c2Da99BzhmvnbgCm]  (3 steps, 6 ingredients)
5. Banana Bread French Toast  [ar_GiHk4/Wm95WTxwkxlmJtSmHUBdpv2La]  (2 steps, 6 ingredients)
6. Very Banana-y Whole Wheat Banana Bread  [ar_wd5llhCCu/vn.eGfx6SvCP2zsq1lSPS]  (4 steps, 9 ingredients)
7. The Best Banana Bread  [ar_pW/G7uT3a0khPJWk/AzOieElj4cz2ku]  (3 steps, 6 ingredients)
8. Organic Banana Bread  [ar_4dTqnPnP8FOgBWmIKlfhquqs.yd1iNW]  (2 steps, 11 ingredients)
9. Banana Bread  [ar_BoBTO3QUO3Ci.0kayPs8.CfDU5oEXuu]  (3 steps, 7 ingredients)
10. Healthier Banana Banana Bread  [ar_zPU0I27hBx09bNpfvQEjNTyHl/X7uwK]  (3 steps, 8 ingredients)
Ask for "the 2nd one" to see its ingredients and instructions.

Active filters: search "banana bread" (titles only)
```

**Checks:**

- PASS: contains 'Banana Bread' (reply contains ('Banana Bread',))
- PASS: every cited recipe ID exists in the dataset (10 IDs, all exist)
- PASS: results are 'banana bread' recipes, or the reply says nothing matches (all results are the dish)

_0.1 s_

## Turn 2

**User:** I'm allergic to nuts

**Intent:** `{"action":"search","exclusion_expansions":[{"category":"nuts","terms":["walnut","pecan","almond","hazelnut","peanut","cashew","pistachio","macadamia","nut"]}]}`

**Bot:**

```
Found 87 recipes; showing 10 (best text match first):
1. Country Banana Bread  [ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi]  (3 steps, 4 ingredients)
2. Banana Banana Bread  [ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC]  (3 steps, 7 ingredients)
3. Rich and Delicious Banana Bread  [ar_TJFqS5qmSUVcBw7c2Da99BzhmvnbgCm]  (3 steps, 6 ingredients)
4. Banana Bread French Toast  [ar_GiHk4/Wm95WTxwkxlmJtSmHUBdpv2La]  (2 steps, 6 ingredients)
5. The Best Banana Bread  [ar_pW/G7uT3a0khPJWk/AzOieElj4cz2ku]  (3 steps, 6 ingredients)
6. Healthier Banana Banana Bread  [ar_zPU0I27hBx09bNpfvQEjNTyHl/X7uwK]  (3 steps, 8 ingredients)
7. Janine's Best Banana Bread  [ar_r.uL.9n9ARPdY33iuX0JqWoLzor1ppa]  (3 steps, 7 ingredients)
8. Joy's Easy Banana Bread  [ar_1FDH/3jPeNVkGWMvwU857yJJCQL8qS6]  (3 steps, 7 ingredients)
9. Banana Bread  [fn_J9d89klHetj.4b5OKiASicRh8tfXK6m]  (2 steps, 10 ingredients)
10. Grandma's Homemade Banana Bread  [ar_TCEBBd8w2zc3RYg2hymhLRXQXMEB9K6]  (3 steps, 9 ingredients)
Ask for "the 2nd one" to see its ingredients and instructions.

Active filters: search "banana bread" (titles only); excluded: walnut, pecan, almond, hazelnut, peanut, cashew, pistachio, macadamia, nut
  'nuts' was expanded to: walnut, pecan, almond, hazelnut, peanut, cashew, pistachio, macadamia, nut (an AI-proposed list; tell me if anything should be added or removed)
```

**Checks:**

- PASS: session keeps text=banana bread, exclude=['walnut', 'pecan', 'nut'] (session as expected)
- PASS: no result mentions an excluded ingredient (checked independently per recipe) (10 results, none mention ['walnut', 'pecan', 'almond', 'hazelnut', 'peanut', 'cashew', 'pistachio', 'macadamia', 'nut'])

_0.0 s_

## Turn 3

**User:** only ones with 5 steps or fewer

**Intent:** `{"action":"search","max_steps":5}`

**Bot:**

```
Found 74 recipes; showing 10 (best text match first):
1. Country Banana Bread  [ar_LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi]  (3 steps, 4 ingredients)
2. Banana Banana Bread  [ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC]  (3 steps, 7 ingredients)
3. Rich and Delicious Banana Bread  [ar_TJFqS5qmSUVcBw7c2Da99BzhmvnbgCm]  (3 steps, 6 ingredients)
4. Banana Bread French Toast  [ar_GiHk4/Wm95WTxwkxlmJtSmHUBdpv2La]  (2 steps, 6 ingredients)
5. The Best Banana Bread  [ar_pW/G7uT3a0khPJWk/AzOieElj4cz2ku]  (3 steps, 6 ingredients)
6. Healthier Banana Banana Bread  [ar_zPU0I27hBx09bNpfvQEjNTyHl/X7uwK]  (3 steps, 8 ingredients)
7. Janine's Best Banana Bread  [ar_r.uL.9n9ARPdY33iuX0JqWoLzor1ppa]  (3 steps, 7 ingredients)
8. Joy's Easy Banana Bread  [ar_1FDH/3jPeNVkGWMvwU857yJJCQL8qS6]  (3 steps, 7 ingredients)
9. Banana Bread  [fn_J9d89klHetj.4b5OKiASicRh8tfXK6m]  (2 steps, 10 ingredients)
10. Grandma's Homemade Banana Bread  [ar_TCEBBd8w2zc3RYg2hymhLRXQXMEB9K6]  (3 steps, 9 ingredients)
Ask for "the 2nd one" to see its ingredients and instructions.

Active filters: search "banana bread" (titles only); excluded: walnut, pecan, almond, hazelnut, peanut, cashew, pistachio, macadamia, nut; at most 5 steps
```

**Checks:**

- PASS: every result is within the step limit (all 10 have <= 5 steps)
- PASS: no result mentions an excluded ingredient (checked independently per recipe) (10 results, none mention ['walnut', 'pecan', 'almond', 'hazelnut', 'peanut', 'cashew', 'pistachio', 'macadamia', 'nut'])

_0.0 s_

## Turn 4

**User:** show me the second one

**Intent:** `{"action":"show_recipe","result_number":2}`

**Bot:**

```
Banana Banana Bread  [ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC]
Ingredients (as written in the source):
  - 2 cups all-purpose flour
  - 1 teaspoon baking soda
  - 1/4 teaspoon salt
  - 1/2 cup butter
  - 3/4 cup brown sugar
  - 2 eggs, beaten
  - 2 1/3 cups mashed overripe bananas
Instructions (3 steps):
  1. Preheat oven to 350 degrees F (175 degrees C). Lightly grease a 9x5 inch loaf pan.
  2. In a large bowl, combine flour, baking soda and salt. In a separate bowl, cream together butter and brown sugar. Stir in eggs and mashed bananas until well blended. Stir banana mixture into flour mixture; stir just to moisten. Pour batter into prepared loaf pan.
  3. Bake in preheated oven for 60 to 65 minutes, until a toothpick inserted into center of the loaf comes out clean. Let bread cool in pan for 10 minutes, then turn out onto a wire rack.
Nutrition and cooking times are not in the dataset.

Active filters: search "banana bread" (titles only); excluded: walnut, pecan, almond, hazelnut, peanut, cashew, pistachio, macadamia, nut; at most 5 steps
```

**Checks:**

- PASS: contains 'Ingredients (as written in the source):', 'Instructions' (reply contains ('Ingredients (as written in the source):', 'Instructions'))
- PASS: does not contain 'WARNING' (none present)

_0.0 s_

## Turn 5

**User:** now muffins instead

**Intent:** `{"action":"search","new_topic":true,"text":"muffins","title_only":true}`

**Bot:**

```
Found 459 recipes; showing 10 (best text match first):
1. Beer Muffins  [ar_z3GfUC20.AMCn7Kn4mcV7exkyld9oBq]  (3 steps, 4 ingredients)
2. Cheddar Jalapeno Corn Muffins  [fn_RtrI9orNWfb0SGvjQH9SuYD2m0M.9dK]  (1 step, 5 ingredients)
3. Wine Cooler Muffins  [ar_a7HbMsG3B7hNwXwL/QDGiJBOEBOv9ju]  (3 steps, 3 ingredients)
4. Grilled Corn Muffins with Blueberry-Honey Butter  [fn_8d8mPfXKqqKcF8K4ndgH9GvIZXtwMly]  (2 steps, 4 ingredients)
5. Healthy Egg Muffins  [ar_om3Ljs/nGX.Z.oyNff.LidcDIYyW16O]  (3 steps, 4 ingredients)
6. Cheddar Muffins  [ar_/1x23KIsjT505STzzYC.zskL0n/2ktO]  (2 steps, 9 ingredients)
7. Garlic Butter English Muffins  [fn_M4v8K5K3vopJR9ZuKE1l9JTKZIPsIeC]  (2 steps, 4 ingredients)
8. Easiest Muffins  [fn_pxoSSIRlRlAjvAneHIryEio7TD7RIpG]  (3 steps, 4 ingredients)
9. Blueberry Muffins I  [ar_u0vtrtoQIlTN6SN3J7biPanY9dGDVNm]  (3 steps, 7 ingredients)
10. Blueberry Muffins  [fn_61dNLEGlIGO7ESk.iu2kEA0GDCEn0gy]  (1 step, 8 ingredients)
Ask for "the 2nd one" to see its ingredients and instructions.

Active filters: search "muffins" (titles only); excluded: walnut, pecan, almond, hazelnut, peanut, cashew, pistachio, macadamia, nut; at most 5 steps
```

**Checks:**

- PASS: session keeps text=muffins, max_steps=5, exclude=['walnut', 'nut'] (session as expected)
- PASS: no result mentions an excluded ingredient (checked independently per recipe) (10 results, none mention ['walnut', 'pecan', 'almond', 'hazelnut', 'peanut', 'cashew', 'pistachio', 'macadamia', 'nut'])
- PASS: every result is within the step limit (all 10 have <= 5 steps)
- PASS: contains 'excluded: walnut' (reply contains ('excluded: walnut',))

_0.1 s_
