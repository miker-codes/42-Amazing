#!/usr/bin/env python3
"""A-Maze-ing entry point: python3 a_maze_ing.py <config_file>."""

import sys

from app.config import ConfigError, load_config


def main() -> int:
    """Validate the command line and run the program.

    Returns:
        The process exit code: 0 on success, non-zero on error.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>", file=sys.stderr)
        return 1

    config_path = sys.argv[1]
    try:
        config = load_config(config_path)
    except OSError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except ConfigError as error:
        print(f"Invalid configuration: {error}", file=sys.stderr)
        return 1

    print(config)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # stay safe on any unexpected input
        print(f"Unexpected error: {error}", file=sys.stderr)
        sys.exit(1)
