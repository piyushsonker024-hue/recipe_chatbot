# known_same_dish_by_title_words

Covers: KNOWN FAILURE: same-dish evidence relies on title words, so a uniquely named dish has none

Mode: scripted intents

## Turn 1

**User:** what can I use instead of butter in Chicken Valdostano?

**Intent:** `{"action":"substitute","recipe_id":"ar_BnEOdvcvT7mEOpAkTGYs.dv17W33eCG","sub_target":"butter"}`

**Bot:**

```
Substituting butter in Chicken Valdostano  [ar_BnEOdvcvT7mEOpAkTGYs.dv17W33eCG]
This recipe uses: 1/4 cup unsalted butter
Compared against 0 recipes of the same dish.
Dataset evidence (verified: these recipes exist and say this):
1. margarine: MODERATE evidence
   - [stated in other dishes] 459 recipes of other dishes list it as an alternative: ar_.ADuDeVzWFpwfgUUNhAp79aEIPgMeJm, ar_.MdxcWpCbtYt5TMO9xbvirCn2oz.tDu, ar_.QMqx4KZavqnQI170ZrUgxkxHl..UKS, ar_.c5hf9iiF7DGfLSW4kxi.L0SGoTiuDC, ar_/3NnLuMotNHbvZDqNdNYKfr7WVaBQMS
   - used together with butter in 77 recipes (8% of the rarer one's recipes)
   - note: indirect: the stated alternative comes from other dishes, not this one
2. olive oil: MODERATE evidence
   - [stated in other dishes] 85 recipes of other dishes list it as an alternative: ar_04dw8aV7qcj.0YWHjNZfA5Ag6/JhFIi, ar_9krsTjPloFErugozlYeTE2/xo4uPEvq, ar_cHxQ63eiZYXjcXD.jLL9UsAlnRh2tm6, ar_fX2MRtBMuIRMpCyFDkT5ihRMaPEQlQq, ar_hi7ZHw2McXxWA1xIRJX82n7.RjyGsOi
   - used together with butter in 5,767 recipes (18% of the rarer one's recipes)
   - note: indirect: the stated alternative comes from other dishes, not this one
3. vegetable oil: MODERATE evidence
   - [stated in other dishes] 35 recipes of other dishes list it as an alternative: ar_AQoeOlshZt4qsaMX.nfK.586MdemyOy, epi_4TV97hfDhL1WCEvPs5GFu657FONjqiu, epi_8tOhezA2EHmBqAz2gnXeRq/S/AJ/ssu, epi_Vc2AtNHGKIsecLfKnTJRD77d8Fe6Rtu, epi_XdnNnC0kf.oF.y1luyA/Vbb6Tzpin.6
   - used together with butter in 2,360 recipes (20% of the rarer one's recipes)
   - note: conflicting: also used together with the target in 2,360 recipes (20% of the rarer one's recipes), which suggests a complement rather than a replacement
   - note: indirect: the stated alternative comes from other dishes, not this one
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
Updated recipe with margarine instead of butter (PREDICTION: not tested; picked because it has the strongest dataset evidence):
  Ingredients:
    - 2 tablespoons all-purpose flour
    - 6 skinless, boneless chicken breast halves - pounded thin
    - 1/4 cup unsalted margarine   [changed; was '1/4 cup unsalted butter'; same amount assumed]
    - 10 fresh mushrooms, sliced
    - 3/4 cup dry white wine
    - 3/4 cup chicken stock
    - 3 tablespoons chopped fresh parsley
    - 1 teaspoon freshly ground white pepper
    - 6 slices thinly sliced prosciutto
    - 6 slices fontina cheese
  Instructions:
    1. Lightly flour chicken breasts, shaking off excess flour. In a large skillet over low heat, melt margarine/margarine. Add chicken and saute until lightly browned, about 2 minutes each side. Remove with slotted spatula and set aside.   [changed]
       REVIEW: this step uses 'browned, melt, set', written for butter; margarine may not behave the same way
    2. Increase heat to medium low. Add mushrooms and saute until juices are rendered, about 4 minutes. Add wine and simmer until reduced by 1/4, about 3 to 4 minutes. Increase heat to medium high. Add stock, parsley and pepper and simmer until sauce reduced to 1 cup, about 10 minutes.
    3. Reduce heat to low. Top each chicken breast with a slice of prosciutto and a slice of fontina cheese. Return chicken to skillet and cook just until cheese melts. Transfer chicken to individual plates and top each with some of the mushroom sauce before serving.
  Verified: the dataset has recipes that use margarine where others use butter (IDs above).
  Predicted, not verified: that this recipe works with margarine at the same amount; texture, taste and cooking time may change.
Safety: Recipe text alone cannot show that a substitution is safe for an allergy or a medical diet. Check product labels, and ask a professional if it matters.
External sources: not used. Say "search the web" to see outside sources (shown separately, with links).

Active filters: no filters
```

**Checks:**

- PASS: contains 'indirect' (reply contains ('indirect',))
- FAIL: at least 5 recipes of the same dish are compared (0 same-dish recipes compared)

_1.2 s_
