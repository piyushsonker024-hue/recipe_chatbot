# no_match_with_marked_alternatives

Covers: Hard constraint makes the result empty; alternatives are labeled as violating it

Mode: scripted intents

## Turn 1

**User:** Lobster bisque, but I'm allergic to shellfish

**Intent:** `{"action":"search","new_topic":true,"text":"lobster bisque","title_only":true,"exclusion_expansions":[{"category":"shellfish","terms":["shrimp","prawn","crab","lobster","scallop","clam","mussel","oyster","crawfish"]}]}`

**Bot:**

```
No recipe matches all of your constraints.
Alternatives that break one constraint (not applied unless you say so):
  - VIOLATES your constraint (allows lobster): 14 recipes, e.g. Lobster Bisque [ar_.UOj9zwBTGaJiP9l9.1O2yy.6TEkb/y]; Special Lobster Bisque [ar_q2gZmSQt3IKtyQniBvQaB8JwM.cjhbG]; Lobster Bisque II [ar_P4m5AVqnH05hQTLO9m2/1dRWTBPtmZ2]

Active filters: search "lobster bisque" (titles only); excluded: shrimp, prawn, crab, lobster, scallop, clam, mussel, oyster, crawfish
  'shellfish' was expanded to: shrimp, prawn, crab, lobster, scallop, clam, mussel, oyster, crawfish (an AI-proposed list; tell me if anything should be added or removed)
```

**Checks:**

- PASS: contains 'No recipe matches all of your constraints', 'VIOLATES your constraint' (reply contains ('No recipe matches all of your constraints', 'VIOLATES your constraint'))
- PASS: session keeps exclude=['lobster'] (session as expected)

_0.0 s_

## Turn 2

**User:** ok what about any bisque then

**Intent:** `{"action":"search","new_topic":true,"text":"bisque","title_only":true}`

**Bot:**

```
Found 59 recipes; showing 10 (best text match first):
1. Tomato Bisque I  [ar_aSO9j62MRnWr6bvJCJdyvElPmt14QPC]  (1 step, 3 ingredients)
2. Butternut Squash Bisque with Vermont Maple Syrup  [fn_LaQUFX4Bt5umxtELoPHeBeWIsw4CL0a]  (1 step, 6 ingredients)
3. Banana Bisque  [fn_4o60k47pX7LYAOEJpXb6N8/nAwQOvMu]  (2 steps, 7 ingredients)
4. Spiced Pumpkin and Sweet Potato Bisque  [fn_7cBI0P/wRCwcofxAMOQvC8AMmAxAJF2]  (1 step, 9 ingredients)
5. Tomato Bisque  [fn_oMWcvCDOeQOIGNR/FrDr77Jc35puvZq]  (1 step, 9 ingredients)
6. Pumpkin Ravioli Bisque  [ar_6SghvmEHRIBQGIBa8Erxmk/2O0rF.ym]  (2 steps, 8 ingredients)
7. Pumpkin Bisque (Dairy Free)  [ar_W468QR/pKsyQ.xnqnyjToQ03yNw5pa2]  (2 steps, 10 ingredients)
8. Chilled Golden Tomato Bisque  [epi_7SQGI1mmvpRmqQjDHnWuRHQ.h75blVm]  (4 steps, 7 ingredients)
9. Butternut Squash Bisque  [ar_3GDAX7n1US5D7uygk9G1/9mO3JYWoyC]  (3 steps, 10 ingredients)
10. Tomato Bisque II  [ar_ZGMB2XqatnSQQy2AoL/jE9D5qGZY2N.]  (2 steps, 10 ingredients)
Ask for "the 2nd one" to see its ingredients and instructions.

Active filters: search "bisque" (titles only); excluded: shrimp, prawn, crab, lobster, scallop, clam, mussel, oyster, crawfish
```

**Checks:**

- PASS: no result mentions an excluded ingredient (checked independently per recipe) (10 results, none mention ['shrimp', 'prawn', 'crab', 'lobster', 'scallop', 'clam', 'mussel', 'oyster', 'crawfish'])
- PASS: session keeps exclude=['lobster', 'shrimp'] (session as expected)

_0.0 s_
