"""Orchestration: config -> mazegen -> output file -> display + menu.

This is what a_maze_ing.py (the entry point) calls into, once the config
file has been loaded and validated.
"""

import sys

from app.config import Config
from app.display import run_menu
from app.output import write_output
from mazegen import MazeGenerator


def run(config: Config) -> int:
    """Generate the maze described by *config* and write the output file.

    Args:
        config: a fully validated configuration.

    Returns:
        The process exit code: 0 on success, non-zero on error.
    """
    try:
        generator = MazeGenerator(
            width=config.width,
            height=config.height,
            entry=config.entry,
            exit=config.exit,
            perfect=config.perfect,
        )
    except ValueError as error:
        print(f"Invalid configuration: {error}", file=sys.stderr)
        return 1

    generator.generate(config.seed)

    try:
        write_output(config, generator)
    except OSError as error:
        print(f"Error: cannot write the output file: {error}",
              file=sys.stderr)
        return 1

    message = f"Maze written to {config.output_file}"
    if not generator.pattern:
        # Shown under the maze, so the screen clearing doesn't hide it.
        message = (
            "Warning: the maze is too small for the '42' pattern "
            "(it needs at least 9x7 cells), so it was left out.\n" + message
        )
    run_menu(config, generator, message)
    return 0
