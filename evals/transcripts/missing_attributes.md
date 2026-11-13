# missing_attributes

Covers: Nutrition and cooking time are not in the data: refuse, don't estimate

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

- PASS: contains 'Nutrition and cooking times are not in the dataset' (reply contains ('Nutrition and cooking times are not in the dataset',))

_0.0 s_

## Turn 2

**User:** How many calories per slice?

**Intent:** `{"action":"unsupported","missing_attribute":"calories"}`

**Bot:**

```
I can't answer that from the dataset: it has no calories. Each recipe only has a title, ingredient lines and instructions, and I won't guess values that aren't there. I can search by dish or ingredient, count steps, or compute ingredient statistics instead.

Active filters: no filters
```

**Checks:**

- PASS: contains "can't answer" (reply contains ("can't answer",))
- PASS: states no number for 'calories' (no invented value)
- PASS: states no number for 'kcal' (no invented value)

_0.0 s_

## Turn 3

**User:** What's the average cooking time of soups?

**Intent:** `{"action":"unsupported","missing_attribute":"cooking time"}`

**Bot:**

```
I can't answer that from the dataset: it has no cooking time. Each recipe only has a title, ingredient lines and instructions, and I won't guess values that aren't there. I can search by dish or ingredient, count steps, or compute ingredient statistics instead.

Active filters: no filters
```

**Checks:**

- PASS: contains "can't answer" (reply contains ("can't answer",))
- PASS: states no number for 'minutes' (no invented value)

_0.0 s_
