"""Conversation state for one chat session. Deterministic: no LLM here.

The LLM turns each user message into a TurnIntent (intent.py). This module
applies it to the session with fixed rules, so how restrictions persist can
be tested and explained:

  - Exclusions, the step limit and the source filter are hard constraints:
    they stay active across turns and topics until the user removes them.
  - The dish/keyword text and the "must include" ingredients belong to the
    current topic: a new topic replaces them ("now show me soups").
  - Without a new topic, the turn refines the active search.
  - "reset" clears everything.

Every answer prints the active constraints, so nothing applies silently.
"""

from dataclasses import dataclass, field

from .intent import TurnIntent
from .normalizer import normalize_ingredient
from .search import SearchQuery


def add_unique(items: list[str], new: list[str]) -> list[str]:
    """Append new terms (lowercased, trimmed) that are not already present."""
    out = list(items)
    for term in new:
        term = term.strip().lower()
        if term and term not in out:
            out.append(term)
    return out


def ingredient_key(said: str) -> str:
    names = normalize_ingredient(said)
    return names[0] if names else said.strip().lower()


def update_have(have: list[str], add: list[str], remove: list[str], replace: bool) -> list[str]:
    """The user's ingredients, kept as they said them ("2 lb chicken"). A newer entry for
    the same ingredient replaces the older one; removal matches by normalized name."""
    out = [] if replace else list(have)
    gone = {ingredient_key(r) for r in remove}
    out = [h for h in out if ingredient_key(h) not in gone]
    for said in add:
        key = ingredient_key(said)
        out = [h for h in out if ingredient_key(h) != key] + [said.strip()]
    return out


def remove_terms(items: list[str], gone: list[str]) -> list[str]:
    gone = {g.strip().lower() for g in gone}
    return [i for i in items if i not in gone]


@dataclass
class Session:
    text: str = ""
    title_only: bool = False
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    max_steps: int | None = None
    sources: list[str] = field(default_factory=list)
    expansions: dict[str, list[str]] = field(default_factory=dict)  # "dairy" -> [milk, ...]
    have: list[str] = field(default_factory=list)                   # pantry for matching
    assume_staples: bool = True
    last_ids: list[str] = field(default_factory=list)               # last results shown, in order
    last_recipe: str | None = None                                  # last recipe opened
    last_substitution: dict | None = None                           # recipe, target, options

    def query(self, limit: int = 10) -> SearchQuery:
        return SearchQuery(text=self.text, title_only=self.title_only,
                           include=list(self.include), exclude=list(self.exclude),
                           max_steps=self.max_steps, sources=list(self.sources), limit=limit)

    def describe(self) -> str:
        """Active search and constraints, in one line for every answer."""
        parts = []
        if self.text:
            parts.append(f'search "{self.text}"' + (" (titles only)" if self.title_only else ""))
        if self.include:
            parts.append("must include: " + ", ".join(self.include))
        if self.exclude:
            parts.append("excluded: " + ", ".join(self.exclude))
        if self.max_steps is not None:
            parts.append(f"at most {self.max_steps} steps")
        if self.sources:
            parts.append("sources: " + ", ".join(self.sources))
        if self.have:
            parts.append("your ingredients: " + ", ".join(self.have))
        return "; ".join(parts) or "no filters"

    # ---------- applying an intent ----------

    def apply(self, intent: TurnIntent) -> None:
        """Update the state from one parsed turn."""
        if intent.action == "reset":
            self.__init__()
            return
        if intent.action not in ("search", "stats", "match"):
            return                                   # show_recipe, help, ... change nothing
        if intent.action == "match":
            self.have = update_have(self.have, intent.add_have, intent.remove_have,
                                    intent.replace_have)
            if intent.assume_staples is not None:
                self.assume_staples = intent.assume_staples

        if intent.new_topic:
            self.text = intent.text or ""
            self.title_only = bool(intent.title_only)
            self.include = []
        elif intent.text is not None:
            self.text = intent.text
        if intent.title_only is not None:
            self.title_only = intent.title_only

        self.include = add_unique(remove_terms(self.include, intent.remove_include),
                                  intent.add_include)
        self.apply_exclusions(intent)

        if intent.clear_max_steps:
            self.max_steps = None
        if intent.max_steps is not None:
            self.max_steps = intent.max_steps
        if intent.sources is not None:
            self.sources = list(intent.sources)

    def apply_exclusions(self, intent: TurnIntent) -> None:
        """Exclusions, including category expansions ("dairy" -> milk, butter, ...).
        Removing a category removes every term it was expanded to."""
        removed = []
        for term in intent.remove_exclude:
            term = term.strip().lower()
            removed += [term] + self.expansions.pop(term, [])
        self.exclude = remove_terms(self.exclude, removed)

        for exp in intent.exclusion_expansions:
            category = exp.category.strip().lower()
            terms = add_unique([], exp.terms)
            self.expansions[category] = terms
            self.exclude = add_unique(self.exclude, terms)
        self.exclude = add_unique(self.exclude, intent.add_exclude)
