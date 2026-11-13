"""Shared test database: 6 small recipes covering the search and stats edge cases."""
import json

import pytest

from recipe_bot.data_loader import SOURCE_FILES
from recipe_bot.store import build_db, connect

AR = {
    "bb1": {"title": "Classic Banana Bread",
            "ingredients": ["3 ripe bananas ADVERTISEMENT", "2 eggs ADVERTISEMENT",
                            "1/2 cup chopped walnuts ADVERTISEMENT", "2 cups all-purpose flour ADVERTISEMENT"],
            "instructions": "Mash bananas.\nMix everything.\nBake 1 hour.\n"},
    "bb2": {"title": "Vegan Banana Bread",
            "ingredients": ["3 bananas", "2 cups flour", "1/3 cup vegetable oil"],
            "instructions": "Mash bananas and mix with oil.\nBake."},
    "cs1": {"title": "Chicken Spinach Skillet",
            "ingredients": ["2 boneless chicken breasts", "4 cups fresh spinach", "1 tablespoon olive oil"],
            "instructions": "Cook chicken. Add spinach."},
}
EPI = {
    "soup": {"title": "Spinach Soup",
             "ingredients": ["1 quart chicken broth", "1 pound spinach", "1 tablespoon almond or peanut butter"],
             "instructions": "Simmer broth.\nAdd spinach.\nBlend.\nServe."},
    "fruit": {"title": "Bananas on Fruit Bread",
              "ingredients": ["2 bananas", "4 slices fruit bread"],
              "instructions": ""},
}
FN = {"pt": {"title": "Shrimp Pad Thai",
             "ingredients": ["8 ounces rice noodles", "1 pound shrimp", "1/4 cup chopped peanuts"],
             "instructions": "Soak noodles.\nStir-fry shrimp.\nToss with noodles and top with peanuts."}}


@pytest.fixture(scope="session")
def conn(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("db")
    for source, payload in {"ar": AR, "epi": EPI, "fn": FN}.items():
        (tmp / SOURCE_FILES[source]).write_text(json.dumps(payload))
    build_db(tmp / "test.db", tmp, cooccur_min=1)
    c = connect(tmp / "test.db")
    yield c
    c.close()

