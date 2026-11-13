import pytest

from recipe_bot.quantities import Quantity, parse_quantity, sufficiency, total_quantity


@pytest.mark.parametrize("line,value,dim", [
    ("1 1/2 pounds chicken breasts ADVERTISEMENT", 680.388, "mass"),
    ("500g chicken", 500, "mass"),
    ("2 (14.5 ounce) cans diced tomatoes", 822.136, "mass"),
    ("1 (28 ounce) can crushed tomatoes", 793.786, "mass"),
    ("2 cups all-purpose flour", 473.176, "volume"),
    ("1/4 teaspoon salt", 1.232, "volume"),
    ("2 to 3 tablespoons olive oil", 44.360, "volume"),          # range -> upper end
    ("8 fl oz chicken broth", 236.588, "volume"),
    ("3 large eggs", 3, "count"),
    ("½ onion, chopped", 0.5, "count"),
    ("1½ cups milk", 354.882, "volume"),
    ("two eggs", 2, "count"),
    ("2 cloves garlic, minced", 2, "clove"),
    ("1 stick butter", 1, "stick"),
])
def test_parse_quantity(line, value, dim):
    q = parse_quantity(line)
    assert q is not None and q.dimension == dim
    assert q.value == pytest.approx(value, rel=1e-3)


@pytest.mark.parametrize("line", [
    "salt and pepper to taste", "Kosher salt", "1 pinch nutmeg", "1 (1 inch) piece ginger",
    "ADVERTISEMENT", "3", "2 inch piece ginger",
])
def test_no_reliable_quantity(line):
    assert parse_quantity(line) is None


def test_total_sums_same_dimension_only():
    q = total_quantity(["1/2 cup butter", "2 tablespoons butter"])
    assert q.dimension == "volume" and q.value == pytest.approx(118.294 + 29.574, rel=1e-3)
    assert total_quantity(["1 stick butter", "2 tablespoons butter"]) is None   # stick vs volume
    assert total_quantity(["butter, for the pan", "1/2 cup butter"]) is None


def test_sufficiency_compares_only_like_with_like():
    have = parse_quantity("2 lb chicken")
    assert sufficiency(have, parse_quantity("1 1/2 pounds chicken")).startswith("enough")
    assert sufficiency(parse_quantity("500 g chicken"), parse_quantity("2 pounds chicken")) \
        .startswith("not enough")
    assert sufficiency(parse_quantity("3 eggs"), parse_quantity("2 large eggs")).startswith("enough")
    assert "different kinds of measure" in sufficiency(parse_quantity("500 g flour"),
                                                       parse_quantity("2 cups flour"))
    assert "you gave no amount" in sufficiency(None, parse_quantity("2 eggs"))
    assert "recipe amount missing" in sufficiency(Quantity(3, "count", "3"), None)
