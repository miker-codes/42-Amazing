"""Writing the a_maze_ing output file.

Format (see subject IV.5): one hex digit per cell (bit0=N, bit1=E, bit2=S,
bit3=W, set = closed), one row per line, then a blank line, then entry
"x,y", exit "x,y" and the shortest path as N/E/S/W letters - each on its own
line. All lines end with '\\n'.

Note: the subject's illustrative screenshot shows "1,1   # entry (x,y)" but
that is just an annotation in the image, not literal file content - trailing
text after the coordinates would break maze_analyzer.py's parser (it does
``x_text, y_text = line.split(",")``, and "(x,y)" itself contains a comma).
The real footer lines must be plain "x,y".
"""

from app.config import Config
from mazegen import Direction, MazeGenerator

_LETTER: dict[Direction, str] = {
    Direction.NORTH: "N",
    Direction.EAST: "E",
    Direction.SOUTH: "S",
    Direction.WEST: "W",
}


def write_output(config: Config, generator: MazeGenerator) -> None:
    """Write the generated maze to config.output_file.

    Args:
        config: the run's configuration (output path, entry/exit as x,y).
        generator: a MazeGenerator on which generate() was already called.

    Raises:
        OSError: if the file cannot be written.
    """
    lines = ["".join(format(cell, "x") for cell in row)
             for row in generator.grid]
    lines.append("")
    lines.append(f"{config.entry[0]},{config.entry[1]}")
    lines.append(f"{config.exit[0]},{config.exit[1]}")
    lines.append("".join(_LETTER[d] for d in generator.shortest_path()))
    with open(config.output_file, "w", encoding="utf-8") as output_file:
        for line in lines:
            output_file.write(line + "\n")
