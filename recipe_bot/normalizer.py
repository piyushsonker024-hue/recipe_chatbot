"""Turn raw ingredient lines into normalized ingredient names.

    "2 cups shredded mozzarella cheese ADVERTISEMENT" -> ["mozzarella cheese"]
    "Kosher salt and freshly ground black pepper"     -> ["salt", "black pepper"]

Pipeline for one line (each step is one small function below):
  1. clean_line      drop the Allrecipes "ADVERTISEMENT" marker and trademark symbols
  2. lowercase; drop section headers ("For the crust:")
  3. strip_noise     remove (parentheticals), "such as ...", "to taste", "for garnish"
  4. special forms   "juice of 1 lime" -> "lime juice"; split "salt and pepper"
  5. comma rule      text after a comma is usually prep ("onion, chopped"), so use the
                     first comma segment that still has a name left after cleaning
  6. "or" rule       "sirloin or filet mignon" -> keep the first alternative
  7. strip_quantity  leading numbers, fractions, ranges and units ("2 1/2 cups")
  8. drop_descriptors size/prep/freshness words ("large", "chopped", "fresh")
  9. singularize     last word only, rule-based ("tomatoes" -> "tomato")
 10. SYNONYMS        map variants to one name ("kosher salt" -> "salt")

Distinct products stay distinct: only whole words are removed, so "peanut
butter" never becomes "butter", and "ground beef" keeps "ground".

Known limits (document in the write-up):
  - English, rule-based; unusual phrasings ("an egg wash made by ...") pass
    through mostly as-is.
  - Only the first "or" alternative that yields a name is kept.
  - Tokens containing digits are dropped, so names like "7-up" lose the number.
  - "and" is split only for salt/pepper; "macaroni and cheese" stays one item.
  - Product forms such as "crushed tomatoes" lose the form word ("tomato").
    "dried" is kept because dried fruit/herbs differ from fresh.
  - The synonym map is small and hand-written; anything missing stays separate.
  - Quantities are discarded here; this module produces names only.
"""

import re

import pandas as pd

AD_MARKER = "ADVERTISEMENT"

UNITS = {
    "cup", "cups", "c", "tablespoon", "tablespoons", "tbsp", "tbs", "tbl",
    "teaspoon", "teaspoons", "tsp", "ounce", "ounces", "oz", "fl", "fluid",
    "pound", "pounds", "lb", "lbs", "gram", "grams", "g", "kg", "kilogram",
    "kilograms", "ml", "milliliter", "milliliters", "liter", "liters", "l",
    "quart", "quarts", "qt", "pint", "pints", "pt", "gallon", "gallons",
    "pinch", "pinches", "dash", "dashes", "drop", "drops", "can", "cans",
    "package", "packages", "pkg", "packet", "packets", "jar", "jars",
    "bottle", "bottles", "box", "boxes", "bag", "bags", "container",
    "containers", "carton", "cartons", "envelope", "envelopes", "stick",
    "sticks", "sprig", "sprigs", "clove", "cloves", "slice", "slices",
    "piece", "pieces", "head", "heads", "bunch", "bunches", "handful",
    "handfuls", "stalk", "stalks", "rib", "ribs", "sheet", "sheets",
    "strip", "strips", "scoop", "scoops", "ear", "ears", "inch", "inches",
    "link", "links",
}

# Units that are also an ingredient when they stand alone ("ground cloves").
UNIT_AND_INGREDIENT = {"clove", "cloves"}

# Words that may appear between or around quantities: "2 to 3", "1 cup plus 2 tbsp".
QUANTITY_WORDS = {
    "to", "or", "plus", "and", "of", "a", "an", "about", "x", "-",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "dozen", "half", "few", "several", "couple",
    "additional", "approximately", "approx", "generous", "scant", "heaped",
}

NUMBER_RE = re.compile(r"^[\d½¼¾⅓⅔⅛⅜⅝⅞/.\-\"'+?]+$")   # 1" (inch mark), "+", "?" (bad fractions)
# "8-ounce", "28-oz", "1¼-inch"
NUMBER_UNIT_RE = re.compile(r"^[\d½¼¾⅓⅔⅛⅜⅝⅞/.]+-?[a-z]+$")

