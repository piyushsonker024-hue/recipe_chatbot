# ingredient_matching

Covers: Task 2: ranked existing recipes, matched/missing, quantities, constraints added later

Mode: scripted intents

## Turn 1

**User:** I have 2 lb chicken breast, 1 onion, 3 cloves garlic, rice and a can of coconut milk. What can I make?

**Intent:** `{"action":"match","new_topic":true,"add_have":["2 lb chicken breast","1 onion","3 cloves garlic","rice","1 can coconut milk"]}`

**Bot:**

```
Ranked 52,503 existing recipes that use at least one of your ingredients (of 124,483 that pass your constraints). Top 5:
1. Polynesian Chicken Fafa  [ar_DDw35W2pVXX.SHfRr8Jwo8LyW1Bn/aW]  (2 steps; score 0.72)
   you have 5 of 8 ingredients:
     - onion  <- your '1 onion' [exact]; quantity not verified (you have 1, recipe needs 1/4 cup; different kinds of measure)
     - garlic  <- your '3 cloves garlic' [exact]; enough: you have 3 cloves, recipe needs 2 cloves
     - coconut milk  <- your '1 can coconut milk' [exact]; quantity not verified (you have 1 can, recipe needs 1 cup; different kinds of measure)
     - long grain white rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
     - chicken breast half  <- your '2 lb chicken breast' [variant]; enough: you have 2 lb (907 g), recipe needs 1 pound (454 g)
   missing: butter, spinach, coconut
   assumed pantry staples: water
   why this rank: coverage 5/8 = 0.62, usage 5/5 = 1.00; (0.62 + 1.00) / 2 - 0.03 x 3 missing = 0.72
2. Coconut Rice  [ar_jNyE1ozCv8t0/5zEfrYyfHwQDcpvhL6]  (2 steps; score 0.70)
   you have 2 of 2 ingredients:
     - basmati rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
     - coconut milk  <- your '1 can coconut milk' [exact]; quantity not verified (you have 1 can, recipe needs 4 (10 ounce) cans; different kinds of measure)
   missing: nothing
   assumed pantry staples: salt
   not used from your list: 2 lb chicken breast, 1 onion, 3 cloves garlic
   why this rank: coverage 2/2 = 1.00, usage 2/5 = 0.40; (1.00 + 0.40) / 2 - 0.03 x 0 missing = 0.70
3. Coconut Rice  [fn_liymsCcQPvtAY.YUjLZuu1VRZLqdgqe]  (2 steps; score 0.70)
   you have 2 of 2 ingredients:
     - jasmine rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
     - unsweetened coconut milk  <- your '1 can coconut milk' [variant]; quantity not verified (you have 1 can, recipe needs 1 cup; different kinds of measure)
   missing: nothing
   assumed pantry staples: water, salt
   not used from your list: 2 lb chicken breast, 1 onion, 3 cloves garlic
   why this rank: coverage 2/2 = 1.00, usage 2/5 = 0.40; (1.00 + 0.40) / 2 - 0.03 x 0 missing = 0.70
4. Stewed Chicken  [fn_zI.U2fPow39uYuNIDtOwk/UpouMb5/S]  (2 steps; score 0.66)
   you have 5 of 9 ingredients:
     - chicken  <- your '2 lb chicken breast' [variant]; not enough: you have 2 lb (907 g), recipe needs 1 (4 pound) chicken (1814 g)
     - garlic  <- your '3 cloves garlic' [exact]; not enough: you have 3 cloves, recipe needs 2 cloves + 2 cloves
     - yellow onion  <- your '1 onion' [variant]; quantity not verified (recipe amount missing or unclear)
     - coconut milk  <- your '1 can coconut milk' [exact]; quantity not verified (recipe amount missing or unclear)
     - white rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
   missing: dried thyme, oil, flour, dried red bean
   assumed pantry staples: salt, black pepper
   why this rank: coverage 5/9 = 0.56, usage 5/5 = 1.00; (0.56 + 1.00) / 2 - 0.03 x 4 missing = 0.66
5. Escarole Soup with Rice  [fn_Nlw6HVRbDCxPAw7iYCoXYdSB9UU4YZi]  (1 step; score 0.60)
   you have 4 of 7 ingredients:
     - garlic  <- your '3 cloves garlic' [exact]; not enough: you have 3 cloves, recipe needs 3 or 4 cloves
     - onion  <- your '1 onion' [exact]; quantity not verified (you have 1, recipe needs 1/2 cup; different kinds of measure)
     - chicken  <- your '2 lb chicken breast' [variant]; quantity not verified (you have 2 lb, recipe needs 6 cups; different kinds of measure)
     - short-grain white rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
   missing: olive oil, escarole, parmesan cheese
   assumed pantry staples: salt, black pepper
   not used from your list: 1 can coconut milk
   why this rank: coverage 4/7 = 0.57, usage 4/5 = 0.80; (0.57 + 0.80) / 2 - 0.03 x 3 missing = 0.60
Scoring: score = (coverage + usage) / 2 - 0.03 x missing, where coverage = share of the recipe's ingredients you have and usage = share of your ingredients it uses; pantry staples (salt, black pepper, water) are assumed unless you say otherwise; ties: fewer missing, fewer steps, title.
Note: 'variant' means your ingredient matched a more specific name in the recipe (e.g. sugar -> brown sugar); check that what you have works.
Note: Where quantities say 'not verified', only the ingredient name was matched; whether you have enough was not checked.

Active filters: your ingredients: 2 lb chicken breast, 1 onion, 3 cloves garlic, rice, 1 can coconut milk
```

