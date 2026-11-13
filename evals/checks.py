"""Checks used by the eval cases. Each check takes a Context and returns (passed, detail).

Checks that verify numbers recompute them by a *different path* than the bot
(raw JSON via the loader, or plain SQL instead of stats.py), so a bug in the
stats engine cannot hide by agreeing with itself.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from statistics import mean, median

from recipe_bot.search import violations
from recipe_bot.session import Session

ID_RE = re.compile(r"\[((?:ar|epi|fn)_[^\]\s]+)\]")


@dataclass
class Context:
    conn: object
    session: Session
    reply: str


def ids_in(reply: str) -> list[str]:
    return ID_RE.findall(reply)


# ---------- reply text ----------

def contains(*texts):
    def check(ctx):
        missing = [t for t in texts if t not in ctx.reply]
        return not missing, f"reply contains {texts}" if not missing else f"missing {missing}"
    check.label = f"contains {', '.join(map(repr, texts))}"
    return check


def not_contains(*texts):
    def check(ctx):
        found = [t for t in texts if t in ctx.reply]
        return not found, "none present" if not found else f"found {found}"
    check.label = f"does not contain {', '.join(map(repr, texts))}"
    return check


def no_number_for(word):
    """The reply must not state a number next to an attribute the data lacks."""
    pattern = re.compile(rf"\d[\d,.]*\s*{word}|{word}\D{{0,15}}\d", re.IGNORECASE)
    def check(ctx):
        m = pattern.search(ctx.reply)
        return m is None, "no invented value" if m is None else f"found '{m.group(0)}'"
    check.label = f"states no number for {word!r}"
    return check


def aggregate_fields():
    """CLAUDE.md: filters, n analyzed, denominator, calculation and rules."""
    needed = ["Filters:", "Recipes analyzed:", "Denominator:", "Calculation:", "Rule ("]
    check = contains(*needed)
    check.label = "states filters, n analyzed, denominator, calculation and rules"
    return check


# ---------- IDs and constraints ----------

def ids_exist():
    def check(ctx):
        ids = ids_in(ctx.reply)
        bad = [i for i in ids if not ctx.conn.execute(
            "SELECT 1 FROM recipes WHERE recipe_id = ?", (i,)).fetchone()]
        return bool(ids) and not bad, f"{len(ids)} IDs, all exist" if not bad else f"unknown IDs {bad}"
    check.label = "every cited recipe ID exists in the dataset"
    return check


def results_respect_exclusions():
    def check(ctx):
        if "No recipe matches all of your constraints" in ctx.reply:
            return True, "reported no match"
        bad = {rid: v for rid in ctx.session.last_ids
               if (v := violations(ctx.conn, rid, ctx.session.exclude))}
        n = len(ctx.session.last_ids)
        return n > 0 and not bad, f"{n} results, none mention {ctx.session.exclude}" if not bad \
            else f"violations: {bad}"
    check.label = "no result mentions an excluded ingredient (checked independently per recipe)"
    return check


def results_within_steps():
    def check(ctx):
        limit = ctx.session.max_steps
        steps = {rid: ctx.conn.execute("SELECT step_count FROM recipes WHERE recipe_id = ?",
                                       (rid,)).fetchone()[0] for rid in ctx.session.last_ids}
        bad = {r: s for r, s in steps.items() if s is None or s > limit}
        return bool(steps) and not bad, f"all {len(steps)} have <= {limit} steps" if not bad \
            else f"over the limit: {bad}"
    check.label = "every result is within the step limit"
    return check


def state(**expected):
    def check(ctx):
        wrong = {}
        for key, want in expected.items():
            have = getattr(ctx.session, key)
            if isinstance(want, list) and isinstance(have, list):
                ok = all(w in have for w in want)          # subset: "still contains"
            else:
                ok = have == want
            if not ok:
                wrong[key] = have
        return not wrong, "session as expected" if not wrong else f"session has {wrong}"
    check.label = "session keeps " + ", ".join(f"{k}={v}" for k, v in expected.items())
    return check


def titles_contain(word):
    """Every listed result is actually the requested dish."""
    def check(ctx):
        titles = dict(ctx.conn.execute(
            f"SELECT recipe_id, title FROM recipes WHERE recipe_id IN "
            f"({','.join('?' * len(ctx.session.last_ids))})", ctx.session.last_ids).fetchall()) \
            if ctx.session.last_ids else {}
        if "No recipe matches" in ctx.reply:
            return True, "reported no match"
        off = [t.strip() for t in titles.values() if word not in t.lower()]
        return not off, "all results are the dish" if not off else \
            f"{len(off)} of {len(titles)} results are not '{word}': {off[:3]}"
    check.label = f"results are '{word}' recipes, or the reply says nothing matches"
    return check


# ---------- independent recomputation ----------

def result_percentage(reply: str) -> tuple[int, int] | None:
    m = re.search(r"Result: ([\d,]+) of ([\d,]+) =", reply)
    return (int(m.group(1).replace(",", "")), int(m.group(2).replace(",", ""))) if m else None


def share_matches_sql(term):
    """Recount with plain SQL using only the 'last word(s)' rule. The bot also counts
    part-word names ('garlic clove'), so the SQL count must be <= the bot's and close."""
    def check(ctx):
        got = result_percentage(ctx.reply)
        if not got:
            return False, "no 'Result: x of y' line"
        sql = ctx.conn.execute(
            "SELECT COUNT(DISTINCT recipe_id) FROM ingredients WHERE name = ? OR name LIKE ?",
            (term, f"% {term}")).fetchone()[0]
        total = ctx.conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
        ok = got[1] == total and sql <= got[0] <= sql * 1.05
        return ok, (f"bot {got[0]:,}/{got[1]:,}; plain SQL (last-word rule only) {sql:,}/{total:,}; "
                    f"difference {got[0] - sql:,} from part-word names")
    check.label = f"'{term}' share agrees with an independent SQL count"
    return check