DESCRIPTORS = {
    # size
    "large", "small", "medium", "extra-large", "jumbo", "big", "thin", "thick",
    # freshness / temperature / state
    "fresh", "freshly", "frozen", "thawed", "canned", "cold", "chilled",
    "warm", "lukewarm", "room-temperature", "softened", "melted", "ripe",
    "overripe", "very",
    # prep
    "chopped", "finely", "coarsely", "roughly", "minced", "diced", "sliced",
    "thinly", "thickly", "grated", "shredded", "crushed", "peeled", "seeded",
    "pitted", "cored", "trimmed", "halved", "quartered", "cubed", "julienned",
    "beaten", "lightly", "whisked", "sifted", "toasted", "rinsed", "drained",
    "packed", "loosely", "firmly", "heaping", "level", "rounded", "divided",
    "deveined", "shelled", "cooked", "uncooked", "patted", "dry-packed",
    # cut of meat
    "boneless", "skinless", "bone-in", "skin-on",
    # quality / marketing
    "good", "good-quality", "high-quality", "best-quality", "quality",
    "organic", "unsalted", "salted", "low-sodium", "reduced-sodium",
    "optional",
}

# "ground" is a prep word for spices but part of the product for meat.
GROUND_MEATS = {"beef", "pork", "turkey", "chicken", "lamb", "veal", "meat",
                "sausage", "bison", "chuck"}

# Words that, left on their own, are not an ingredient name.
NOT_A_NAME = {"whole", "plain", "extra", "more", "needed", "taste", "other",
              "and", "or", "with", "of"}

# Connector words that cannot start or end a name.
EDGE_WORDS = {"and", "or", "with", "of", "plus", "for", "in", "to"}

# Adjectives shared across an "or": "yellow or brown mustard" -> "yellow mustard".
SHARED_ADJECTIVES = {"yellow", "red", "green", "white", "black", "brown",
                     "dark", "light", "sweet", "hot", "mild", "dry", "golden",
                     "orange", "purple", "spicy", "smoked", "sharp"}

# "basil leaves" means the herb itself; "bay leaf" does not drop "leaf".
LEAF_HERBS = {"basil", "mint", "parsley", "cilantro", "sage", "thyme",
              "oregano", "tarragon", "rosemary", "dill", "coriander"}

# Last-word singularization: irregulars and words that must not lose their "s".
IRREGULAR_PLURALS = {"leaves": "leaf", "loaves": "loaf", "halves": "half",
                     "knives": "knife", "potatoes": "potato",
                     "tomatoes": "tomato"}
KEEP_S = {"molasses", "hummus", "asparagus", "couscous", "swiss", "grits",
          "greens", "brussels", "schnapps", "citrus", "octopus", "bass",
          "anise", "series", "fries"}

# variant -> canonical name. Applied after singularization.
SYNONYMS = {
    "kosher salt": "salt", "sea salt": "salt", "coarse salt": "salt",
    "table salt": "salt", "fine salt": "salt", "coarse sea salt": "salt",
    "flaky sea salt": "salt", "fine sea salt": "salt", "fleur de sel": "salt",
    "coarse kosher salt": "salt",
    "pepper": "black pepper", "fresh black pepper": "black pepper",
    "black peppercorn": "black peppercorn",
    "all-purpose flour": "flour", "all purpose flour": "flour",
    "plain flour": "flour", "unbleached all-purpose flour": "flour",
    "white sugar": "sugar", "granulated sugar": "sugar", "caster sugar": "sugar",
    "superfine sugar": "sugar", "granulated white sugar": "sugar",
    "light brown sugar": "brown sugar", "dark brown sugar": "brown sugar",
    "golden brown sugar": "brown sugar",
    "confectioners' sugar": "powdered sugar", "confectioners sugar": "powdered sugar",
    "confectioner's sugar": "powdered sugar", "icing sugar": "powdered sugar",
    "extra-virgin olive oil": "olive oil", "extra virgin olive oil": "olive oil",
    "virgin olive oil": "olive oil",
    "scallion": "green onion", "spring onion": "green onion",
    "coriander leaf": "cilantro",
    "garbanzo bean": "chickpea",
    "heavy whipping cream": "heavy cream", "whipping cream": "heavy cream",
    "double cream": "heavy cream",
    "vanilla": "vanilla extract", "pure vanilla extract": "vanilla extract",
    "bicarbonate of soda": "baking soda",
    "corn starch": "cornstarch",
    "courgette": "zucchini", "aubergine": "eggplant",
    "parmesan": "parmesan cheese", "parmigiano-reggiano": "parmesan cheese",
    "parmigiano reggiano": "parmesan cheese",
    "parmigiano-reggiano cheese": "parmesan cheese",
    "mozzarella": "mozzarella cheese", "cheddar": "cheddar cheese",
    "feta": "feta cheese", "ricotta": "ricotta cheese",
    "gruyere": "gruyere cheese", "gruyère": "gruyere cheese",
    "gruyère cheese": "gruyere cheese",
    "flat-leaf parsley": "parsley", "italian parsley": "parsley",
    "flat leaf parsley": "parsley", "italian flat-leaf parsley": "parsley",
    "garlic clove": "garlic",
}

