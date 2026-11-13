"""Run the eval conversations against the real database.

    python -m evals.run_eval            scripted: the expected intents are executed (no API key)
    python -m evals.run_eval --live     the real LLM parser reads each message; its intent is
                                        scored against the expected one, then executed

Writes evals/transcripts/<case>.md (every turn, reply and check) and evals/RESULTS.md.
"""

import argparse
import sys
import time
from pathlib import Path

from recipe_bot.answer import handle
from recipe_bot.chat import last_titles
from recipe_bot.intent import api_error_message
from recipe_bot.intent import TurnIntent
from recipe_bot.session import Session
from recipe_bot.store import connect

from .cases import CONVERSATIONS
from .checks import Context

OUT = Path(__file__).parent


# ---------- live parser scoring ----------

def norm(value):
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list):
        return [norm(v) for v in value]
    return value


def parse_diffs(expected: dict, parsed: TurnIntent | None) -> list[str]:
    """Fields where the parsed intent differs from the expected one. Lists: every expected
    item must be present; expansions: every expected category must be present."""
    if parsed is None:
        return ["parser returned nothing"]
    got = parsed.model_dump()
    diffs = []
    for key, want in expected.items():
        have = got.get(key)
        if key == "exclusion_expansions":
            cats = {e["category"].lower() for e in have}
            ok = all(e["category"] in cats for e in want)
        elif isinstance(want, list):
            ok = set(norm(want)) <= set(norm(have or []))
        else:
            ok = norm(want) == norm(have)
        if not ok:
            diffs.append(f"{key}: expected {want!r}, got {have!r}")
    return diffs


# ---------- running ----------

def run_case(conn, case: dict, parser=None, web=None) -> dict:
    session = Session()
    turns = []
    for turn in case["turns"]:
        expected = TurnIntent(**turn["intent"])
        start = time.time()
        diffs = None
        try:
            if parser is not None:
                parsed = parser.parse(turn["user"], session, last_titles(conn, session))
                diffs = parse_diffs(turn["intent"], parsed)
                intent = parsed
            else:
                intent = expected
            reply = handle(conn, session, intent, web=web)
        except Exception as e:      # API overload/quota: later turns depend on this one, so stop
            error = api_error_message(e) or f"{type(e).__name__}: {e}"
            turns.append({"user": turn["user"], "intent": None, "reply": f"[NOT RUN] {error}",
                          "checks": [(c.label, False, "not run (API error)") for c in turn["checks"]],
                          "parse_diffs": None, "seconds": time.time() - start})
            return {"case": case, "turns": turns, "passed": False, "error": error}
        seconds = time.time() - start
        ctx = Context(conn, session, reply)
        results = [(c.label, *c(ctx)) for c in turn["checks"]]
        turns.append({"user": turn["user"], "intent": intent, "reply": reply, "checks": results,
                      "parse_diffs": diffs, "seconds": seconds})
    passed = all(ok for t in turns for _, ok, _ in t["checks"])
    return {"case": case, "turns": turns, "passed": passed, "error": None}


def transcript(result: dict, live: bool) -> str:
    case = result["case"]
    lines = [f"# {case['name']}", "", f"Covers: {case['covers']}", "",
             f"Mode: {'live parser' if live else 'scripted intents'}", ""]
    for i, t in enumerate(result["turns"], 1):
        intent = t["intent"].model_dump_json(exclude_defaults=True) if t["intent"] else "null"
        lines += [f"## Turn {i}", "", f"**User:** {t['user']}", "",
                  f"**Intent:** `{intent}`", ""]
        if t["parse_diffs"] is not None:
            lines += [f"**Parser:** {'matches expected' if not t['parse_diffs'] else '; '.join(t['parse_diffs'])}", ""]
        lines += ["**Bot:**", "", "```", t["reply"], "```", "", "**Checks:**", ""]
        lines += [f"- {'PASS' if ok else 'FAIL'}: {label} ({detail})" for label, ok, detail in t["checks"]]
        lines += ["", f"_{t['seconds']:.1f} s_", ""]
    return "\n".join(lines)


def outcome(result: dict) -> str:
    expect_fail = result["case"].get("expect_fail", False)
    if result.get("error"):
        return "ERROR (API; re-run this case)"
    if result["passed"]:
        return "PASS (expected to fail: now fixed?)" if expect_fail else "PASS"
    return "FAIL (known, documented)" if expect_fail else "FAIL"


def summary(results: list[dict], live: bool) -> str:
    n_checks = sum(len(t["checks"]) for r in results for t in r["turns"])
    n_ok = sum(ok for r in results for t in r["turns"] for _, ok, _ in t["checks"])
    lines = ["# Eval results", "",
             f"Mode: {'live parser' if live else 'scripted intents (no API key needed)'}. "
             f"Re-run with `python -m evals.run_eval{' --live' if live else ''}`.", "",
             f"Checks passed: {n_ok}/{n_checks}", "",
             "| Case | Covers | Turns | Checks | Outcome |", "|---|---|---|---|---|"]
    for r in results:
        c = r["case"]
        ok = sum(ok for t in r["turns"] for _, ok, _ in t["checks"])
        total = sum(len(t["checks"]) for t in r["turns"])
        lines.append(f"| [{c['name']}](transcripts/{c['name']}.md) | {c['covers']} | "
                     f"{len(r['turns'])} | {ok}/{total} | {outcome(r)} |")
    if live:
        turns = [t for r in results for t in r["turns"]]
        exact = sum(not t["parse_diffs"] for t in turns)
        lines += ["", f"Parser: {exact}/{len(turns)} turns parsed as expected."]
    failed = [(r["case"]["name"], label, detail) for r in results for t in r["turns"]
              for label, ok, detail in t["checks"] if not ok]
    if failed:
        lines += ["", "## Failed checks", ""]
        lines += [f"- **{name}**: {label}: {detail}" for name, label, detail in failed]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    args = argparse.ArgumentParser()
    args.add_argument("--live", action="store_true", help="use the real LLM parser")
    args.add_argument("--case", help="run one case by name")
    opts = args.parse_args(argv)
    conn = connect()
    parser = web = None
    if opts.live:
        from recipe_bot.intent import IntentParser
        from recipe_bot.substitution import search_web
        parser = IntentParser()
        web = lambda title, target, sub: search_web(parser.client, title, target, sub, parser.model)  # noqa: E731
    cases = [c for c in CONVERSATIONS if not opts.case or c["name"] == opts.case]
    results = []
    (OUT / "transcripts").mkdir(exist_ok=True)
    for case in cases:
        r = run_case(conn, case, parser, web)
        results.append(r)
        (OUT / "transcripts" / f"{case['name']}.md").write_text(transcript(r, opts.live))
        print(f"{outcome(r):28} {case['name']}")
    if not opts.case:
        (OUT / "RESULTS.md").write_text(summary(results, opts.live))
        print(f"Wrote {OUT / 'RESULTS.md'}")
    errors = [r["case"]["name"] for r in results if r.get("error")]
    if errors:
        print(f"API errors in: {', '.join(errors)}. Re-run each with --live --case <name>.")
    unexpected = [r for r in results if not r["passed"]
                  and (r.get("error") or not r["case"].get("expect_fail"))]
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
