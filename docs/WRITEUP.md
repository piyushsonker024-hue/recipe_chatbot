# Recipe Chatbot: Design Write-up

A conversational assistant over the Recipe Box dataset (124,483 usable recipes from
Allrecipes, Epicurious and Food Network). It searches recipes, computes statistics, ranks
recipes for the ingredients a user has, and suggests substitutions. This write-up explains
the decisions on retrieval, normalization, ranking, computation, uncertainty and external search,
and what the evaluation found. Detailed notes, with more numbers, are in
[interview_notes.md](interview_notes.md); the eval is in [../evals/README.md](../evals/README.md).

## 1. The central decision: the LLM parses, code answers

The assignment's main risk is an answer that sounds right but isn't in the data. So the
LLM has one job: it turns each message into a structured `TurnIntent` (action, dish text,
include and exclude terms, step limit, statistic, substitution target…). It uses Claude
structured outputs, so the code receives validated, typed fields. Everything after that is
deterministic code: session rules, SQL filters, statistics, ranking, evidence mining, and
**template** replies.

- A template can't invent a title, a number or a cooking time. The only LLM-authored text that
  reaches the user is a category expansion ("dairy" → milk, butter, …) and the name of a
  missing attribute. Both are labeled.
- The same split makes the system testable: 175 unit tests run with a fake LLM, and the eval
  runs the whole pipeline after parsing with no API key.
- **Trade-off:** replies are plainer than LLM prose. Letting an LLM rephrase the templates, without
  adding facts, is possible future work. I also didn't use tool calling. A single parse is cheaper,
  easier to test, and keeps the model away from writing the final answer.

## 2. Data and identity

- **Stable IDs:** `<source>_<key>`, from the original JSON key. They are independent of load order, and their uniqueness is asserted.
- **Originals are never changed.** Title, ingredient lines and instructions are stored as they appear in the file.
  Normalized names, step counts and rewritten recipes live in separate columns and tables, or exist only in a reply.
- **Skipped records are counted, not hidden:** 681 of 125,164 (0.5%), with no title or no content. So
  the full-dataset denominator, 124,483, is known and stated.

## 3. Normalization

A rule-based pipeline turns an ingredient line into names: it strips noise, parentheticals and quantities,
drops descriptors, singularizes, and applies a small synonym map. Examples: "2 cups shredded mozzarella cheese" becomes
`mozzarella cheese`, and "salt and freshly ground pepper" becomes `salt` and `black pepper`.

- **Why rules, not an LLM or an NLP model:** they're deterministic, fast over 1.32M lines, and every
  rule can be shown and tested. Each name keeps its raw line for tracing.
- **Distinct products stay distinct**, as CLAUDE.md requires. Only whole words are removed, so
  `butter`, `peanut butter` and `buttermilk` are three names, and `dried basil` is not `basil`.
- **Coverage:** 99.5% of non-ad lines yield a name. 5,296 names (those used in 10+ recipes) cover 91.8% of all mentions.
- **Limits:** under 2% of lines give poor names (often instruction sentences stored as ingredient lines in the source). Only the first "or" alternative becomes the name, and
  the synonym map is small.

## 4. Retrieval

SQLite with an FTS5 index (BM25) over title, normalized names, raw lines and instructions,
plus a normalized-ingredient table. SQLite is a single file with no server, so the project runs
anywhere. The same index serves search, statistics and matching.

- **One definition of the filtered set.** `find_matches()` is used by search, stats and the matcher, so
  "chicken recipes without peanuts" is the same set in a result list, a percentage and a ranking.
- **Hard filters are exact, and strict on purpose.** An excluded term must not appear in the title, names, *raw*
  lines or instructions. Raw lines catch the second "or" alternative ("almond or peanut butter").
  This over-excludes ("peanut" also removes peanut oil), which is the safe direction for allergies.
  A recipe whose step count is unknown never passes a step limit.
- **Include has a precise rule.** The term must be the name's last word(s) ("spinach" matches "baby spinach"),
  or be followed only by part words ("chicken" matches "chicken breast"). Derived products ("chicken broth") and
  different products ("peanut butter" for "butter") never match.
- **Ranking:** exact title-phrase matches first, then BM25 weighting title 10, names 3, instructions 1.
  Every query word must match. Under a looser rule, "chicken tikka masala" reported 18,773 matches; now it reports 21.
  `title_only` is used for dish-type questions: "cookies" anywhere gives 7,489 recipes, because "place on a cookie sheet" counts, while titles only give 3,113.
- **Why not embeddings:** constraints and missing-ingredient lists must be exact and explainable.
  Embeddings would blur exactly the distinctions (butter vs peanut butter) the rules protect.
  They would help with paraphrased dish names, which is a stated limitation (section 10).