**Checks:**

- PASS: every cited recipe ID exists in the dataset (5 IDs, all exist)
- PASS: contains 'coverage', 'missing', 'score =' (reply contains ('coverage', 'missing', 'score ='))
- PASS: contains 'not verified' (reply contains ('not verified',))

_1.2 s_

## Turn 2

**User:** no dairy please, and at most 4 steps

**Intent:** `{"action":"match","exclusion_expansions":[{"category":"dairy","terms":["milk","butter","cheese","cream","yogurt","cream cheese","sour cream","buttermilk"]}],"max_steps":4}`

**Bot:**

```
Ranked 16,932 existing recipes that use at least one of your ingredients (of 37,076 that pass your constraints). Top 5:
1. Basmati and Black Rice Juk  [fn_NwCjtdYTs80sTo6nPij.LmWs/TdcL/q]  (3 steps; score 0.55)
   you have 3 of 4 ingredients:
     - thai black rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
     - roasted garlic  <- your '3 cloves garlic' [variant]; not enough: you have 3 cloves, recipe needs 4 to 6 cloves
     - basmati rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
   missing: horseradish
   assumed pantry staples: water, salt, black pepper
   not used from your list: 2 lb chicken breast, 1 onion, 1 can coconut milk
   why this rank: coverage 3/4 = 0.75, usage 2/5 = 0.40; (0.75 + 0.40) / 2 - 0.03 x 1 missing = 0.55
2. Chicken Bogg  [ar_PRzcNAgb5XxCnsMPcvoWxjjA2zJWV1i]  (1 step; score 0.54)
   you have 3 of 5 ingredients:
     - chicken breast half  <- your '2 lb chicken breast' [variant]; enough: you have 2 lb (907 g), recipe needs 2 pounds (907 g)
     - onion  <- your '1 onion' [exact]; not enough: you have 1, recipe needs 2
     - instant white rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
   missing: smoked beef sausage, pork sausage
   assumed pantry staples: salt, black pepper
   not used from your list: 3 cloves garlic, 1 can coconut milk
   why this rank: coverage 3/5 = 0.60, usage 3/5 = 0.60; (0.60 + 0.60) / 2 - 0.03 x 2 missing = 0.54
3. Slow Cooker Red Beans and Rice  [fn_JWtTVzlPXsV.8yvodsPH.yxH32UmMGG]  (1 step; score 0.54)
   you have 3 of 5 ingredients:
     - onion  <- your '1 onion' [exact]; quantity not verified (you have 1, recipe needs 1/2 cup; different kinds of measure)
     - garlic  <- your '3 cloves garlic' [exact]; enough: you have 3 cloves, recipe needs 2 cloves
     - hot rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
   missing: smoked creole seasoned sausage, dried red bean
   assumed pantry staples: water, salt, black pepper
   not used from your list: 2 lb chicken breast, 1 can coconut milk
   why this rank: coverage 3/5 = 0.60, usage 3/5 = 0.60; (0.60 + 0.60) / 2 - 0.03 x 2 missing = 0.54
4. Brazilian White Rice  [ar_3yCyrnI87/N1pnlB4E68qFd30ufEXZm]  (2 steps; score 0.54)
   you have 3 of 5 ingredients:
     - long-grain white rice  <- your 'rice' [variant]; quantity not verified (you gave no amount)
     - onion  <- your '1 onion' [exact]; quantity not verified (you have 1, recipe needs 2 tablespoons; different kinds of measure)
     - garlic  <- your '3 cloves garlic' [exact]; enough: you have 3 cloves, recipe needs 2 cloves
   missing: vegetable oil, hot water
   assumed pantry staples: salt
   not used from your list: 2 lb chicken breast, 1 can coconut milk
   why this rank: coverage 3/5 = 0.60, usage 3/5 = 0.60; (0.60 + 0.60) / 2 - 0.03 x 2 missing = 0.54
5. Roast Chicken  [fn_ev.qCC2R0faHIsfQ4rBb4ADnrvDrnKS]  (2 steps; score 0.54)
   you have 3 of 5 ingredients:
     - chicken  <- your '2 lb chicken breast' [variant]; not enough: you have 2 lb (907 g), recipe needs 6 to 7 pound (3175 g)
     - onion  <- your '1 onion' [exact]; enough: you have 1, recipe needs 1
     - garlic  <- your '3 cloves garlic' [exact]; enough: you have 3 cloves, recipe needs 2 cloves
   missing: roasted chicken juice, chicken stock
   assumed pantry staples: salt, black pepper
   not used from your list: rice, 1 can coconut milk
   why this rank: coverage 3/5 = 0.60, usage 3/5 = 0.60; (0.60 + 0.60) / 2 - 0.03 x 2 missing = 0.54
Scoring: score = (coverage + usage) / 2 - 0.03 x missing, where coverage = share of the recipe's ingredients you have and usage = share of your ingredients it uses; pantry staples (salt, black pepper, water) are assumed unless you say otherwise; ties: fewer missing, fewer steps, title.
Note: 'variant' means your ingredient matched a more specific name in the recipe (e.g. sugar -> brown sugar); check that what you have works.
Note: Where quantities say 'not verified', only the ingredient name was matched; whether you have enough was not checked.
Warning: your '1 can coconut milk' contains the excluded word(s) milk, so recipes using it are excluded too. Tell me if that exclusion should not apply to it.

Active filters: excluded: milk, butter, cheese, cream, yogurt, cream cheese, sour cream, buttermilk; at most 4 steps; your ingredients: 2 lb chicken breast, 1 onion, 3 cloves garlic, rice, 1 can coconut milk
  'dairy' was expanded to: milk, butter, cheese, cream, yogurt, cream cheese, sour cream, buttermilk (an AI-proposed list; tell me if anything should be added or removed)
```

**Checks:**

- PASS: no result mentions an excluded ingredient (checked independently per recipe) (5 results, none mention ['milk', 'butter', 'cheese', 'cream', 'yogurt', 'cream cheese', 'sour cream', 'buttermilk'])
- PASS: every result is within the step limit (all 5 have <= 4 steps)
- PASS: session keeps have=['2 lb chicken breast', 'rice'] (session as expected)

_0.6 s_
