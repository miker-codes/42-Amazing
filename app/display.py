"""Terminal ASCII visualization and the interactive menu.

Required interactions (subject chapter V): re-generate and re-display,
show/hide the shortest path, change wall colours (optionally, colour the
"42" pattern separately).

How the drawing works: the maze is drawn on a "canvas" of blocks that is
(2 * height + 1) rows by (2 * width + 1) columns. Cell (row, col) sits on
block (2 * row + 1, 2 * col + 1); the blocks between two cells are the
walls between them; the blocks where four cells meet are always wall.
Each block is printed as two characters, so the maze looks square.
"""

from app.config import Config
from app.output import write_output
from mazegen import Direction, MazeGenerator

# ANSI escape codes: "\033[...m" changes the colour of what is printed
# after it, "\033[0m" goes back to normal.
_RESET = "\033[0m"
_CLEAR_SCREEN = "\033[2J\033[H"
_WALL_COLOURS = ("\033[97m", "\033[93m", "\033[92m", "\033[94m")
_COLOUR: dict[str, str] = {
    "path": "\033[96m",    # cyan
    "entry": "\033[95m",   # magenta
    "exit": "\033[91m",    # red
    "42": "\033[90m",      # grey
}
_BLOCK = "██"     # two full-block characters
_STEP: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (-1, 0),
    Direction.EAST: (0, 1),
    Direction.SOUTH: (1, 0),
    Direction.WEST: (0, -1),
}
_MENU = (
    "=== A-Maze-ing ===\n"
    "1. Re-generate a new maze\n"
    "2. Show / Hide the shortest path\n"
    "3. Rotate the wall colours\n"
    "4. Quit"
)


def render(generator: MazeGenerator, show_path: bool, wall_colour: str) -> str:
    """Draw the maze as coloured blocks.

    Args:
        generator: a MazeGenerator on which generate() was already called.
        show_path: whether to draw the shortest path from entry to exit.
        wall_colour: ANSI colour code used for the walls.

    Returns:
        The whole drawing, ready to print.
    """
    canvas = _build_canvas(generator, show_path)
    lines = []
    for canvas_row in canvas:
        line = ""
        for kind in canvas_row:
            if kind == "open":
                line += "  "
            elif kind == "wall":
                line += wall_colour + _BLOCK + _RESET
            else:
                line += _COLOUR[kind] + _BLOCK + _RESET
        lines.append(line)
    return "\n".join(lines)


def _build_canvas(
    generator: MazeGenerator, show_path: bool
) -> list[list[str]]:
    """Decide what each block of the drawing is: wall, open, path..."""
    canvas = [
        ["wall" for _ in range(2 * generator.width + 1)]
        for _ in range(2 * generator.height + 1)
    ]
    for row in range(generator.height):
        for col in range(generator.width):
            walls = generator.grid[row][col]
            if (row, col) in generator.pattern:
                canvas[2 * row + 1][2 * col + 1] = "42"
                continue
            canvas[2 * row + 1][2 * col + 1] = "open"
            if not walls & Direction.EAST:
                canvas[2 * row + 1][2 * col + 2] = "open"
            if not walls & Direction.SOUTH:
                canvas[2 * row + 2][2 * col + 1] = "open"

    if show_path:
        row, col = generator.entry
        for direction in generator.shortest_path():
            drow, dcol = _STEP[direction]
            # the block between the two cells, then the next cell itself
            canvas[2 * row + 1 + drow][2 * col + 1 + dcol] = "path"
            row, col = row + drow, col + dcol
            canvas[2 * row + 1][2 * col + 1] = "path"

    entry_row, entry_col = generator.entry
    exit_row, exit_col = generator.exit
    canvas[2 * entry_row + 1][2 * entry_col + 1] = "entry"
    canvas[2 * exit_row + 1][2 * exit_col + 1] = "exit"
    return canvas


def run_menu(config: Config, generator: MazeGenerator, message: str) -> None:
    """Show the maze and loop on the interactive menu until the user quits.

    Args:
        config: the run's configuration (needed to re-write the output
            file when a new maze is generated).
        generator: a MazeGenerator on which generate() was already called.
        message: a status line to show above the menu the first time.
    """
    show_path = False
    colour_index = 0
    while True:
        print(_CLEAR_SCREEN, end="")
        print(render(generator, show_path, _WALL_COLOURS[colour_index]))
        print(message)
        print(_MENU)
        try:
            choice = input("Choice? (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        message = ""
        if choice == "1":
            generator.generate()
            try:
                write_output(config, generator)
                message = f"New maze written to {config.output_file}"
            except OSError as error:
                message = f"Error: cannot write the output file: {error}"
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            colour_index = (colour_index + 1) % len(_WALL_COLOURS)
        elif choice == "4":
            return
        else:
            message = f"Invalid choice {choice!r}: type 1, 2, 3 or 4."
