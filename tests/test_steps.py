import pytest

from recipe_bot.steps import count_steps, split_steps


@pytest.mark.parametrize("instructions,expected", [
    ("Mix flour and water.\nKnead.\nBake 20 minutes.\n", 3),   # ar style, trailing \n
    ("Preheat oven.\n\n\nBake.", 2),                            # blank lines ignored
    ("Whisk eggs. Add milk. Cook in a pan.", 1),                # one paragraph = 1 step
    ("  Stir.  \n   \n", 1),
    ("Stir.\nADVERTISEMENT", 1),
    ("", None),                                                 # unknown, not 0
    ("   \n  ", None),
    (None, None),
])
def test_count_steps(instructions, expected):
    assert count_steps(instructions) == expected


def test_split_steps_keeps_original_text():
    assert split_steps("  Boil water.\nAdd pasta, stir.") == ["Boil water.", "Add pasta, stir."]
