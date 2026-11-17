#!/usr/bin/env python3
"""mazegen - reusable grid maze generator and solver.

This module is the standalone, pip-installable part of A-Maze-ing: it knows
nothing about config files, output file formats, or terminal rendering. It
only knows how to build a grid of cells with walls and how to find a path
through it, so a later project can simply::

    from mazegen import MazeGenerator

and build its own generator on top of it.

TODO (phase 3 onward, together):
* Design and implement the generation algorithm itself (carve passages into
  the grid built below).
* Read back the grid and a solution path from the outside.
"""

from enum import IntFlag

Cell = tuple[int, int]  # (x, y): x = column index, y = row index


class Direction(IntFlag):
    """A wall side; the integer value is the bit used in a cell's walls.

    Matches the subject's output encoding (bit0=N, bit1=E, bit2=S, bit3=W),
    so a cell's wall mask can be written straight to the output file with no
    translation.
    """

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8


_ALL_WALLS = Direction.NORTH | Direction.EAST | Direction.SOUTH | Direction.WEST


class MazeGenerator:
    """Builds a maze on a rectangular grid of cells.

    Attributes:
        width: maze width, in cells.
        height: maze height, in cells.
        entry: (x, y) of the entry cell.
        exit: (x, y) of the exit cell.
        perfect: True for a single-path maze, False for a playable board.
        grid: grid[y][x] holds the closed walls of the cell at column x,
            row y. Every cell starts fully closed; carving passages (a
            later phase) clears bits as the generation algorithm runs.
    """

    def __init__(
        self, width: int, height: int, entry: Cell, exit: Cell, perfect: bool
    ) -> None:
        """Validate the parameters and allocate a fully-walled grid.

        Args:
            width: maze width, in cells.
            height: maze height, in cells.
            entry: (x, y) of the entry cell.
            exit: (x, y) of the exit cell.
            perfect: True for a single-path maze, False for a playable board.

        Raises:
            ValueError: if a parameter makes no sense (non-positive size,
                entry/exit out of bounds, or entry == exit).
        """
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        for name, (x, y) in (("entry", entry), ("exit", exit)):
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError(f"{name} {x},{y} is outside the {width}x{height} maze")
        if entry == exit:
            raise ValueError("entry and exit must be different cells")

        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.perfect = perfect
        self.grid: list[list[Direction]] = [
            [_ALL_WALLS for _ in range(width)] for _ in range(height)
        ]
