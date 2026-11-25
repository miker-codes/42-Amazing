*This project has been created as part of the 42 curriculum by mruiz-ra, blromero.*

# A-Maze-ing

## Description

A-Maze-ing is a maze generator written in Python. It reads a configuration
file, generates a maze, writes it to a file using a hexadecimal wall
encoding, and shows it in the terminal with an interactive menu.

It can build two kinds of mazes:

- **Perfect maze** (`PERFECT=True`): exactly one path between any two cells,
  with no loops.
- **Pac-Man board** (`PERFECT=False`, the default): every corridor is
  reachable, there are many independent routes (loops) and no dead-end, so
  it can be used directly as a level for a Pac-Man-like game.

Every maze contains a "42" drawn with fully closed cells, and the
generation is reproducible with a seed. The generator itself lives in a
standalone, pip-installable package (`mazegen`) so it can be reused in a
later project.

## Instructions

Requirements: Python 3.10 or later. The program only uses the standard
library, so it runs without installing anything:

```
python3 a_maze_ing.py config.txt
```

The `Makefile` automates the rest (it creates a virtual environment in
`.venv/`):

| Rule | What it does |
|---|---|
| `make install` | Create `.venv`, install the dev tools (flake8, mypy, build) and `mazegen` |
| `make run` | Run the program with `config.txt` |
| `make debug` | Run it under `pdb` |
| `make lint` | `flake8 .` + `mypy .` with the flags required by the subject |
| `make lint-strict` | `flake8 .` + `mypy . --strict` |
| `make package` | Rebuild `mazegen-1.0.0-py3-none-any.whl` and `.tar.gz` at the root |
| `make clean` | Remove caches and build leftovers |

### Interactive menu

After generating, the maze is drawn in the terminal (walls as coloured
blocks, entry in magenta, exit in red, "42" in grey) with this menu:

```
1. Re-generate a new maze      (random, and re-writes the output file)
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Quit
```

### Output file

One hexadecimal digit per cell, one row per line. Each digit encodes the
**closed** walls of the cell: bit 0 = North, 1 = East, 2 = South,
3 = West (e.g. `9` = North + West closed, `f` = fully closed). After an
empty line come the entry `x,y`, the exit `x,y` and the shortest path from
entry to exit as `N`/`E`/`S`/`W` letters. Every line ends with `\n`.

The file can be checked with the analysis script provided with the
subject: `python3 maze_analyzer.py maze.txt`.

## Configuration file

One `KEY=VALUE` pair per line. Empty lines and lines starting with `#` are
ignored. Spaces around the key and the value are allowed.

| Key | Mandatory | Format | Example |
|---|---|---|---|
| `WIDTH` | yes | positive integer (cells) | `WIDTH=20` |
| `HEIGHT` | yes | positive integer (cells) | `HEIGHT=15` |
| `ENTRY` | yes | `x,y` inside the maze (x = column, y = row, `0,0` = top-left) | `ENTRY=0,0` |
| `EXIT` | yes | `x,y` inside the maze, different from `ENTRY` | `EXIT=19,14` |
| `OUTPUT_FILE` | yes | path of the output file | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | yes | `True` or `False` (any case) | `PERFECT=False` |
| `SEED` | no | integer; same seed = same maze, no seed = a new maze each run | `SEED=42` |

If a key appears twice, the last value is used. Any error (file not found,
line without `=`, missing key, non-integer value, coordinates out of the
maze, `ENTRY` equal to `EXIT` or inside the "42") stops the program with a
clear message and exit code 1. If the maze is smaller than 9x7 the "42" is
left out and a warning is printed; if it is too small to hold 2 loops in
Pac-Man mode (2x1, 2x2) a warning is printed too.

The default configuration is `config.txt`.

## Maze generation algorithm

1. **Perfect maze: randomized recursive backtracker** (iterative, with a
   stack). Starting from the entry, it moves to a random unvisited
   neighbour, removing the wall between them, and pushes it on the stack;
   when the current cell has no unvisited neighbour it pops the stack
   (backtracks). It stops when the stack is empty, which means every cell
   was visited. Since it only ever opens a wall towards an unvisited cell,
   the result is a spanning tree: fully connected and without any loop.
2. **"42" pattern**: a 7x5 drawing centred in the grid. Its cells are
   marked as visited before carving, so the backtracker never opens them
   and they stay fully closed.
3. **Pac-Man board** (only when `PERFECT=False`): starting from the perfect
   maze, every dead-end (a cell with 3 closed walls) gets one more wall
   opened towards a non-"42" neighbour ("braiding"). Each opening creates a
   loop. An opening that would leave a 3x3 open area is undone and another
   wall is tried. Very small mazes that end up with fewer than 2 loops get
   extra random walls opened until they have 2.
4. **Shortest path: breadth-first search** from the entry through open
   walls, recording where each cell was reached from, then walking that
   back from the exit.

### Why this algorithm

- The recursive backtracker is simple to write and to explain (a stack and
  a visited set), and it is easy to make reproducible with a seed.
- It produces long, winding corridors with relatively few dead-ends, which
  suits the perfect mode and leaves little work for the braiding step.
- Kruskal's and Prim's algorithms were considered: they also give perfect
  mazes, but need an extra data structure (union-find, frontier set) and
  give many short dead-ends.
- Braiding on top of the perfect maze reuses the same code for both modes:
  the Pac-Man board is "the perfect maze plus a few walls removed".

