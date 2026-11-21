#!/usr/bin/env python3
"""mazegen - reusable grid maze generator and solver.

This module is the standalone, pip-installable part of A-Maze-ing: it knows
nothing about config files, output file formats, or terminal rendering. It
only knows how to build a grid of cells with walls and how to find a path
through it, so a later project can simply::

    from mazegen import MazeGenerator

and build its own generator on top of it.

TODO (together):
* Non-perfect (Pac-Man) mode: generate() currently always produces a perfect
  maze, regardless of self.perfect.
* The "42" pattern and the no-3x3-open-area rule.
* Read back a solution path (shortest path) from the outside.
"""

import random
from enum import IntFlag

Cell = tuple[int, int]  # (row, col): internal convention, matches grid[row][col]


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

_STEP: dict[Direction, Cell] = {
    Direction.NORTH: (-1, 0),
    Direction.EAST: (0, 1),
    Direction.SOUTH: (1, 0),
    Direction.WEST: (0, -1),
}
_OPPOSITE: dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
}


class MazeGenerator:
    """Builds a maze on a rectangular grid of cells.

    Attributes:
        width: maze width, in cells.
        height: maze height, in cells.
        entry: (row, col) of the entry cell.
        exit: (row, col) of the exit cell.
        perfect: True for a single-path maze, False for a playable board.
        grid: grid[row][col] holds the closed walls of that cell. Every
            cell starts fully closed; generate() carves passages into it.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit: tuple[int, int],
        perfect: bool,
    ) -> None:
        """Validate the parameters and allocate a fully-walled grid.

        Args:
            width: maze width, in cells.
            height: maze height, in cells.
            entry: (x, y) of the entry cell, the subject's convention.
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
        self.entry: Cell = (entry[1], entry[0])  # (x, y) -> (row, col)
        self.exit: Cell = (exit[1], exit[0])
        self.perfect = perfect
        self.grid: list[list[Direction]] = self._blank_grid()
        self._rng = random.Random()

    def generate(self, seed: int | None = None) -> None:
        """(Re)generate the maze, replacing any previous result.

        Args:
            seed: RNG seed for a reproducible maze. ``None`` means "pick an
                unpredictable one" (a fresh maze each call).
        """
        self._rng = random.Random(seed)
        self.grid = self._blank_grid()
        self._carve(self.entry)

    def _blank_grid(self) -> list[list[Direction]]:
        """Return a new grid of self.height x self.width, fully walled."""
        return [[_ALL_WALLS for _ in range(self.width)] for _ in range(self.height)]

    def _neighbours(self, cell: Cell) -> list[tuple[Cell, Direction]]:
        """In-bounds neighbours of *cell*, each with the Direction to reach it."""
        row, col = cell
        result = []
        for direction in Direction:
            drow, dcol = _STEP[direction]
            neighbour = (row + drow, col + dcol)
            nrow, ncol = neighbour
            if 0 <= nrow < self.height and 0 <= ncol < self.width:
                result.append((neighbour, direction))
        return result

    def _open(self, cell: Cell, neighbour: Cell, direction: Direction) -> None:
        """Carve the passage between two adjacent cells, both sides at once."""
        cr, cc = cell
        nr, nc = neighbour
        self.grid[cr][cc] &= _ALL_WALLS ^ direction
        self.grid[nr][nc] &= _ALL_WALLS ^ _OPPOSITE[direction]

    def _carve(self, start: Cell) -> None:
        """Randomized recursive backtracker, iterative (stack-based)."""
        visited = {start}
        stack = [start]
        while stack:
            current = stack[-1]
            candidates = [
                (neighbour, direction)
                for neighbour, direction in self._neighbours(current)
                if neighbour not in visited
            ]
            if not candidates:
                stack.pop()
                continue
            neighbour, direction = self._rng.choice(candidates)
            self._open(current, neighbour, direction)
            visited.add(neighbour)
            stack.append(neighbour)
