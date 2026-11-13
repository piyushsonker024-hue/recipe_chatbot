"""Parse one user message into a structured TurnIntent with Gemini.

This is the only place the LLM is used, and it only classifies and extracts:
it never answers, counts or names recipes. The response is constrained to
the TurnIntent schema (structured outputs, validated by Pydantic), so the
rest of the system receives typed fields, not free text.

Model: gemini-3.8-flash with low thinking (an extraction task). The reply is
constrained to TurnIntent's JSON schema and validated again with Pydantic.
API key: GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable.
Override the model with RECIPE_BOT_MODEL.
"""

import json
import os
from typing import Literal

from google.genai import types
from pydantic import BaseModel, Field, ValidationError

MODEL = os.environ.get("RECIPE_BOT_MODEL", "gemini-3.8-flash")

StatName = Literal[
    "count", "ingredient_share", "top_ingredients", "step_stats",
    "ingredient_count_stats", "fewest_steps", "most_steps",
    "fewest_ingredients", "most_ingredients",
]


class Expansion(BaseModel):
    category: str = Field(description="What the user said, e.g. 'dairy', 'nuts', 'meat'.")
    terms: list[str] = Field(description="Ingredient words that category covers, to exclude.")


class TurnIntent(BaseModel):
    action: Literal["search", "match", "show_recipe", "stats", "substitute", "reset",
                    "show_state", "unsupported", "help"]
    # --- search scope ---
    new_topic: bool = Field(False, description="True when the user starts a different dish or "
                            "question; replaces text and must-include ingredients.")
    text: str | None = Field(None, description="Dish name or keywords; null keeps the current text.")
    title_only: bool | None = Field(None, description="True for dish-type questions "
                                    "(cookies, lasagna), so instruction mentions do not count.")
    add_include: list[str] = Field(default_factory=list)
    remove_include: list[str] = Field(default_factory=list)
    # --- hard constraints (persist across turns) ---
    add_exclude: list[str] = Field(default_factory=list)
    remove_exclude: list[str] = Field(default_factory=list)
    exclusion_expansions: list[Expansion] = Field(default_factory=list)
    max_steps: int | None = None
    clear_max_steps: bool = False
    sources: list[Literal["ar", "epi", "fn"]] | None = None
    # --- ingredient matching (the user's pantry; persists across turns) ---
    add_have: list[str] = Field(default_factory=list, description="Ingredients the user has, "
                                "with amounts exactly as said, e.g. '2 lb chicken', 'rice'.")
    remove_have: list[str] = Field(default_factory=list)
    replace_have: bool = Field(False, description="True for 'I only have ...': replaces the list.")
    assume_staples: bool | None = Field(None, description="False if the user says they lack "
                                        "salt, pepper or water.")
    # --- show a recipe ---
    result_number: int | None = Field(None, description="1-based position in the last results.")
    recipe_id: str | None = None
    show: Literal["ingredients", "instructions", "both"] = "both"
    # --- substitution (uses result_number / recipe_id / the last recipe opened) ---
    sub_target: str | None = Field(None, description="Ingredient to replace, e.g. 'butter'.")
    sub_candidate: str | None = Field(None, description="Replacement the user proposes or "
                                      "picks from the last options; null to let the data decide.")
    use_web: bool = Field(False, description="True only if the user asks to search the web.")
    # --- statistics ---
    stat: StatName | None = None
    stat_term: str | None = Field(None, description="Ingredient for ingredient_share.")
    by_source: bool = False
    top_n: int | None = None
    stat_skip: list[str] = Field(default_factory=list)
    # --- cannot be answered from the data ---
    missing_attribute: str | None = Field(None, description="For 'unsupported': what the "
                                          "dataset lacks, e.g. 'nutrition', 'cooking time'.")


