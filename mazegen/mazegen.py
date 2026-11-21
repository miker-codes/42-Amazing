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
* The no-3x3-open-area rule (only matters once loops are added).
"""

import random
from collections import deque
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

# The "42" drawing: each "X" is a fully closed cell. A "4" and a "2", each
# 3 cells wide, separated by an empty column. 7 wide x 5 tall.
_PATTERN_42 = (
    "X.X.XXX",
    "X.X...X",
    "XXX.XXX",
    "..X.X..",
    "..X.XXX",
)


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
        pattern: (row, col) cells of the "42" drawing, which stay fully
            closed. Empty if the maze is too small to fit it.
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
                entry/exit out of bounds, entry == exit, or entry/exit
                inside the "42" pattern).
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
        self.pattern: set[Cell] = self._pattern_cells()
        for name, (row, col) in (("entry", self.entry), ("exit", self.exit)):
            if (row, col) in self.pattern:
                raise ValueError(
                    f"{name} {col},{row} falls inside the '42' pattern"
                )
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

    def shortest_path(self) -> list[Direction]:
        """Find the shortest path from entry to exit (breadth-first search).

        Only reads the grid: it moves through open walls, never changes one.
        Call it after generate().

        Returns:
            The moves to follow from the entry, e.g. [EAST, SOUTH, ...].
            Empty if the exit cannot be reached (e.g. generate() was not
            called yet, so every wall is still closed).
        """
        came_from: dict[Cell, tuple[Cell, Direction]] = {}
        visited = {self.entry}
        queue = deque([self.entry])
        while queue:
            current = queue.popleft()
            if current == self.exit:
                return self._rebuild_path(came_from)
            row, col = current
            for neighbour, direction in self._neighbours(current):
                if neighbour in visited or self.grid[row][col] & direction:
                    continue
                visited.add(neighbour)
                came_from[neighbour] = (current, direction)
                queue.append(neighbour)
        return []

    def _rebuild_path(
        self, came_from: dict[Cell, tuple[Cell, Direction]]
    ) -> list[Direction]:
        """Walk came_from back from exit to entry, then reverse it."""
        path: list[Direction] = []
        cell = self.exit
        while cell != self.entry:
            cell, direction = came_from[cell]
            path.append(direction)
        path.reverse()
        return path

    def _blank_grid(self) -> list[list[Direction]]:
        """Return a new grid of self.height x self.width, fully walled."""
        return [[_ALL_WALLS for _ in range(self.width)] for _ in range(self.height)]

    def _pattern_cells(self) -> set[Cell]:
        """Cells of the "42" drawing, centred in the grid.

        The drawing needs a free margin of one cell all around, so it never
        touches the outer border (that could wall off a pocket of cells).

        Returns:
            The (row, col) cells to keep fully closed, or an empty set if
            the maze is too small to fit the drawing plus its margin.
        """
        rows = len(_PATTERN_42)
        cols = len(_PATTERN_42[0])
        if self.height < rows + 2 or self.width < cols + 2:
            return set()
        top = (self.height - rows) // 2
        left = (self.width - cols) // 2
        cells: set[Cell] = set()
        for r, line in enumerate(_PATTERN_42):
            for c, char in enumerate(line):
                if char == "X":
                    cells.add((top + r, left + c))
        return cells

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
        """Randomized recursive backtracker, iterative (stack-based).

        The "42" cells start out as already visited, so the backtracker
        never carves into them and they stay fully closed.
        """
        visited = {start} | self.pattern
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
