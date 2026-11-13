"""Load settings such as GEMINI_API_KEY from a .env file in the project root.

Format: one KEY=value per line; blank lines and lines starting with # are
ignored; an optional "export " prefix and surrounding quotes are allowed.
A variable already set in the environment wins over the file, so
`export GEMINI_API_KEY=...` in the terminal still works. The .env file is
git-ignored, so the key never reaches the repository.
"""

import os
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def parse_env(text: str) -> dict[str, str]:
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.removeprefix("export ").split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_env(path: Path = ENV_FILE) -> list[str]:
    """Set variables from `path` that are not already set. Returns the names loaded."""
    if not path.is_file():
        return []
    loaded = []
    for key, value in parse_env(path.read_text()).items():
        if key and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded
