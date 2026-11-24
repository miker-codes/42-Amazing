"""mazegen - reusable grid maze generator and solver.

Usage::

    from mazegen import MazeGenerator

See mazegen/mazegen.py for the full documentation.
"""

from .mazegen import MIN_LOOPS, Cell, Direction, MazeGenerator

__all__ = ["MIN_LOOPS", "Cell", "Direction", "MazeGenerator"]