SYSTEM_PROMPT = """You convert one message from a recipe-chatbot user into a TurnIntent. You do not answer the user. Code runs the search and statistics over a dataset of 124,483 recipes (Allrecipes "ar", Epicurious "epi", Food Network "fn"), each with only a title, ingredient lines and instructions.

Actions:
- search: find recipes, or refine the active search (add/remove ingredients, exclusions, step limit).
- match: the user says what ingredients they have and wants recipes they can make ("I have chicken, rice and onions", "what can I cook with..."). Put each ingredient in add_have with its amount exactly as said. "I also have X" adds; "I ran out of X" / "I don't have X" goes in remove_have; "I only have ..." sets replace_have. Follow-ups that change constraints while matching ("no dairy", "under 4 steps") stay action match.
- show_recipe: the user wants ingredients or instructions of a recipe. Use result_number for "the second one" (1-based, from the last results) or recipe_id when given.
- substitute: replace an ingredient in a recipe ("no buttermilk, what can I use?", "can I use oil instead of butter?", "swap the eggs"). Set sub_target; set sub_candidate if the user names a replacement or picks one of the last options ("use the second one" -> that option's name from last_substitution); set use_web only when the user asks for web or online sources. The recipe is the one in result_number/recipe_id, else the last one opened.
- stats: counts, percentages, averages, medians, rankings ("how many", "what share", "most common", "average steps", "fewest steps").
- reset: start over and clear all filters. show_state: "what filters are on?". help: greetings or "what can you do".
- unsupported: the question needs data the dataset does not have (nutrition, calories, cooking or prep time, cost, cuisine labels, ratings, servings). Set missing_attribute. Never guess these.

Session rules:
- new_topic=true when the user moves to a different dish or question. It replaces text and must-include ingredients. Exclusions and the step limit stay unless the user removes them.
- Follow-ups such as "without nuts", "under 5 steps", "only Food Network" refine the active search: new_topic=false, text=null.
- For stats about the current results ("how many of these..."), keep new_topic=false. For stats about the whole dataset or another dish, new_topic=true and set text (or "" for everything).
- Set title_only=true when text names a dish type ("cookies", "lasagna", "banana bread"); false for ingredient-like or descriptive keywords.

Ingredients and exclusions:
- add_include: ingredients a searched recipe must contain. add_exclude: ingredients the recipe must not contain (allergies, dislikes). "I don't have X" is not an exclusion: it is remove_have.
- If the user excludes a category (dairy, nuts, tree nuts, shellfish, gluten, meat, pork, eggs), put it in exclusion_expansions with the ingredient words it covers (e.g. dairy: milk, butter, cheese, cream, yogurt, ghee, buttermilk, whey, sour cream). Be broad: over-excluding is safe. Do not also put the category word in add_exclude unless it appears in recipes itself (e.g. "pork" does).
- "vegetarian" means exclude meat, poultry, fish and shellfish: list cuts and products too (beef, pork, ham, bacon, sausage, pepperoni, salami, prosciutto, pancetta, chicken, turkey, duck, lamb, veal, fish, salmon, tuna, anchovy, shrimp, crab, lobster, clam, mussel, oyster, scallop, squid, gelatin, broth made from meat or fish). "vegan" also excludes dairy, eggs and honey.
- Use plain lowercase ingredient words without quantities.

The user message comes with the current session state and the last results as JSON. Use them to resolve "these", "it" and "the third one"."""


def build_context(session, titles: dict[str, str]) -> str:
    """Session state and last results, sent with each user message."""
    state = {
        "active_search": session.text, "title_only": session.title_only,
        "must_include": session.include, "excluded": session.exclude,
        "max_steps": session.max_steps, "sources": session.sources,
        "your_ingredients": session.have, "assume_staples": session.assume_staples,
        "last_results": [{"number": i + 1, "recipe_id": rid, "title": titles.get(rid, "")}
                         for i, rid in enumerate(session.last_ids)],
        "last_recipe_opened": session.last_recipe,
        "last_substitution": session.last_substitution,
    }
    return json.dumps(state, ensure_ascii=False)


class IntentParser:
    """Wraps the Gemini call. `client` is injectable so tests need no API key."""

    def __init__(self, client=None, model: str = MODEL):
        self.client = client if client is not None else make_client()
        self.model = model

    def parse(self, message: str, session, titles: dict[str, str]) -> TurnIntent | None:
        """Return the intent, or None if the model was blocked, cut off, or returned
        something that does not validate against TurnIntent."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"Session state:\n{build_context(session, titles)}\n\nUser message:\n{message}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_json_schema=TurnIntent.model_json_schema(),
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                max_output_tokens=8192,
            ),
        )
        if not finished(response):
            return None
        try:
            return TurnIntent.model_validate_json(response.text)
        except ValidationError:
            return None


def make_client():
    """Gemini client; reads GEMINI_API_KEY (or GOOGLE_API_KEY) from the environment."""
    from google import genai
    return genai.Client()


def finished(response) -> bool:
    """True if the model completed normally (not blocked by safety, not cut off)."""
    candidates = getattr(response, "candidates", None) or []
    return bool(candidates) and candidates[0].finish_reason == types.FinishReason.STOP \
        and bool(response.text)
