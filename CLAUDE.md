This file travels with the repo (unlike `~/.claude/CLAUDE.md`, which is
per-machine). Read it on any machine before doing anything else, together
with `NOTES.md` (its top section, "Dónde lo dejamos", is the current status).

# Project

A-Maze-ing, 42 Málaga, milestone 2 Python track. Student: mruiz-ra. Full
subject is `en.subject.pdf` at repo root — **gitignored on purpose**, so it
does not travel with `git clone`/`git pull`; it must be copied in separately
on each machine. `maze_analyzer.py` (also at root) is the grading/validation
script provided with the subject — treat it as a second source of truth
alongside the PDF whenever something is ambiguous.

# How to work with Mike (non-negotiable, carried over from his personal
# instructions)

- He has to explain every line of his own code in a peer/staff defense.
  **Do not write full solutions unprompted.** Act as a tutor: explain
  concepts, point out bugs, let him write the code himself. Only write code
  directly when he explicitly asks (e.g. "móntalo tú").
- Before writing code for an important design decision (data structures,
  the generation algorithm, non-perfect mode, the "42" pattern, pathfinding,
  packaging layout), present options with honest pros/cons and wait for his
  choice. Don't just pick silently.
- Go in small, checkable steps. After touching any file, run `flake8` and
  `mypy` (both the mandatory flags and `--strict`) on it and show the
  result — don't just claim it passes.
- When something doesn't land, don't just repeat the same explanation
  louder — find a different, more concrete angle (a tiny worked example by
  hand, a live one-liner demo, a closer analogy). He will tell you plainly
  when something isn't clicking; take it as a signal to change approach, not
  to simplify what you already said.
- Append every new concept explained to `NOTES.md` (one section per
  file/topic) — it's his personal revision doc for the defense, not part of
  the graded deliverable.
- He prioritizes **understanding and being able to defend every line** over
  speed or feature completeness. When in doubt, less code he can't explain
  beats more code he can't explain.

# Key decisions already locked in (don't re-litigate without reason)

- `Config` (app/config.py): a `@dataclass`, built by `load_config()`, which
  raises `ConfigError` on bad input. `a_maze_ing.py` catches `OSError` and
  `ConfigError` separately, plus a top-level `except Exception` safety net
  (same pattern as `maze_analyzer.py`'s own `__main__` block).
- `mazegen/mazegen.py` is standalone: it must never import from `app` (the
  reusable package can't depend on this project's own config format). Public
  API (constructor params) uses `(x, y)` like the subject and `Config`; the
  internal `Cell` type is `(row, col)`, matching `grid[row][col]` directly —
  one single swap happens at the top of `MazeGenerator.__init__`, nowhere
  else. Mirrors `maze_analyzer.py`'s own `Direction`/`Cell` approach.
- Maze generation algorithm: **recursive backtracker** (iterative, stack-
  based — chosen over Kruskal's/Prim's: no new data structure to learn,
  fewer natural dead-ends, which helps the non-perfect mode later).
- `Direction` is an `IntFlag` (bit0=N, bit1=E, bit2=S, bit3=W), matching the
  subject's output encoding exactly — no translation needed when writing the
  output file later.
- Tooling: Python 3.10 minimum (home machine is newer, campus may be older -
  never use 3.11+-only syntax). `.venv` via `make install` (Arch/PEP 668
  blocks bare `pip install`). Only add an import/concept when it's actually
  needed right now, not preemptively "for later".