SALT_AND_PEPPER_RE = re.compile(r"^(.*\bsalt)\s+(?:and|&)\s+(.*\bpepper)\b(.*)$")
JUICE_OF_RE = re.compile(r"^(juice|zest|grated zest|finely grated zest)\s+(?:and\s+\w+\s+)?of\s+(.+)$")
TRAILING_RE = re.compile(
    r"\b(to taste|for (garnish|serving|dusting|brushing|frying|decoration|the pan)"
    r"|as needed|if needed|or as needed|or more|plus more|at room temperature"
    r"|of (your )?choice|cut into|cut in).*$"
)


def clean_line(line: str) -> str:
    """Display-safe version of a raw line: no ad marker, no trademark symbols."""
    text = line.replace(AD_MARKER, "")
    text = re.sub(r"[®™©*]", "", text)
    text = re.sub(r"[—–]", "-", text)                # em/en dash -> hyphen
    return re.sub(r"\s+", " ", text).strip()


def strip_noise(text: str) -> str:
    """Remove parentheticals, brand hints and trailing usage phrases."""
    text = re.sub(r"\([^)]*\)?", " ", text)          # (28 ounce), (optional)
    text = re.sub(r"\b(such as|e\.g\.|like)\b.*$", "", text)
    text = TRAILING_RE.sub("", text)
    return text.strip(" ,;.-")


def strip_quantity(tokens: list[str]) -> list[str]:
    """Drop leading quantity tokens: numbers, units and connector words."""
    i = 0
    while i < len(tokens) - 1:   # always keep at least one token
        tok = tokens[i].strip(".,")
        is_number = bool(NUMBER_RE.match(tok)) or bool(NUMBER_UNIT_RE.match(tok))
        if is_number or tok in UNITS or tok in QUANTITY_WORDS:
            i += 1
        else:
            break
    return tokens[i:]


def is_descriptor(tok: str) -> bool:
    """'chopped' or a hyphenated mix of descriptors like 'medium-diced'."""
    return tok in DESCRIPTORS or all(p in DESCRIPTORS for p in tok.split("-"))


def drop_descriptors(tokens: list[str]) -> list[str]:
    """Remove size/prep/freshness words; keep 'ground' before meats."""
    kept = []
    for i, tok in enumerate(tokens):
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        if is_descriptor(tok):
            continue
        if tok == "ground" and nxt not in GROUND_MEATS:
            continue
        kept.append(tok)
    return kept


def singularize(word: str) -> str:
    """Rule-based singular for one word. Deliberately simple and predictable."""
    if word in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[word]
    if word in KEEP_S or len(word) <= 3 or word.endswith(("ss", "us", "is")):
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"                     # berries -> berry
    if word.endswith(("ches", "shes", "xes", "zes", "sses")):
        return word[:-2]                           # peaches -> peach
    if word.endswith("oes"):
        return word[:-2]                           # mangoes -> mango
    if word.endswith("s"):
        return word[:-1]                           # carrots -> carrot
    return word


def strip_edges(tokens: list[str]) -> list[str]:
    """Remove connector words left at either end ("and drained" -> "drained")."""
    while tokens and tokens[0] in EDGE_WORDS:
        tokens = tokens[1:]
    while tokens and tokens[-1] in EDGE_WORDS:
        tokens = tokens[:-1]
    return tokens


