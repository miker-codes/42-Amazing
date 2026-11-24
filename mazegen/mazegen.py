"""mazegen - reusable grid maze generator and solver.

This module is the standalone, pip-installable part of A-Maze-ing: it knows
nothing about config files, output file formats, or terminal rendering. It
only knows how to build a grid of cells with walls and how to find a path
through it, so a later project can reuse it as it is.

Basic example::

    from mazegen import Direction, MazeGenerator

    gen = MazeGenerator(width=20, height=15, entry=(0, 0), exit=(19, 14),
                        perfect=True)
    gen.generate(seed=42)
    path = gen.shortest_path()      # [Direction.EAST, Direction.SOUTH, ...]

Custom parameters:
    width, height   Size of the maze, in cells.
    entry, exit     (x, y) cells: x is the column, y the row, (0, 0) is the
                    top-left corner. They must be different and inside the
                    maze (and not on the "42" drawing).
    perfect         True: exactly one path between any two cells (no loop).
                    False: Pac-Man board (loops, no dead-end, no 3x3 open
                    area).
    seed            Argument of generate(): the same int always gives the
                    same maze; None (the default) gives a new one each time.
    Invalid parameters raise ValueError.

Generated structure:
    gen.grid[row][col]  The CLOSED walls of that cell, as a Direction flag
                        (an int from 0 to 15): bit 0 = North, 1 = East,
                        2 = South, 3 = West. For instance
                        ``gen.grid[0][0] & Direction.NORTH`` is true when
                        the cell has a north wall.
    gen.pattern         Set of (row, col) cells drawing the "42" (fully
                        closed). Empty if the maze is smaller than 9x7.
    gen.entry, gen.exit The entry/exit as (row, col) - the internal order,
                        same as gen.grid[row][col].

Solution:
    gen.shortest_path() returns the moves from entry to exit as a list of
    Direction (breadth-first search), or [] if generate() was not called.

Pac-Man mode check:
    gen.count_loops() returns the number of independent loops (routes);
    a Pac-Man board needs at least MIN_LOOPS (2). Mazes too small to hold
    them (2x1, 2x2) get as many as fit.
"""

import random
from collections import deque
from enum import IntFlag

Cell = tuple[int, int]  # (row, col): same order as grid[row][col]


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


_ALL_WALLS = (
    Direction.NORTH | Direction.EAST | Direction.SOUTH | Direction.WEST
)

# Pac-Man mode: independent routes the board must offer (subject: "at least
# two independent routes").
MIN_LOOPS = 2

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
                raise ValueError(
                    f"{name} {x},{y} is outside the {width}x{height} maze"
                )
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
        if not self.perfect:
            self._braid()
            self._add_loops(MIN_LOOPS)

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
        return [
            [_ALL_WALLS for _ in range(self.width)]
            for _ in range(self.height)
        ]

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
        """Neighbours of *cell* inside the grid, with the Direction to each."""
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

    def _close(
        self, cell: Cell, neighbour: Cell, direction: Direction
    ) -> None:
        """Rebuild the wall between two adjacent cells (undoes _open)."""
        cr, cc = cell
        nr, nc = neighbour
        self.grid[cr][cc] |= direction
        self.grid[nr][nc] |= _OPPOSITE[direction]

    def _braid(self) -> None:
        """Pac-Man mode: give every dead-end a second way out.

        A dead-end is a cell with 3 closed walls. Opening one more of its
        walls joins it to a corridor it was not connected to, which creates
        a loop. An opening is undone if it would leave a 3x3 open area.
        Dead-ends whose closed walls only face the border or the "42" are
        left as they are (nothing can be opened there).
        """
        for row in range(self.height):
            for col in range(self.width):
                cell = (row, col)
                if cell in self.pattern or not self._is_dead_end(cell):
                    continue
                options = [
                    (neighbour, direction)
                    for neighbour, direction in self._neighbours(cell)
                    if self.grid[row][col] & direction
                    and neighbour not in self.pattern
                ]
                self._rng.shuffle(options)
                for neighbour, direction in options:
                    self._open(cell, neighbour, direction)
                    if not self._has_open_3x3(cell):
                        break
                    self._close(cell, neighbour, direction)

    def count_loops(self) -> int:
        """Independent loops of the maze (ignoring the "42" cells).

        A perfect maze (a tree) with N cells has exactly N - 1 passages;
        every passage on top of that closes one loop. Only the East and
        South walls of each cell are looked at, so each passage is counted
        once.
        """
        cells = 0
        passages = 0
        for row in range(self.height):
            for col in range(self.width):
                if (row, col) in self.pattern:
                    continue
                cells += 1
                if not self.grid[row][col] & Direction.EAST:
                    passages += 1
                if not self.grid[row][col] & Direction.SOUTH:
                    passages += 1
        return passages - (cells - 1)

    def _add_loops(self, wanted: int) -> None:
        """Open random extra walls until the maze has *wanted* loops.

        Only needed for very small mazes, where _braid() may find too few
        dead-ends to create enough loops. Walls towards the "42" or that
        would leave a 3x3 open area are not opened. If the maze is too
        small to hold *wanted* loops, it just opens what it can.
        """
        loops = self.count_loops()
        if loops >= wanted:
            return
        walls = []
        for row in range(self.height):
            for col in range(self.width):
                cell = (row, col)
                for neighbour, direction in self._neighbours(cell):
                    if direction not in (Direction.EAST, Direction.SOUTH):
                        continue
                    if not self.grid[row][col] & direction:
                        continue
                    if cell in self.pattern or neighbour in self.pattern:
                        continue
                    walls.append((cell, neighbour, direction))
        self._rng.shuffle(walls)
        for cell, neighbour, direction in walls:
            if loops >= wanted:
                return
            self._open(cell, neighbour, direction)
            if self._has_open_3x3(cell):
                self._close(cell, neighbour, direction)
            else:
                loops += 1

    def _is_dead_end(self, cell: Cell) -> bool:
        """True if *cell* has exactly 3 closed walls (a single way out)."""
        row, col = cell
        closed = 0
        for direction in Direction:
            if self.grid[row][col] & direction:
                closed += 1
        return closed == 3

    def _has_open_3x3(self, cell: Cell) -> bool:
        """True if some 3x3 square containing *cell* has no inner wall.

        The subject forbids open areas wider than 2 cells. Checking the
        squares around the cell just opened is enough: any new open square
        must contain the wall that was just removed.
        """
        row, col = cell
        for top in range(row - 2, row + 1):
            for left in range(col - 2, col + 1):
                if self._is_open_square(top, left):
                    return True
        return False

    def _is_open_square(self, top: int, left: int) -> bool:
        """True if the 3x3 square whose top-left cell is (top, left) exists
        and has every inner wall open."""
        if top < 0 or left < 0:
            return False
        if top + 3 > self.height or left + 3 > self.width:
            return False
        for row in range(top, top + 3):
            for col in range(left, left + 3):
                walls = self.grid[row][col]
                if col < left + 2 and walls & Direction.EAST:
                    return False
                if row < top + 2 and walls & Direction.SOUTH:
                    return False
        return True

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
