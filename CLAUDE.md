# CLAUDE.md

## Project
GenAI Intern Assignment: a conversational recipe chatbot over the Recipe Box dataset (https://eightportions.com/datasets/Recipes/). It searches, analyzes, matches and adapts recipes. Answers must be grounded in retrieved data. Refusing an unsupported answer is better than fabricating one.
## Hard rules
- Use all three dataset JSON files (`recipes_raw_nosource_ar.json`, `recipes_raw_nosource_epi.json`, `recipes_raw_nosource_fn.json`).
- Every recipe keeps a stable ID (`<source>_<key>`) plus the original title, ingredients and instructions. Never alter the originals; store normalized fields separately.
- Counts, percentages, rankings, averages and medians are computed in code (SQL/pandas) over the complete filtered set. The LLM never estimates them.
- Aggregate answers must state: filters applied, number of recipes analyzed, denominator, calculation, and the ingredient-normalization and step-counting rules used.
- Do not fabricate nutrition values, cooking times or other attributes missing from the data. Say what is missing. Label any external fact or estimate clearly.
- Hard constraints (allergies, excluded ingredients, step limits) are never relaxed silently. If nothing matches, say so, then offer alternatives clearly marked as violating the constraint.
- Never claim a substitution is medically safe based on recipe text alone.
- The chatbot must work in a single session with follow-ups. A newly stated restriction applies to the active search until the user changes it.

## Tasks
1. **Search and Q&A (3/10):** search by dish name, ingredient or natural language; return titles and IDs, with ingredients and instructions on request; handle follow-ups; compute statistics.
2. **Ingredient matching (3/10):** rank existing recipes only (never invent) for the user's ingredients, hard constraints and preferences. Show matched, missing and extra ingredients, step count and the ranking reason. Quantities are used only when reliably comparable; otherwise report a name-level match and say quantity sufficiency was not verified.
3. **Substitution (4/10):** local dataset evidence first, citing recipe IDs and saying when the evidence is indirect. External search is secondary, clearly labeled and linked. Return an updated ingredient list and revised instructions, and separate predictions from verified outcomes.

## Architecture (planned)
- **Data layer:** load the 3 JSON files into SQLite/pandas with stable IDs and a normalized-ingredient table.
- **Normalizer:** lowercase, strip quantities and units, lemmatize, apply a synonym map. Keep distinct forms or products separate when it affects the match (e.g. butter vs. peanut butter). Document its limits.
- **Retrieval:** hybrid search (BM25 and/or FAISS embeddings) for search; SQL/pandas for analytics.
- **Session state:** a structured object holding the active query, constraints and last results.
- **LLM role:** parse intent into structured filters and phrase answers. It is not a source of facts.
- **Ranking (Task 2):** transparent formula, e.g. matched/required with penalties for missing and extra ingredients, after a hard-filter pass.
- **Substitution evidence (Task 3):** mine co-occurrence and similar recipes in the dataset; cite IDs.

## Build order
1. Data loader, ID scheme, normalizer.
2. Task 1 search and stats engine, then the CLI/web UI with session state.
3. Task 2 matcher and scorer.
4. Task 3 substitution.
5. Eval set, test conversations, README, write-up.

## Deliverables
- Public GitHub repo with a brief README on running it on another machine (install, API key setup, dataset download, run command).
- At least 5 test conversations, including a multi-turn follow-up, an aggregate statistics query, a no-match case, and a substitution with weak or conflicting evidence.
- A small reproducible eval set: what worked, what failed and why, plus at least one case where a one-shot LLM answer is wrong or ungrounded and how this system handles it.
- Write-up of decisions on retrieval, normalization, ranking, computation, uncertainty and external search.
- Brief disclosure of where AI coding tools were used.

## Conventions
- Python 3, with dependencies pinned in `requirements.txt`. API keys come from environment variables and are never committed.
- Keep functions small and explainable; the author must be able to walk through all code in the interview and modify it live.
- Prefer deterministic, testable code for anything numeric or filter-related. Add tests for the normalizer, step counter and stats functions.
