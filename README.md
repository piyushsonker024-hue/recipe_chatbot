# Recipe Chatbot

A conversational recipe assistant over the [Recipe Box dataset](https://eightportions.com/datasets/Recipes/)
(124,483 recipes from Allrecipes, Epicurious and Food Network). It searches, computes
statistics, ranks recipes for the ingredients you have, and suggests substitutions. Every answer
is grounded in the data:

- **The LLM only parses** your message into a structured intent. Every recipe, number and piece
  of evidence comes from code (SQLite and pandas) over the dataset.
- **Every statistic** states its filters, the number of recipes analyzed, the denominator, the calculation and the rules used.
- **Hard constraints** (allergies, exclusions, step limits) persist through the conversation and are
  never relaxed silently. If nothing matches, the bot says so and offers alternatives clearly marked as violating a constraint.
- **Missing data** (nutrition, cooking times) is never estimated.
- **Substitutions** cite the recipe IDs behind them, separate verified evidence from a predicted
  rewrite, and use the web only on request, labeled as external.

## Run it on another machine

Developed and tested on Python 3.14 (macOS).

```bash
# 1. Install
git clone <this repo> recipe_chatbot && cd recipe_chatbot
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Dataset: download recipes_raw.zip from https://eightportions.com/datasets/Recipes/
#    and put the three JSON files in data/:
#      data/recipes_raw_nosource_ar.json
#      data/recipes_raw_nosource_epi.json
#      data/recipes_raw_nosource_fn.json

# 3. Build the database (one time, about 40 s; writes data/recipes.db, about 640 MB)
python -m recipe_bot.store            # add --rebuild to rebuild

# 4. API key (used to parse messages, and for web search only when you ask)
export ANTHROPIC_API_KEY=sk-ant-...   # never commit it; .env is git-ignored
# optional: export RECIPE_BOT_MODEL=claude-opus-5-5   (the default)

# 5. Chat
python main.py                        # add --debug to print each parsed intent
```

Commands that work without the LLM: `/state` (active filters), `/reset`, `/help`, `/quit`.

### Example session

```
you> banana bread recipes
you> I'm allergic to nuts            (the exclusion stays on for the rest of the session)
you> only ones with 5 steps or fewer
you> show me the second one
you> I'm out of eggs, what can I use?
you> search the web for that
you> what percentage of recipes use garlic?
you> I have 2 lb chicken breast, an onion, garlic and rice. What can I make?
```

## Tests and evaluation

```bash
python -m pytest -q                   # 175 unit tests; small built-in sample data, no dataset or key needed
python -m evals.run_eval              # 10 conversations against the real data, no key needed
python -m evals.run_eval --live       # the same, with the real LLM parser (needs a key)
python -m evals.one_shot              # one-shot LLM baseline vs this system (needs a key)
```

See [evals/README.md](evals/README.md) for the method, what worked, what failed and why,
and the one-shot comparison. Transcripts of each test conversation are in
[evals/transcripts/](evals/transcripts/).

## How it works

```
3 JSON files -> data_loader -> normalizer + step counter -> SQLite (FTS5 + ingredient table)
user message -> intent.py (Claude: structured TurnIntent) -> session.py (deterministic state rules)
             -> search / stats / matcher / substitution (code over the data) -> answer.py (template reply)
```

| Module | Role |
|---|---|
| `recipe_bot/data_loader.py` | Loads the 3 files. Stable IDs `<source>_<key>`; the original fields are never altered |
| `recipe_bot/normalizer.py` | Rule-based ingredient names: strips quantities, units and prep words, singularizes, applies synonyms; keeps distinct products apart (butter vs peanut butter) |
| `recipe_bot/steps.py` | A step is one non-empty paragraph of the original instructions |
| `recipe_bot/store.py` | SQLite: recipes, normalized ingredients, an FTS5 index (BM25), the co-occurrence table |
| `recipe_bot/search.py` | Hybrid search (title phrase plus BM25) with strict filters; shared by search, statistics and matching |
| `recipe_bot/stats.py` | Counts, shares, top-N, means and medians, over the full filtered set |
| `recipe_bot/matcher.py`, `quantities.py` | Task 2: `score = (coverage + usage)/2 - 0.03 x missing`; quantities compared only in the same kind of measure |
| `recipe_bot/substitution.py` | Task 3: stated alternatives, near-identical recipes and usage-pattern evidence; graded, conflict-checked, cited |
| `recipe_bot/intent.py`, `session.py`, `answer.py`, `chat.py` | LLM parsing, session state, replies, CLI |

**Write-up:** [docs/WRITEUP.md](docs/WRITEUP.md) covers the decisions on retrieval, normalization, ranking, computation, uncertainty and external search, plus the evaluation and its limits. Longer notes with more numbers are in [docs/interview_notes.md](docs/interview_notes.md) (also as a PDF).

## Known limitations

- Ingredient normalization is rule-based. A small share of lines yield poor names, and the synonym map is small.
- Step counts aren't fully comparable across sources, because each source splits steps differently.
- Exclusions are strict word matches, so they over-exclude ("peanut" also removes peanut oil). Category lists such as "dairy" are proposed by the LLM and always shown to you.
- Ingredient matching ranks by name. Quantity shortfalls are reported but don't affect the score.
- A substitution assumes the same amount, and finding the "same dish" depends on title words.
- The dataset has no nutrition, cooking-time, cuisine or diet labels.

## AI tool disclosure

The code, tests and docs were written with Claude Code (an AI coding assistant), step by step
from the plan in `CLAUDE.md`. The design was reviewed, and the results were checked against the real
data. At runtime the app calls Claude (`claude-opus-5-5`) to parse messages into structured intents,
and for web search when the user asks for it.