@lru_cache(maxsize=1)
def raw_step_counts() -> dict[str, list[int]]:
    """Step counts recomputed from the raw JSON files, bypassing the database."""
    from recipe_bot.data_loader import DEFAULT_DATA_DIR, load_recipes
    from recipe_bot.steps import count_steps
    recipes, _ = load_recipes(DEFAULT_DATA_DIR)
    out: dict[str, list[int]] = {}
    for rid, instructions in recipes["instructions"].items():
        n = count_steps(instructions)
        if n is not None:
            out.setdefault(rid.split("_")[0], []).append(n)
    return out


def step_stats_match_raw():
    def check(ctx):
        details, ok = [], True
        for source, counts in sorted(raw_step_counts().items()):
            want_mean, want_median = round(mean(counts), 2), median(counts)
            m = re.search(rf"source={source}, recipes=([\d,]+), mean=([\d.]+), median=([\d.]+)",
                          ctx.reply)
            if not m:
                return False, f"no row for {source}"
            n, got_mean, got_median = int(m.group(1).replace(",", "")), float(m.group(2)), float(m.group(3))
            same = n == len(counts) and abs(got_mean - want_mean) < 0.01 and got_median == want_median
            ok &= same
            details.append(f"{source}: bot n={n:,} mean={got_mean} median={got_median}; "
                           f"raw n={len(counts):,} mean={want_mean} median={want_median}")
        return ok, "; ".join(details)
    check.label = "steps by source agree with a recount from the raw JSON files"
    return check


def quantity_shortfalls_rank_lower():
    """A result the user lacks enough of (by their own stated amount) should not rank above
    one they can make with what they have."""
    def check(ctx):
        blocks = re.split(r"\n(?=\d+\. )", ctx.reply)[1:]
        short = [i for i, b in enumerate(blocks) if "not enough:" in b]
        fine = [i for i, b in enumerate(blocks) if "not enough:" not in b]
        bad = [(s, f) for s in short for f in fine if s < f]
        return not bad, (f"results with a shortfall at ranks {[s + 1 for s in short]}, "
                         f"without at {[f + 1 for f in fine]}")
    check.label = "results with a quantity shortfall rank below results without one"
    return check


def same_dish_found(minimum=5):
    def check(ctx):
        m = re.search(r"Compared against ([\d,]+) recipes? of the same dish", ctx.reply)
        n = int(m.group(1).replace(",", "")) if m else 0
        return n >= minimum, f"{n} same-dish recipes compared"
    check.label = f"at least {minimum} recipes of the same dish are compared"
    return check
