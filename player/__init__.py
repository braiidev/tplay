import curses
import sys

from .app import PlayerApp


def main() -> None:
    try:
        curses.wrapper(lambda stdscr: PlayerApp(stdscr).run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
