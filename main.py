"""Entry point: python main.py [--debug]"""
import sys

from recipe_bot.chat import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
