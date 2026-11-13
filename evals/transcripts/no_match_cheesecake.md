# no_match_cheesecake

Covers: No match under three hard constraints (found and fixed by this eval: it used to fall back to any-word matches such as smoothies)

Mode: scripted intents

## Turn 1

**User:** vegan cheesecake with no dairy or eggs, 2 steps max

**Intent:** `{"action":"search","new_topic":true,"text":"vegan cheesecake","add_exclude":["egg"],"exclusion_expansions":[{"category":"dairy","terms":["milk","butter","cheese","cream","yogurt","cream cheese","sour cream","buttermilk"]}],"max_steps":2}`

**Bot:**

```
No recipe matches all of your constraints.
Relaxing any single constraint does not help either; try a different dish.

Active filters: search "vegan cheesecake"; excluded: milk, butter, cheese, cream, yogurt, cream cheese, sour cream, buttermilk, egg; at most 2 steps
  'dairy' was expanded to: milk, butter, cheese, cream, yogurt, cream cheese, sour cream, buttermilk (an AI-proposed list; tell me if anything should be added or removed)
```

**Checks:**

- PASS: results are 'cheesecake' recipes, or the reply says nothing matches (reported no match)
- PASS: no result mentions an excluded ingredient (checked independently per recipe) (reported no match)

_0.1 s_
