"""One-shot LLM baseline: ask Gemini the same questions with no access to the data,
then grade its answers against what this system computes.

    python -m evals.one_shot          (needs GEMINI_API_KEY; writes evals/ONE_SHOT.md)

Grading is automatic where it can be (numbers within tolerance, cited IDs exist in
the dataset); every answer is also saved verbatim for manual review.
"""

import re
import sys
from pathlib import Path

from google.genai import types

from recipe_bot.intent import MODEL
from recipe_bot.search import SearchQuery, search
from recipe_bot.stats import ingredient_share, step_stats
from recipe_bot.store import connect


OUT = Path(__file__).parent / "ONE_SHOT.md"
CONTEXT = ("You are answering questions about the Recipe Box dataset "
           "(https://eightportions.com/datasets/Recipes/): about 125,000 recipes scraped from "
           "Allrecipes, Epicurious and Food Network. Recipe IDs look like '<source>_<key>', "
           "e.g. 'ar_<key>'. Answer directly and concisely.")


def first_percent(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    return float(m.group(1)) if m else None


def first_number(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:steps|step)", text)
    return float(m.group(1)) if m else None


def cases(conn):
    garlic = ingredient_share(conn, SearchQuery(), "garlic")
    pct = round(100 * int(re.search(r"([\d,]+) of", garlic.value).group(1).replace(",", ""))
                / garlic.n_analyzed, 1)
    ar = next(r for r in step_stats(conn, SearchQuery(), by_source=True).rows if r["source"] == "ar")
    bisque = search(conn, SearchQuery(text="lobster bisque", title_only=True,
                                      exclude=["lobster", "shrimp", "crab"]))
    return [
        {"question": "What percentage of recipes in the dataset contain garlic?",
         "truth": f"{pct}% (computed: {garlic.value})",
         "grade": lambda a: (p := first_percent(a)) is not None and abs(p - pct) <= 1.0},
        {"question": "Give me 3 banana bread recipes from the dataset, with their recipe IDs.",
         "truth": "IDs must exist in the dataset",
         "grade": lambda a: bool(ids := cited_ids(a)) and all(exists(conn, i) for i in ids)},
        {"question": "What is the average number of instruction steps in the Allrecipes recipes?",
         "truth": f"{ar['mean']} (mean over {ar['recipes']:,} recipes, one step per paragraph)",
         "grade": lambda a: (n := first_number(a)) is not None and abs(n - ar["mean"]) <= 0.25},
        {"question": "I'm allergic to shellfish. Give me a lobster bisque recipe from the dataset.",
         "truth": f"{bisque.total} recipes match: none can be lobster bisque without shellfish",
         "grade": lambda a: bool(re.search(r"\b(no|none|cannot|can't|isn't|not possible)\b", a,
                                           re.IGNORECASE))},
    ]


def cited_ids(text):
    return re.findall(r"\b(?:ar|epi|fn)_[\w./]+[\w/]", text)


def exists(conn, rid):
    return conn.execute("SELECT 1 FROM recipes WHERE recipe_id = ?", (rid,)).fetchone() is not None


def main() -> int:
    try:
        from recipe_bot.intent import make_client
        client = make_client()
    except Exception as e:
        print(f"Needs GEMINI_API_KEY ({e})", file=sys.stderr)
        return 1
    conn = connect()
    lines = ["# One-shot LLM baseline", "",
             f"Model: {MODEL}, no tools, no data. Each answer is graded against this system's "
             "computed result; answers are verbatim.", ""]
    for c in cases(conn):
        response = client.models.generate_content(
            model=MODEL, contents=c["question"],
            config=types.GenerateContentConfig(system_instruction=CONTEXT))
        answer = (response.text or "").strip()
        ok = c["grade"](answer)
        lines += [f"## {c['question']}", "", f"**Grounded answer (this system):** {c['truth']}", "",
                  f"**One-shot grade:** {'correct' if ok else 'WRONG or ungrounded'}", "",
                  "**One-shot answer:**", "", "> " + answer.replace("\n", "\n> "), ""]
        print(f"{'ok   ' if ok else 'WRONG'} {c['question']}")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
