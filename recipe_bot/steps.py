"""Count instruction steps.

Rule: a step is one non-empty paragraph (text between newlines) of the
original instructions. All three sources separate steps with newlines.

Limits (state these in aggregate answers):
  - Sources split steps differently. Allrecipes uses short one-action lines;
    Food Network and Epicurious paragraphs can hold several actions, and about
    15% of ar/fn recipes are a single paragraph. Step counts are therefore
    comparable within a source more than across sources.
  - Empty instructions give None (unknown), never 0, so they are excluded
    from averages instead of pulling them down.
"""

from .normalizer import AD_MARKER


def split_steps(instructions: str | None) -> list[str]:
    """Original instructions -> list of step texts."""
    if not instructions:
        return []
    paragraphs = (p.strip() for p in instructions.split("\n"))
    return [p for p in paragraphs if p and p != AD_MARKER]


def count_steps(instructions: str | None) -> int | None:
    """Number of steps, or None when the recipe has no instructions."""
    steps = split_steps(instructions)
    return len(steps) or None
