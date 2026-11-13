# substitution_respects_exclusion

Covers: Task 3: best-evidence substitute is excluded by the user, so the next one is used

Mode: scripted intents

## Turn 1

**User:** show me recipe ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC

**Intent:** `{"action":"show_recipe","recipe_id":"ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC"}`

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

Active filters: no filters
```

**Checks:**

- PASS: contains 'Banana Banana Bread' (reply contains ('Banana Banana Bread',))

_0.0 s_

## Turn 2

**User:** no margarine in anything please

**Intent:** `{"action":"search","add_exclude":["margarine"]}`

**Bot:**

```
Found 121,850 recipes; showing 10 (fewest steps first):
1. "Almost Famous" Strawberry Lemonade  [fn_rv7nUfSjvxezpTG2sPYBIv9iLBw5aaq]  (1 step, no ingredient list)
2. "Be Mine" Brownie  [fn_JzoOTR5GIw6FS0eD2Hp7Cevno032jVO]  (1 step, 8 ingredients)
3. "Caribou" Stew  [fn_sgGiXPV.DB/jWlNguRPbEd8PohdU5FS]  (1 step, 16 ingredients)
4. "Cowboy" Stew  [fn_S0FoAgfWe.13vYsKM3mBEfurLX5EDmm]  (1 step, 14 ingredients)
5. "Cuisinart" Yellow Tomato Gazpacho  [fn_iuRjpdotzqlPQvKLs.In51Irft.0yZe]  (1 step, 10 ingredients)
6. "Cuisinart" Yellow Tomato Gazpacho  [fn_GcJVLhIZbzeOD/2wqWsfoRhOgoqy1rq]  (1 step, 10 ingredients)
7. "Cup of Happiness" Classic Lemonade  [fn_zUJW.goTUvwV3P4JncgnscD.6xdeM4C]  (1 step, no ingredient list)
8. "Deconstructed" Italian Cheesecake  [fn_bflLDgBj4zPPappptgCif.Kr78zTOnm]  (1 step, 4 ingredients)
9. "Eat Your Vegetables!": Green Bean Salad with Red Onion and Tomato  [fn_ghWgYCtvc7wKgeE8wyEvJKbLpeO6vpe]  (1 step, 8 ingredients)
10. "Egg Not" (Eggless Eggnog)  [ar_Zf39JPX8cHwKW.AassinMKTl30Wd1Cq]  (1 step, 7 ingredients)
Ask for "the 2nd one" to see its ingredients and instructions.