def name_from_segment(segment: str) -> str:
    """Normalize one comma-free, 'or'-free piece of text to a name ('' if none)."""
    tokens = segment.split()
    tokens = strip_quantity(tokens)
    if "plus" in tokens:                           # "egg plus 3 tbsp water"
        tokens = tokens[:tokens.index("plus")]
    tokens = [t.strip(".,;:-)") for t in tokens]
    # Sizes such as "1-inch-thick" or "10-to-12-pound" are never part of a name.
    tokens = [t for t in tokens if t and not re.search(r"\d", t)]
    tokens = drop_descriptors(tokens)
    tokens = strip_edges(strip_quantity(tokens) if tokens else tokens)
    if not tokens or (len(tokens) == 1 and (tokens[0] in NOT_A_NAME
                                            or tokens[0] in UNITS - UNIT_AND_INGREDIENT
                                            or tokens[0] in QUANTITY_WORDS
                                            or NUMBER_RE.match(tokens[0]))):
        return ""
    tokens[-1] = singularize(tokens[-1])
    if len(tokens) >= 2 and tokens[-1] == "leaf" and tokens[-2] in LEAF_HERBS:
        tokens = tokens[:-1]                       # basil leaf -> basil
    name = " ".join(tokens)
    return SYNONYMS.get(name, name)


def alternatives(segment: str) -> list[str]:
    """Split on 'or'. An adjective-only first part borrows the noun of the
    next part ("yellow or brown mustard" -> "yellow mustard")."""
    parts = re.split(r"\s+or\s+", segment.strip())
    if len(parts) > 1:
        words, rest = parts[0].split(), parts[1].split()
        if words and words[-1] in SHARED_ADJECTIVES and len(rest) >= 2:
            parts[0] = " ".join(words + rest[1:])
    return parts


def first_name(text: str) -> str:
    """Comma rule then 'or' rule: the first segment and alternative that
    yields a name. "1 can or jar chickpeas" -> "1 can" is empty -> "chickpea"."""
    for segment in text.split(","):
        for alt in alternatives(segment):
            name = name_from_segment(alt)
            if name:
                return name
    return ""


def normalize_ingredient(line: str) -> list[str]:
    """Raw ingredient line -> list of normalized names (usually 0 or 1)."""
    text = clean_line(line).lower()
    if not text or text.endswith(":") or re.match(r"^(special )?equipment\b", text):
        return []                                  # ad marker, header, equipment
    text = re.sub(r"^[a-z ]{3,30}:\s*", "", text)   # "accompaniment: rice" -> "rice"
    text = re.sub(r"^accompaniments?\b\s*", "", text)
    text = re.sub(r"\bhalf[ -]and[ -]half\b", "half-and-half", text)
    text = text.replace("and/or", "or")
    text = strip_noise(text)

    juice = JUICE_OF_RE.match(text)
    if juice:
        fruit = first_name(juice.group(2))
        return [f"{fruit} {juice.group(1).split()[-1]}"] if fruit else []

    sp = SALT_AND_PEPPER_RE.match(text)
    if sp:
        names = [first_name(sp.group(1)), first_name(sp.group(2))]
        return [n for n in names if n]

    name = first_name(text)
    return [name] if name else []


def build_ingredient_table(recipes: pd.DataFrame) -> pd.DataFrame:
    """One row per normalized ingredient: recipe_id, line_no, raw, name.

    The raw line is kept next to its name so every normalization can be
    traced back. A recipe may list the same name twice (e.g. butter for crust
    and filling); `is_duplicate` marks repeats so counts per recipe can use
    unique names.
    """
    rows = []
    for recipe_id, lines in zip(recipes["recipe_id"], recipes["ingredients"]):
        seen = set()
        for line_no, raw in enumerate(lines):
            for name in normalize_ingredient(raw):
                rows.append({"recipe_id": recipe_id, "line_no": line_no,
                             "raw": raw, "name": name,
                             "is_duplicate": name in seen})
                seen.add(name)
    return pd.DataFrame(rows, columns=["recipe_id", "line_no", "raw", "name",
                                       "is_duplicate"])