## 5. Computation

Every count, percentage, mean, median and ranking is computed in SQL and pandas over the **complete**
filtered set, written to a temporary table. The LLM never estimates a number. Each answer is a
`StatResult` that prints what CLAUDE.md requires: the filters, recipes analyzed, the denominator, exclusions
and why, the calculation, and the exact text of the normalization, include, exclude and step rules used.

- Unknown values are excluded and reported, never counted as 0. For example, 33 recipes have no instructions, so their steps are unknown.
- Ties at a ranking cut-off are reported, and each ingredient counts once per recipe.
- **Step rule:** one step is one non-empty paragraph. Sources split steps differently
  (Allrecipes mean 3.32, Epicurious 5.02, Food Network 4.02), and answers say that cross-source comparisons are rough.
- Example: "what share of chicken recipes use garlic?" gives 4,287 of 9,364 = 45.8%, and the reply lists which
  names were counted as garlic.

## 6. Ranking for the user's ingredients (Task 2)

Only existing recipes are ranked. The hard filters run first, and then every candidate is scored in SQL and pandas:

```
coverage = matched / required      share of the recipe you already have
usage    = used / have             share of your ingredients it uses
score    = (coverage + usage) / 2 - 0.03 x missing
```

- **Why this formula:** my first version used coverage alone, and it ranked "Coconut Rice" (2 of 2 ingredients, using
  2 of the user's 5) above recipes that use everything the user has. Averaging with usage fixes that.
  The per-item penalty separates recipes that need more shopping. Ties are broken deterministically: fewer missing, fewer steps, then title.
- Pantry staples (salt, black pepper, water) are assumed only if the user didn't list them. The reply says so, and the user can turn this off.
- Each result shows the matched ingredients (labeled **exact** or **variant**, e.g. rice matched basmati rice), the missing and unused ones, the step count, and
  the arithmetic behind its rank. Exact duplicate recipes in the dataset are merged, and their IDs listed.
- **Quantities are compared only when reliable:** mass with mass, volume with volume, count with count.
  Cups against grams would need a density, so the answer says "quantity not verified" rather than guessing.
- Example: for 2 lb chicken breast, onion, garlic, rice and coconut milk, 52,503 recipes use at least one item.
  #1 is Polynesian Chicken Fafa: coverage 5/8 and usage 5/5, so (0.62 + 1.00)/2 − 0.03 × 3 = 0.72. Its chicken check says "enough (907 g vs 454 g)".

## 7. Substitution (Task 3)

The dataset doesn't contain substitutions as such, but recipe authors state them, and similar recipes reveal them.
The evidence comes in three tiers, strongest first, and each one cites recipe IDs:

1. **Stated alternatives:** "1 cup butter or margarine", "(spinach may be substituted)". These are split into
   the *same dish* (title words match this recipe's) and *other dishes*, which is labeled indirect.
2. **Near-identical recipes:** same-dish recipes overlapping at least 50% that lack the target and use X instead.
3. **Usage pattern:** ingredients used alongside the same other ingredients (PPMI cosine over co-occurrence).
   This is the weakest tier, and it is always labeled indirect.

- **A fixed grading rule:** *strong* means stated twice in this dish, or stated once plus a near-identical recipe. *Moderate* means stated once,
  2+ near-identical recipes, or 10+ other dishes. Anything less is *weak*.
- **Conflict check:** real substitutes rarely appear in the same recipe as what they replace (butter and margarine share 77
  recipes; butter and sugar share 14,457). A candidate found together with the target in at least 20% of the rarer one's recipes is
  flagged *conflicting*. This is how weak or conflicting evidence is shown rather than smoothed over.
- **Verified vs predicted:** the reply separates *verified* (these recipes exist and say this) from *predicted, not
  verified* (the rewritten ingredient list and instructions). The rewrite marks each changed line, states that
  **the same amount is assumed**, and flags steps whose technique was written for the original ingredient ("cream the butter").
  A safety note always says that recipe text can't show that a swap is safe for an allergy or a medical diet.
- **Constraints:** a candidate that breaks a session exclusion is labeled "BREAKS your exclusion". It is never chosen
  automatically, and gets a WARNING if the user asks for it anyway.
- Examples:
  - *Butter in Banana Banana Bread:* margarine is strong (2 same-dish recipes, 457 other recipes, 2
    near-identical recipes; together with butter in only 8%). With "no margarine", olive oil (moderate, indirect: 85 other recipes) is used instead.
  - *Eggs in Country Banana Bread:* everything is weak, and milk, cream, evaporated milk and meringue powder
    are flagged conflicting (found with eggs in 28–51% of recipes). The reply says the evidence is weak and offers web search.

## 8. Uncertainty and refusal

The system prefers saying "I don't know" to an unsupported answer:

- **Missing attributes:** nutrition, cooking times, cuisine and diet labels aren't in the data. These questions are refused, and the
  reply says what *is* available. Every opened recipe says that nutrition and times are not in the dataset.
- **No match:** the reply says so, then shows what relaxing each single constraint would give, each item marked
  "VIOLATES your constraint". Nothing is applied unless the user agrees.
- **Parser failure:** if the model declines or its output is unusable, the reply is "please rephrase", never a guess. On an API error the filters stay
  unchanged.
- **Nothing applies silently.** Every reply ends with the active filters. AI-proposed category lists
  are shown and can be edited. `--debug` prints the parsed intent.
- **Persistent restrictions:** exclusions, the step limit and the source filter stay on across turns and topics until the
  user removes them. Dish text and must-include terms belong to the current topic.

## 9. External search

Web search is secondary and runs only when the user asks ("search the web"). It calls Claude with the
server-side web search tool, asking for ratios, effects on the result, and where sources disagree, with no safety claims.
The output appears in its own section, labeled "WEB SEARCH, not from the dataset, not verified by this system",
with links, after the dataset evidence. A failure there is never fatal. The live path is tested
only with a fake client so far, because there was no API key on the build machine.

## 10. Evaluation

The eval has 10 conversations (26 turns, 57 automatic checks) on the real data: `python -m evals.run_eval`. Numbers are
**recomputed by a different path**: the garlic share by plain SQL, and steps by source from the raw JSON files. Every
listed recipe is re-checked against the exclusions and step limit, and every cited ID is checked to exist.
**55 of 57 checks pass.**

- **Found and fixed by the eval:** when hard filters emptied a result, search fell back to matching *any* word.
  "Lobster bisque, I'm allergic to shellfish" returned tomato bisques, and "vegan cheesecake, no dairy or eggs, 2 steps"
  returned smoothies. The fallback now applies only when the words never occur together in the dataset.
  Otherwise the reply says nothing matches and lists the 14 lobster bisques as violating alternatives.
- **Known failure: quantities don't affect ranking.** With "2 eggs", a recipe needing 4 eggs ties for first. The shortfall is
  reported but not scored. The fix would be "fewer known shortfalls" as the first tie-breaker.
- **Known failure: same-dish evidence uses title words.** "Chicken Valdostano" has 0 same-dish recipes, so only
  indirect evidence remains (labeled as such).
- **One-shot baseline:** `python -m evals.one_shot` asks the model the same questions with no data and grades the answers
  (garlic share 26.4%; Allrecipes mean steps 3.32; banana-bread IDs must exist; lobster bisque with a shellfish
  allergy has 0 matches). **It hasn't been run yet (no API key).** What can be said without running it: keys are random
  32-character strings, so any specific recipe ID a one-shot answer gives must be invented. This system cites only
  retrieved IDs, and the eval verifies every one.
- **Not yet evaluated:** the live parser on real messages (`--live`), for the same reason.

## 11. Limitations and next steps

| Limitation | Effect | Next step |
|---|---|---|
| Rule-based normalizer, small synonym map | <2% poor names; some variants stay separate | Grow the map from audits of frequent names |
| Strict exclusion | Over-excludes ("peanut" removes peanut oil) | Allergen-specific term lists, shown to the user |
| Category expansion by the LLM | Can miss terms (shellfish was missed once, then fixed) | A fixed, reviewed list per category |
| "pepper" is ambiguous | Black pepper and bell pepper both match | A disambiguation question |
| Step counts differ by source | Cross-source comparisons are rough | Stated in every step answer |
| Quantities not in the ranking | A recipe you can't make can rank first | Shortfall tie-breaker |
| Same-dish lookup by title | Unique titles get only indirect evidence | Similar recipes by ingredient overlap |
| Substitution amount assumed 1:1 | Rewritten amounts may be wrong | Ratios from labeled external sources |
| Live parser and web search untested on the API | Unknown parse accuracy | Run `evals.run_eval --live` and `evals.one_shot` |

## 12. Use of AI coding tools

The code, tests and docs were written with Claude Code, an AI coding assistant, working step by step from the
plan in `CLAUDE.md`. I reviewed the design decisions. Measurements and test expectations were checked against the real data,
and the eval's numbers are recomputed independently rather than trusted. At runtime the app
uses Claude (`claude-opus-5-5`) only to parse messages, and for web search when the user asks.
