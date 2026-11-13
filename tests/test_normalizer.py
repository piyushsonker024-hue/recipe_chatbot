import pandas as pd
import pytest

from recipe_bot.normalizer import (build_ingredient_table, clean_line,
                                   normalize_ingredient, singularize)

# (raw line from the dataset, expected names). Real lines from all three sources.
CASES = [
    # quantities, units, ad marker
    ("2 cups shredded mozzarella cheese ADVERTISEMENT", ["mozzarella cheese"]),
    ("1 1/2 teaspoons ground nutmeg ADVERTISEMENT", ["nutmeg"]),
    ("2 1/2 to 2 3/4 cups sugar, or to taste", ["sugar"]),
    ("2 8-ounce packages cream cheese, room temperature", ["cream cheese"]),
    ("1 (28 ounce) can stewed tomatoes, drained ADVERTISEMENT", ["stewed tomato"]),
    ("2/3 cup plus 2 tablespoons olive oil", ["olive oil"]),
    ("Four 6-ounce salmon fillets", ["salmon fillet"]),
    ("a 4 to 7 pound turkey, split", ["turkey"]),
    ('1 1" piece ginger, peeled', ["ginger"]),
    ("Two or three handfuls arugula", ["arugula"]),
    ("3 very ripe bananas, mashed", ["banana"]),
    # comma rule: leading descriptor list vs trailing prep
    ("4 skinless, boneless chicken breast halves ADVERTISEMENT", ["chicken breast half"]),
    ("1 onion, very thinly sliced", ["onion"]),
    ("1/4 cup (1/2 stick) unsalted butter, melted", ["butter"]),
    # or rule
    ("1 pound top round, sirloin or filet mignon", ["top round"]),
    ("2 tablespoon yellow or brown mustard", ["yellow mustard"]),
    ("1 can or jar (12 to 16 ounces) chickpeas, rinsed and drained", ["chickpea"]),
    # salt and pepper split, synonyms
    ("Kosher salt and freshly ground black pepper", ["salt", "black pepper"]),
    ("salt and pepper to taste ADVERTISEMENT", ["salt", "black pepper"]),
    ("3 tablespoons extra-virgin olive oil", ["olive oil"]),
    ("2 scallions, green part only, sliced", ["green onion"]),
    ("1/3 cup fresh basil leaves ADVERTISEMENT", ["basil"]),
    ("2 bay leaves", ["bay leaf"]),
    ("Confectioners' sugar, for dredging", ["powdered sugar"]),
    # special forms
    ("Juice of 1 lime", ["lime juice"]),
    ("3/4 cup half and half", ["half-and-half"]),
    # brand / parenthetical noise
    ("3/4 cup lemon-lime soda (e.g. 7-Up™) ADVERTISEMENT", ["lemon-lime soda"]),
    ("1 (16 ounce) jar four-cheese Alfredo sauce (such as Classico®)", ["four-cheese alfredo sauce"]),
    # labels and junk tokens
    ("Accompaniment: jasmine rice", ["jasmine rice"]),
    ("+ 2 tablespoons butter", ["butter"]),
    ("? cups flour", ["flour"]),
    ("Additional all-purpose flour, for dusting", ["flour"]),
    # not ingredients
    ("ADVERTISEMENT", []),
    ("For the filling:", []),
    ("Special equipment: a 9-inch springform pan", []),
]


@pytest.mark.parametrize("raw,expected", CASES)
def test_normalize_ingredient(raw, expected):
    assert normalize_ingredient(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("2 tablespoons creamy peanut butter", ["creamy peanut butter"]),
    ("1 cup buttermilk", ["buttermilk"]),
    ("1 pound ground beef ADVERTISEMENT", ["ground beef"]),
    ("1 teaspoon ground cinnamon", ["cinnamon"]),
    ("1 tablespoon dried basil", ["dried basil"]),
    ("1 teaspoon ground cloves", ["clove"]),
    ("2 cloves garlic, minced", ["garlic"]),
])
def test_distinct_products_stay_distinct(raw, expected):
    """Removing whole words only: peanut butter is not butter, ground beef keeps 'ground'."""
    assert normalize_ingredient(raw) == expected


@pytest.mark.parametrize("word,expected", [
    ("tomatoes", "tomato"), ("berries", "berry"), ("peaches", "peach"),
    ("carrots", "carrot"), ("leaves", "leaf"), ("cloves", "clove"),
    ("molasses", "molasses"), ("asparagus", "asparagus"), ("hummus", "hummus"),
    ("grits", "grits"), ("swiss", "swiss"), ("egg", "egg"),
])
def test_singularize(word, expected):
    assert singularize(word) == expected


def test_clean_line_keeps_text_but_drops_marker():
    assert clean_line("1 cup water ADVERTISEMENT") == "1 cup water"
    assert clean_line("Sabra® Hummus") == "Sabra Hummus"


def test_build_ingredient_table_traces_raw_and_flags_duplicates():
    recipes = pd.DataFrame({
        "recipe_id": ["ar_1"],
        "ingredients": [["2 tbsp butter ADVERTISEMENT", "ADVERTISEMENT",
                         "Salt and pepper", "1/4 cup butter, melted"]],
    })
    table = build_ingredient_table(recipes)
    assert list(table["name"]) == ["butter", "salt", "black pepper", "butter"]
    assert list(table["line_no"]) == [0, 2, 2, 3]
    assert list(table["is_duplicate"]) == [False, False, False, True]
    assert table.iloc[0]["raw"] == "2 tbsp butter ADVERTISEMENT"   # original kept