Active filters: excluded: margarine
```

**Checks:**

- PASS: session keeps exclude=['margarine'] (session as expected)

_0.2 s_

## Turn 3

**User:** what can I use instead of butter in it?

**Intent:** `{"action":"substitute","recipe_id":"ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC","sub_target":"butter"}`

**Bot:**

```
Substituting butter in Banana Banana Bread  [ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC]
This recipe uses: 1/2 cup butter
Compared against 191 recipes of the same dish.
Dataset evidence (verified: these recipes exist and say this):
1. margarine: STRONG evidence
   - [stated in this dish] 2 recipes of this dish list it as an alternative: ar_hxIyxv/BIP1BaT9Tbw1QIGHR.R9GmaG, fn_OMRS5x7e72E/cpE2/g2OwnZWGm..Wl2
   - [stated in other dishes] 457 recipes of other dishes list it as an alternative: ar_.ADuDeVzWFpwfgUUNhAp79aEIPgMeJm, ar_.MdxcWpCbtYt5TMO9xbvirCn2oz.tDu, ar_.QMqx4KZavqnQI170ZrUgxkxHl..UKS, ar_.c5hf9iiF7DGfLSW4kxi.L0SGoTiuDC, ar_/3NnLuMotNHbvZDqNdNYKfr7WVaBQMS
   - [near-identical recipes] 2 near-identical recipes of this dish use it and do not use the target: ar_pW/G7uT3a0khPJWk/AzOieElj4cz2ku, ar_1SOVtYR.EsXlA6DdlIF8jYika3BGaZu
   - used together with butter in 77 recipes (8% of the rarer one's recipes)
   - BREAKS your exclusion: margarine
2. olive oil: MODERATE evidence
   - [stated in other dishes] 85 recipes of other dishes list it as an alternative: ar_04dw8aV7qcj.0YWHjNZfA5Ag6/JhFIi, ar_9krsTjPloFErugozlYeTE2/xo4uPEvq, ar_cHxQ63eiZYXjcXD.jLL9UsAlnRh2tm6, ar_fX2MRtBMuIRMpCyFDkT5ihRMaPEQlQq, ar_hi7ZHw2McXxWA1xIRJX82n7.RjyGsOi
   - used together with butter in 5,767 recipes (18% of the rarer one's recipes)
   - note: indirect: the stated alternative comes from other dishes, not this one
3. vegetable oil: MODERATE evidence
   - [stated in this dish] 1 recipe of this dish lists it as an alternative: fn_XM5oN9mScJzsQeWWJWjt79EPaUpY7Oa
   - [stated in other dishes] 34 recipes of other dishes list it as an alternative: ar_AQoeOlshZt4qsaMX.nfK.586MdemyOy, epi_4TV97hfDhL1WCEvPs5GFu657FONjqiu, epi_8tOhezA2EHmBqAz2gnXeRq/S/AJ/ssu, epi_Vc2AtNHGKIsecLfKnTJRD77d8Fe6Rtu, epi_XdnNnC0kf.oF.y1luyA/Vbb6Tzpin.6
   - used together with butter in 2,360 recipes (20% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 2,360 recipes (20% of the rarer one's recipes), which suggests a complement rather than a replacement
4. oil: MODERATE evidence
   - [stated in other dishes] 34 recipes of other dishes list it as an alternative: ar_QIPzg5WkoWsYOtE2uQTKFuiVMZtDsje, ar_QLcEao/IE9L1eA9fkR/skbaV8zSejnK, epi_3TD/oyiSWgZi6EANk3S1ijarbx9ZrZi, epi_HGOX77Ktvt8lQJ3zFGVvHXK1vI.DcAm, epi_gDcEyk2W.YzmuYeeUho9rvHnAjTRBqa
   - used together with butter in 268 recipes (24% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 268 recipes (24% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
5. nonstick cooking spray: MODERATE evidence
   - [stated in other dishes] 20 recipes of other dishes list it as an alternative: epi_EVwgu4PM.b.bQ5IuHXaBUVP4YwwycCy, epi_VMdrs/x0dDDm3HX.tNX1Rd0FZkc6caK, fn_2GYJBr1TGd5MD3ltvJg6jNkEAwKod5C, fn_2a6LpxmDGCDsMFMLMIYJ08IaWrbqZpC, fn_4gRkhuPmD9hGfwqihvADkLuSWKYOw5q
   - used together with butter in 354 recipes (44% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 354 recipes (44% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
Updated recipe with olive oil instead of butter (PREDICTION: not tested; picked because it has the strongest dataset evidence):
  Ingredients:
    - 2 cups all-purpose flour
    - 1 teaspoon baking soda
    - 1/4 teaspoon salt
    - 1/2 cup olive oil   [changed; was '1/2 cup butter'; same amount assumed]
    - 3/4 cup brown sugar
    - 2 eggs, beaten
    - 2 1/3 cups mashed overripe bananas
  Instructions:
    1. Preheat oven to 350 degrees F (175 degrees C). Lightly grease a 9x5 inch loaf pan.
    2. In a large bowl, combine flour, baking soda and salt. In a separate bowl, cream together olive oil and brown sugar. Stir in eggs and mashed bananas until well blended. Stir banana mixture into flour mixture; stir just to moisten. Pour batter into prepared loaf pan.   [changed]
       REVIEW: this step uses 'cream', written for butter; olive oil may not behave the same way
    3. Bake in preheated oven for 60 to 65 minutes, until a toothpick inserted into center of the loaf comes out clean. Let bread cool in pan for 10 minutes, then turn out onto a wire rack.
  Verified: the dataset has recipes that use olive oil where others use butter (IDs above).
  Predicted, not verified: that this recipe works with olive oil at the same amount; texture, taste and cooking time may change.
Safety: Recipe text alone cannot show that a substitution is safe for an allergy or a medical diet. Check product labels, and ask a professional if it matters.
External sources: not used. Say "search the web" to see outside sources (shown separately, with links).

Active filters: excluded: margarine
```

**Checks:**

- PASS: contains 'margarine: STRONG evidence', 'BREAKS your exclusion: margarine', 'Updated recipe with olive oil', 'REVIEW:' (reply contains ('margarine: STRONG evidence', 'BREAKS your exclusion: margarine', 'Updated recipe with olive oil', 'REVIEW:'))
- PASS: does not contain 'Updated recipe with margarine' (none present)

_1.2 s_

## Turn 4

**User:** what about margarine anyway?

**Intent:** `{"action":"substitute","recipe_id":"ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC","sub_target":"butter","sub_candidate":"margarine"}`

**Bot:**

```
Substituting butter in Banana Banana Bread  [ar_kq.naD.8G19M4UU9dVvJgHtpfo.l/eC]
This recipe uses: 1/2 cup butter
Compared against 191 recipes of the same dish.
Dataset evidence (verified: these recipes exist and say this):
1. margarine: STRONG evidence
   - [stated in this dish] 2 recipes of this dish list it as an alternative: ar_hxIyxv/BIP1BaT9Tbw1QIGHR.R9GmaG, fn_OMRS5x7e72E/cpE2/g2OwnZWGm..Wl2
   - [stated in other dishes] 457 recipes of other dishes list it as an alternative: ar_.ADuDeVzWFpwfgUUNhAp79aEIPgMeJm, ar_.MdxcWpCbtYt5TMO9xbvirCn2oz.tDu, ar_.QMqx4KZavqnQI170ZrUgxkxHl..UKS, ar_.c5hf9iiF7DGfLSW4kxi.L0SGoTiuDC, ar_/3NnLuMotNHbvZDqNdNYKfr7WVaBQMS
   - [near-identical recipes] 2 near-identical recipes of this dish use it and do not use the target: ar_pW/G7uT3a0khPJWk/AzOieElj4cz2ku, ar_1SOVtYR.EsXlA6DdlIF8jYika3BGaZu
   - used together with butter in 77 recipes (8% of the rarer one's recipes)
   - BREAKS your exclusion: margarine
2. olive oil: MODERATE evidence
   - [stated in other dishes] 85 recipes of other dishes list it as an alternative: ar_04dw8aV7qcj.0YWHjNZfA5Ag6/JhFIi, ar_9krsTjPloFErugozlYeTE2/xo4uPEvq, ar_cHxQ63eiZYXjcXD.jLL9UsAlnRh2tm6, ar_fX2MRtBMuIRMpCyFDkT5ihRMaPEQlQq, ar_hi7ZHw2McXxWA1xIRJX82n7.RjyGsOi
   - used together with butter in 5,767 recipes (18% of the rarer one's recipes)
   - note: indirect: the stated alternative comes from other dishes, not this one
3. vegetable oil: MODERATE evidence
   - [stated in this dish] 1 recipe of this dish lists it as an alternative: fn_XM5oN9mScJzsQeWWJWjt79EPaUpY7Oa
   - [stated in other dishes] 34 recipes of other dishes list it as an alternative: ar_AQoeOlshZt4qsaMX.nfK.586MdemyOy, epi_4TV97hfDhL1WCEvPs5GFu657FONjqiu, epi_8tOhezA2EHmBqAz2gnXeRq/S/AJ/ssu, epi_Vc2AtNHGKIsecLfKnTJRD77d8Fe6Rtu, epi_XdnNnC0kf.oF.y1luyA/Vbb6Tzpin.6
   - used together with butter in 2,360 recipes (20% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 2,360 recipes (20% of the rarer one's recipes), which suggests a complement rather than a replacement
4. oil: MODERATE evidence
   - [stated in other dishes] 34 recipes of other dishes list it as an alternative: ar_QIPzg5WkoWsYOtE2uQTKFuiVMZtDsje, ar_QLcEao/IE9L1eA9fkR/skbaV8zSejnK, epi_3TD/oyiSWgZi6EANk3S1ijarbx9ZrZi, epi_HGOX77Ktvt8lQJ3zFGVvHXK1vI.DcAm, epi_gDcEyk2W.YzmuYeeUho9rvHnAjTRBqa
   - used together with butter in 268 recipes (24% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 268 recipes (24% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
5. nonstick cooking spray: MODERATE evidence
   - [stated in other dishes] 20 recipes of other dishes list it as an alternative: epi_EVwgu4PM.b.bQ5IuHXaBUVP4YwwycCy, epi_VMdrs/x0dDDm3HX.tNX1Rd0FZkc6caK, fn_2GYJBr1TGd5MD3ltvJg6jNkEAwKod5C, fn_2a6LpxmDGCDsMFMLMIYJ08IaWrbqZpC, fn_4gRkhuPmD9hGfwqihvADkLuSWKYOw5q
   - used together with butter in 354 recipes (44% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 354 recipes (44% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
Updated recipe with margarine instead of butter (PREDICTION: not tested; picked because you chose it):
  Ingredients:
    - 2 cups all-purpose flour
    - 1 teaspoon baking soda
    - 1/4 teaspoon salt
    - 1/2 cup margarine   [changed; was '1/2 cup butter'; same amount assumed]
    - 3/4 cup brown sugar
    - 2 eggs, beaten
    - 2 1/3 cups mashed overripe bananas
  Instructions:
    1. Preheat oven to 350 degrees F (175 degrees C). Lightly grease a 9x5 inch loaf pan.
    2. In a large bowl, combine flour, baking soda and salt. In a separate bowl, cream together margarine and brown sugar. Stir in eggs and mashed bananas until well blended. Stir banana mixture into flour mixture; stir just to moisten. Pour batter into prepared loaf pan.   [changed]
       REVIEW: this step uses 'cream', written for butter; margarine may not behave the same way
    3. Bake in preheated oven for 60 to 65 minutes, until a toothpick inserted into center of the loaf comes out clean. Let bread cool in pan for 10 minutes, then turn out onto a wire rack.
  Verified: the dataset has recipes that use margarine where others use butter (IDs above).
  Predicted, not verified: that this recipe works with margarine at the same amount; texture, taste and cooking time may change.
  WARNING: margarine breaks your exclusion (margarine).
Safety: Recipe text alone cannot show that a substitution is safe for an allergy or a medical diet. Check product labels, and ask a professional if it matters.
External sources: not used. Say "search the web" to see outside sources (shown separately, with links).

Active filters: excluded: margarine
```

**Checks:**

- PASS: contains 'WARNING: margarine breaks your exclusion' (reply contains ('WARNING: margarine breaks your exclusion',))

_1.2 s_
