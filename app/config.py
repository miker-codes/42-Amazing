"""Parsing and validation of the a_maze_ing configuration file.

Mandatory keys per the subject: WIDTH, HEIGHT, ENTRY, EXIT, OUTPUT_FILE,
PERFECT. One KEY=VALUE pair per line, '#' starts a comment.
"""

from dataclasses import dataclass

_MANDATORY_KEYS = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT")


class ConfigError(Exception):
    """Raised when the configuration file is missing a key or is invalid."""


@dataclass
class Config:
    """A fully validated a_maze_ing configuration.

    Attributes:
        width: maze width, in cells.
        height: maze height, in cells.
        entry: (x, y) coordinates of the entry cell.
        exit: (x, y) coordinates of the exit cell.
        output_file: path where the maze output must be written.
        perfect: True for a single-path maze, False for a playable board.
    """

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool


def load_config(path: str) -> Config:
    """Read, parse and validate an a_maze_ing configuration file.

    Args:
        path: path to the config file.

    Returns:
        A fully validated Config.

    Raises:
        OSError: if the file cannot be opened.
        ConfigError: if the file content is invalid.
    """
    raw = _read_pairs(path)
    missing = [key for key in _MANDATORY_KEYS if key not in raw]
    if missing:
        raise ConfigError(f"missing mandatory key(s): {', '.join(missing)}")

    width = _parse_int(raw["WIDTH"], "WIDTH")
    height = _parse_int(raw["HEIGHT"], "HEIGHT")
    if width <= 0 or height <= 0:
        raise ConfigError("WIDTH and HEIGHT must be positive integers")

    entry = _parse_coordinates(raw["ENTRY"], "ENTRY", width, height)
    exit_ = _parse_coordinates(raw["EXIT"], "EXIT", width, height)
    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must be different cells")

    return Config(
        width=width,
        height=height,
        entry=entry,
        exit=exit_,
        output_file=raw["OUTPUT_FILE"],
        perfect=_parse_bool(raw["PERFECT"], "PERFECT"),
    )


def _read_pairs(path: str) -> dict[str, str]:
    """Read KEY=VALUE pairs from *path*, skipping blanks and '#' comments."""
    pairs: dict[str, str] = {}
    with open(path, encoding="utf-8") as config_file:
        for line in config_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ConfigError(f"invalid line (missing '='): {line!r}")
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip()
    return pairs


def _parse_int(value: str, key: str) -> int:
    """Parse *value* as an int, naming *key* in the error if it fails."""
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key} must be an integer, got {value!r}") from None


def _parse_bool(value: str, key: str) -> bool:
    """Parse *value* as True/False, naming *key* in the error if it fails."""
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ConfigError(f"{key} must be True or False, got {value!r}")


def _parse_coordinates(value: str, key: str, width: int, height: int) -> tuple[int, int]:
    """Parse *value* as 'x,y', checking it falls inside the maze bounds."""
    parts = value.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key} must be 'x,y', got {value!r}")
    x = _parse_int(parts[0], key)
    y = _parse_int(parts[1], key)
    if not (0 <= x < width and 0 <= y < height):
        raise ConfigError(f"{key} {x},{y} is outside the {width}x{height} maze")
    return x, y
