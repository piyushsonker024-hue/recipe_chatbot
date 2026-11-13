"""Parse ingredient quantities, and compare them only when that is reliable.

    "1 1/2 pounds chicken"      -> 680.4 g (mass)
    "2 (14.5 ounce) cans beans" -> 822.1 g (mass)
    "3 large eggs"              -> 3 (count)
    "2 cloves garlic"           -> 2 clove (its own dimension)
    "salt to taste"             -> None (no quantity)

Comparison rule: two quantities are compared only if they have the same
dimension: mass with mass, volume with volume, a plain count with a plain
count, cloves with cloves. Anything else (cups of flour vs grams of flour,
needing a density) is reported as "quantity not verified", never guessed.

Choices to state:
  - A range ("2 to 3 cups") counts as its upper end: the most the recipe may need.
  - "oz"/"ounce" is treated as weight. A fluid ounce must be written "fl oz".
  - Recipes give totals for their own yield; servings are not in the data,
    so there is no scaling.
"""

import re
from dataclasses import dataclass

UNICODE_FRACTIONS = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3,
                     "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875}
NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
                "twelve": 12, "dozen": 12, "half": 0.5}

# unit word -> (dimension, size in the base unit: grams for mass, ml for volume)
UNITS = {}
for words, dim, size in [
    (("g", "gram", "grams", "gr"), "mass", 1.0),
    (("kg", "kilogram", "kilograms", "kilo", "kilos"), "mass", 1000.0),
    (("oz", "ounce", "ounces"), "mass", 28.3495),
    (("lb", "lbs", "pound", "pounds"), "mass", 453.592),
    (("ml", "milliliter", "milliliters", "millilitre", "millilitres"), "volume", 1.0),
    (("l", "liter", "liters", "litre", "litres"), "volume", 1000.0),
    (("tsp", "teaspoon", "teaspoons", "t"), "volume", 4.92892),
    (("tbsp", "tbs", "tbl", "tablespoon", "tablespoons"), "volume", 14.7868),
    (("cup", "cups", "c"), "volume", 236.588),
    (("pint", "pints", "pt"), "volume", 473.176),
    (("quart", "quarts", "qt"), "volume", 946.353),
    (("gallon", "gallons", "gal"), "volume", 3785.41),
]:
    for w in words:
        UNITS[w] = (dim, size)

# Countable pieces that are only comparable with the same piece.
PIECE_UNITS = {"clove": "clove", "cloves": "clove", "slice": "slice", "slices": "slice",
               "stick": "stick", "sticks": "stick", "can": "can", "cans": "can",
               "package": "package", "packages": "package", "jar": "jar", "jars": "jar",
               "head": "head", "heads": "head", "bunch": "bunch", "bunches": "bunch",
               "stalk": "stalk", "stalks": "stalk", "sprig": "sprig", "sprigs": "sprig"}

# Words after a number that mean it is not a plain count of the ingredient.
NOT_A_COUNT = {"pinch", "pinches", "dash", "dashes", "handful", "handfuls", "piece",
               "pieces", "inch", "inches", "drop", "drops", "to", "taste"}


@dataclass(frozen=True)
class Quantity:
    value: float        # in base units (g, ml) or pieces
    dimension: str      # "mass", "volume", "count", or a piece name such as "clove"
    text: str           # the quantity as written, for display

    def describe(self) -> str:
        if self.dimension == "mass":
            return f"{self.text} ({self.value:.0f} g)"
        if self.dimension == "volume":
            return f"{self.text} ({self.value:.0f} ml)"
        return self.text


def read_number(tokens: list[str], i: int) -> tuple[float | None, int]:
    """Read '1', '1/2', '1 1/2', '1.5', '½', '1½', 'two' at tokens[i]. Returns (value, next index)."""
    def single(tok: str) -> float | None:
        tok = tok.strip("(),")
        if tok in NUMBER_WORDS:
            return NUMBER_WORDS[tok]
        m = re.fullmatch(r"(\d+(?:\.\d+)?)?([½¼¾⅓⅔⅛⅜⅝⅞])?", tok)
        if m and (m.group(1) or m.group(2)):
            return float(m.group(1) or 0) + UNICODE_FRACTIONS.get(m.group(2) or "", 0)
        m = re.fullmatch(r"(\d+)/(\d+)", tok)
        if m and int(m.group(2)):
            return int(m.group(1)) / int(m.group(2))
        return None

    if i >= len(tokens):
        return None, i
    first = single(tokens[i])
    if first is None:
        return None, i
    i += 1
    if i < len(tokens) and re.fullmatch(r"\d+/\d+|[½¼¾⅓⅔⅛⅜⅝⅞]", tokens[i]):  # mixed number
        first += single(tokens[i]) or 0
        i += 1
    return first, i


