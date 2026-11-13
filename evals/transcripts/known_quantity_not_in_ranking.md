# known_quantity_not_in_ranking

Covers: KNOWN FAILURE: a recipe needing 4 eggs ranks level with one you can make with your 2

Mode: scripted intents

## Turn 1

**User:** I have flour, sugar, butter, 2 eggs and milk

**Intent:** `{"action":"match","new_topic":true,"add_have":["flour","sugar","butter","2 eggs","milk"]}`

**Bot:**

```
Ranked 74,735 existing recipes that use at least one of your ingredients (of 124,483 that pass your constraints). Top 5:
1. Butterscotch Pudding II  [ar_P0DWIxogWC8gmo1XGFra9MtOzYNkree]  (1 step; score 1.00)
   you have 5 of 5 ingredients:
     - brown sugar  <- your 'sugar' [variant]; quantity not verified (you gave no amount)
     - flour  <- your 'flour' [exact]; quantity not verified (you gave no amount)
     - whole milk  <- your 'milk' [variant]; quantity not verified (you gave no amount)
     - egg yolk  <- your '2 eggs' [variant]; enough: you have 2, recipe needs 2
     - butter  <- your 'butter' [exact]; quantity not verified (you gave no amount)
   missing: nothing
   why this rank: coverage 5/5 = 1.00, usage 5/5 = 1.00; (1.00 + 1.00) / 2 - 0.03 x 0 missing = 1.00
2. Dessert Crepes  [ar_QeKj1uJqGB68n1tRx36Q6z5rACdryzG]  (2 steps; score 1.00)
   you have 5 of 5 ingredients:
     - egg  <- your '2 eggs' [exact]; not enough: you have 2, recipe needs 4
     - milk  <- your 'milk' [exact]; quantity not verified (you gave no amount)
     - butter  <- your 'butter' [exact]; quantity not verified (you gave no amount)
     - flour  <- your 'flour' [exact]; quantity not verified (you gave no amount)
     - sugar  <- your 'sugar' [exact]; quantity not verified (you gave no amount)
   missing: nothing
   assumed pantry staples: salt
   why this rank: coverage 5/5 = 1.00, usage 5/5 = 1.00; (1.00 + 1.00) / 2 - 0.03 x 0 missing = 1.00
3. Easy Tea Cakes  [fn_dHKbcFwKAKL7R2mNtDgK0SZDDbJXa6u]  (2 steps; score 1.00)
   you have 5 of 5 ingredients:
     - butter  <- your 'butter' [exact]; quantity not verified (you gave no amount)
     - powdered sugar  <- your 'sugar' [variant]; quantity not verified (you gave no amount)
     - egg  <- your '2 eggs' [exact]; not enough: you have 2, recipe needs 4
     - sour milk  <- your 'milk' [variant]; quantity not verified (you gave no amount)
     - flour  <- your 'flour' [exact]; quantity not verified (you gave no amount)
   missing: nothing
   why this rank: coverage 5/5 = 1.00, usage 5/5 = 1.00; (1.00 + 1.00) / 2 - 0.03 x 0 missing = 1.00
4. French Crepes  [ar_jT9nSS7fy9zecsaw10uzEKKF4OESQZO]  (2 steps; score 1.00)
   you have 5 of 5 ingredients:
     - flour  <- your 'flour' [exact]; quantity not verified (you gave no amount)
     - sugar  <- your 'sugar' [exact]; quantity not verified (you gave no amount)
     - egg  <- your '2 eggs' [exact]; not enough: you have 2, recipe needs 3
     - milk  <- your 'milk' [exact]; quantity not verified (you gave no amount)
     - butter  <- your 'butter' [exact]; quantity not verified (you gave no amount)
   missing: nothing
   assumed pantry staples: salt
   why this rank: coverage 5/5 = 1.00, usage 5/5 = 1.00; (1.00 + 1.00) / 2 - 0.03 x 0 missing = 1.00
5. Sweet Crepes  [fn_X5BvsQDFbW87o8.54hN.09a9WibADLi]  (2 steps; score 1.00)
   you have 6 of 6 ingredients:
     - flour  <- your 'flour' [exact]; quantity not verified (you gave no amount)
     - sugar  <- your 'sugar' [exact]; quantity not verified (you gave no amount)
     - egg  <- your '2 eggs' [exact]; enough: you have 2, recipe needs 2
     - milk  <- your 'milk' [exact]; quantity not verified (you gave no amount)
     - butter  <- your 'butter' [exact]; quantity not verified (you gave no amount)
     - clarified butter  <- your 'butter' [variant]; quantity not verified (you gave no amount)
   missing: nothing
   assumed pantry staples: salt
   why this rank: coverage 6/6 = 1.00, usage 5/5 = 1.00; (1.00 + 1.00) / 2 - 0.03 x 0 missing = 1.00
Scoring: score = (coverage + usage) / 2 - 0.03 x missing, where coverage = share of the recipe's ingredients you have and usage = share of your ingredients it uses; pantry staples (salt, black pepper, water) are assumed unless you say otherwise; ties: fewer missing, fewer steps, title.
Note: 'variant' means your ingredient matched a more specific name in the recipe (e.g. sugar -> brown sugar); check that what you have works.
Note: Where quantities say 'not verified', only the ingredient name was matched; whether you have enough was not checked.

Active filters: your ingredients: flour, sugar, butter, 2 eggs, milk
```

**Checks:**

- PASS: contains 'not enough: you have 2, recipe needs 4' (reply contains ('not enough: you have 2, recipe needs 4',))
- FAIL: results with a quantity shortfall rank below results without one (results with a shortfall at ranks [2, 3, 4], without at [1, 5])

_1.2 s_