## Reusable part: `mazegen`

The whole generator (generation, "42" pattern, Pac-Man mode, solver) is the
`mazegen` package, in the `mazegen/` folder. It does not depend on the rest
of the project (config file, output format, display). It is packaged as
`mazegen-1.0.0-py3-none-any.whl` at the root of the repository, and can be
rebuilt from the sources with `make package` (or `python -m build`).

Install it in any project:

```
pip install mazegen-1.0.0-py3-none-any.whl
```

### Basic example

```python
from mazegen import Direction, MazeGenerator

gen = MazeGenerator(width=20, height=15, entry=(0, 0), exit=(19, 14),
                    perfect=True)
gen.generate(seed=42)
path = gen.shortest_path()      # [Direction.EAST, Direction.SOUTH, ...]
```

### Custom parameters

| Parameter | Meaning |
|---|---|
| `width`, `height` | Size of the maze, in cells |
| `entry`, `exit` | `(x, y)` cells: x is the column, y the row, `(0, 0)` is the top-left corner |
| `perfect` | `True`: exactly one path between two cells. `False`: Pac-Man board |
| `seed` (argument of `generate()`) | Same integer = same maze; `None` (default) = a new maze each call |

Invalid parameters raise `ValueError`.

### Accessing the generated structure and a solution

| Attribute / method | Content |
|---|---|
| `gen.grid[row][col]` | The **closed** walls of that cell as a `Direction` flag (an int from 0 to 15: bit 0 = N, 1 = E, 2 = S, 3 = W). `gen.grid[0][0] & Direction.NORTH` is true when the cell has a north wall |
| `gen.pattern` | Set of `(row, col)` cells of the "42" (empty if the maze is smaller than 9x7) |
| `gen.entry`, `gen.exit` | Entry and exit as `(row, col)` (same order as `gen.grid`) |
| `gen.shortest_path()` | The moves from entry to exit, as a list of `Direction` |
| `gen.count_loops()` | Number of independent loops (at least `MIN_LOOPS` = 2 in Pac-Man mode) |

## Advanced features

- **No dead-end at all in Pac-Man mode** (bonus): the braided board passes
  `python3 maze_analyzer.py maze.txt --max-dead-ends 0`.
- **Reproducible generation** with the optional `SEED` key.
- Terminal display with colours, path toggle and wall colour rotation.

## Resources

- Jamis Buck, *Mazes for Programmers* (2015), and his blog series on maze
  algorithms: <https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap>
- Wikipedia, *Maze generation algorithm*:
  <https://en.wikipedia.org/wiki/Maze_generation_algorithm>
- Walter D. Pullen, *Think Labyrinth* (maze classification, braid mazes):
  <https://www.astrolog.org/labyrnth/algrithm.htm>
- Wikipedia, *Breadth-first search*:
  <https://en.wikipedia.org/wiki/Breadth-first_search>
- Python documentation: `random`, `enum.IntFlag`, `dataclasses`,
  `collections.deque`: <https://docs.python.org/3/>
- Python Packaging User Guide: <https://packaging.python.org/>
- PEP 8 and PEP 257 (style and docstrings).
- ANSI escape codes for terminal colours:
  <https://en.wikipedia.org/wiki/ANSI_escape_code>
- MIT License: <https://choosealicense.com/licenses/mit/>

### How AI was used

We used an AI assistant (Claude) as a tutor throughout the project:
explaining concepts (bit flags, stacks and queues, BFS, packaging, mypy
errors), proposing design options with their pros and cons so that we could
choose, reviewing our code, and testing it (running `maze_analyzer.py` on
hundreds of generated mazes, edge-case configuration files, lint).

Some parts of the code were written by the AI at our explicit request:
the "42" pattern, the BFS solver, the output writer, the CLI wiring, the
terminal display and menu, the Pac-Man braiding and the 2-loop guarantee,
and the packaging setup. Every one of them was then reviewed and explained
line by line until we could defend it; where a construct was hard to read
(list comprehensions in the output writer, for example) it was rewritten
in a simpler form. The configuration parser, the entry point and the core
of the maze generator were written by us with the AI's guidance. The final
design choices (algorithm, data structures, error handling) are ours.

## Project management

- **Team and roles**: mruiz-ra and blromero. We did not split the project
  into separate parts: we worked on every part together (design, maze
  generator, configuration and output, display and menu, packaging,
  testing and documentation), so that both of us can explain and modify
  any part of the code.
- **Planning and how it evolved**: the initial plan was config parsing ->
  perfect maze -> "42" -> Pac-Man mode -> output file -> display ->
  packaging.
  Along the way the order changed: the shortest path, the output file and
  the display were done before the Pac-Man mode, so that every later change
  could be seen and checked with `maze_analyzer.py` straight away. Testing
  against the analyzer also revealed late that very small Pac-Man mazes
  could end up with a single loop, which led to the 2-loop guarantee.
- **What worked well**: using `(row, col)` inside the generator with a
  single conversion from the subject's `(x, y)`, and a wall encoding
  (`IntFlag`) identical to the output format; validating every change with
  the provided `maze_analyzer.py` over many seeds and sizes.
- **What could be improved**: real unit tests (pytest), a graphical display
  with MiniLibX, and more generation algorithms.
- **Tools**: Python 3.10, venv, flake8, mypy, setuptools/build, Git and
  GitHub, VS Code, Claude Code.