def read_amount(tokens: list[str], i: int) -> tuple[float | None, int]:
    """A number or a range ('2 to 3', '2-3'); a range gives its upper end."""
    if i < len(tokens) and re.fullmatch(r"\d+(\.\d+)?-\d+(\.\d+)?", tokens[i]):
        return float(tokens[i].split("-")[1]), i + 1
    value, j = read_number(tokens, i)
    if value is None:
        return None, i
    if j + 1 < len(tokens) and tokens[j] in ("to", "or", "-"):
        upper, k = read_number(tokens, j + 1)
        if upper is not None:
            return max(value, upper), k
    return value, j


def read_unit(tokens: list[str], i: int) -> tuple[str | None, float, int]:
    """Unit at tokens[i]: (dimension, size, next index); dimension None if no unit."""
    if i >= len(tokens):
        return None, 0.0, i
    tok = tokens[i].strip(".,")
    if tok in ("fl", "fluid") and i + 1 < len(tokens) and tokens[i + 1].strip(".") in ("oz", "ounce", "ounces"):
        return "volume", 29.5735, i + 2
    if tok in UNITS:
        dim, size = UNITS[tok]
        return dim, size, i + 1
    m = re.fullmatch(r"([a-z]+)", tok)
    if m and tok in PIECE_UNITS:
        return PIECE_UNITS[tok], 1.0, i + 1
    return None, 0.0, i


def parse_quantity(line: str) -> Quantity | None:
    """Quantity at the start of an ingredient line, or None if there is none or it is unclear."""
    text = line.replace("ADVERTISEMENT", "").strip().lower()
    text = re.sub(r"(\d)([a-z])", r"\1 \2", text)            # "500g" -> "500 g"
    text = re.sub(r"([½¼¾⅓⅔⅛])", r" \1", text).replace("  ", " ")
    tokens = text.replace("(", " ( ").replace(")", " ) ").split()
    amount, i = read_amount(tokens, 0)
    if amount is None:
        return None

    # Package with its size in parentheses: "2 (14.5 ounce) cans"
    if i < len(tokens) and tokens[i] == "(":
        size, j = read_amount(tokens, i + 1)
        dim, unit_size, k = read_unit(tokens, j) if size is not None else (None, 0, j)
        if dim in ("mass", "volume") and k < len(tokens) and tokens[k] == ")":
            snippet = " ".join(tokens[:k + 2]).replace("( ", "(").replace(" )", ")")
            return Quantity(amount * size * unit_size, dim, snippet)
        return None                                          # unclear parenthetical

    dim, unit_size, j = read_unit(tokens, i)
    if dim is not None:
        size = unit_size if dim in ("mass", "volume") else 1.0
        return Quantity(amount * size, dim, " ".join(tokens[:j]))
    if i < len(tokens) and tokens[i].strip(".,") in NOT_A_COUNT:
        return None
    if i >= len(tokens):
        return None                                          # a bare number
    return Quantity(amount, "count", " ".join(tokens[:i]))


def total_quantity(lines: list[str]) -> Quantity | None:
    """Sum the quantities of several lines for the same ingredient (butter for crust and
    filling). None if any line has no quantity or the dimensions differ."""
    quantities = [parse_quantity(line) for line in lines]
    if not quantities or any(q is None for q in quantities):
        return None
    if len({q.dimension for q in quantities}) != 1:
        return None
    text = " + ".join(q.text for q in quantities)
    return Quantity(sum(q.value for q in quantities), quantities[0].dimension, text)


def sufficiency(have: Quantity | None, need: Quantity | None) -> str:
    """'enough', 'not enough', or 'not verified' with the reason."""
    if have is None:
        return "quantity not verified (you gave no amount)"
    if need is None:
        return "quantity not verified (recipe amount missing or unclear)"
    if have.dimension != need.dimension:
        return (f"quantity not verified (you have {have.text}, recipe needs {need.text}; "
                "different kinds of measure)")
    verdict = "enough" if have.value >= need.value - 1e-9 else "not enough"
    return f"{verdict}: you have {have.describe()}, recipe needs {need.describe()}"
