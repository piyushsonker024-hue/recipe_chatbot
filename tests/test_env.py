import os

from recipe_bot.env import load_env, parse_env


def test_parse_env_formats():
    text = """
# a comment
GEMINI_API_KEY=abc123
export RECIPE_BOT_MODEL="gemini-x"
QUOTED='with spaces'
not a setting
EMPTY=
"""
    assert parse_env(text) == {"GEMINI_API_KEY": "abc123", "RECIPE_BOT_MODEL": "gemini-x",
                               "QUOTED": "with spaces", "EMPTY": ""}


def test_load_env_does_not_override_the_environment(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("RB_TEST_A=from_file\nRB_TEST_B=from_file\n")
    monkeypatch.setenv("RB_TEST_A", "from_shell")
    monkeypatch.delenv("RB_TEST_B", raising=False)
    assert load_env(env) == ["RB_TEST_B"]
    assert os.environ["RB_TEST_A"] == "from_shell" and os.environ["RB_TEST_B"] == "from_file"
    monkeypatch.delenv("RB_TEST_B")


def test_missing_file_is_fine(tmp_path):
    assert load_env(tmp_path / "nope.env") == []
