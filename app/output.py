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

TODO (phase 8): implement once the grid representation (phase 2) and
pathfinding (phase 7) exist.
"""

from __future__ import annotations
