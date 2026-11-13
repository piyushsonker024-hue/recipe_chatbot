"""Command-line chat loop.

    python main.py            chat
    python main.py --debug    also print each parsed intent (useful to show
                              exactly what the LLM extracted)

/state, /reset, /help and /quit are handled locally without calling the LLM.
"""

import argparse
import sys

from .answer import HELP, constraint_line, handle
from .intent import IntentParser, TurnIntent
from .substitution import search_web
from .session import Session
from .store import connect

LOCAL_COMMANDS = {"/state": "show_state", "/reset": "reset", "/help": "help"}


def last_titles(conn, session: Session) -> dict[str, str]:
    """Titles of the last results, so the parser can resolve 'the second one'."""
    if not session.last_ids:
        return {}
    marks = ",".join("?" * len(session.last_ids))
    rows = conn.execute(f"SELECT recipe_id, title FROM recipes WHERE recipe_id IN ({marks})",
                        session.last_ids)
    return {rid: title.strip() for rid, title in rows}


def turn(conn, session: Session, parser: IntentParser, message: str, debug: bool = False) -> str:
    """One chat turn: parse (LLM) -> apply + execute (code) -> reply."""
    command = message.strip().lower()
    if command in LOCAL_COMMANDS:
        return handle(conn, session, TurnIntent(action=LOCAL_COMMANDS[command]))
    intent = parser.parse(message, session, last_titles(conn, session))

    def web(title, target, sub):                 # only called when the user asks for it
        return search_web(parser.client, title, target, sub, parser.model)

    reply = handle(conn, session, intent, web=web)
    if debug and intent is not None:
        reply = "[intent] " + intent.model_dump_json(exclude_defaults=True) + "\n\n" + reply
    return reply


def main(argv: list[str] | None = None) -> int:
    args = argparse.ArgumentParser(description="Recipe chatbot").parse_known_args(argv)[1]
    debug = "--debug" in args
    conn = connect()
    try:
        parser = IntentParser()
    except Exception as e:     # missing key / SDK problem: fail with a clear message
        print(f"Could not start the language model client: {e}\n"
              "Set ANTHROPIC_API_KEY (see README).", file=sys.stderr)
        return 1
    session = Session()
    print(HELP + "\n")
    while True:
        try:
            message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not message:
            continue
        if message.lower() in ("/quit", "/exit"):
            break
        try:
            print("\nbot> " + turn(conn, session, parser, message, debug) + "\n")
        except Exception as e:  # keep the session alive on API/network errors
            print(f"\nbot> Something went wrong ({type(e).__name__}: {e}). "
                  f"Your filters are unchanged.\n{constraint_line(session)}\n")
    return 0
