# level.py -- Text map parser
import os
import paths

WALL_CHAR = "#"
EMPTY_CHARS = {".", " "}
START_CHAR = "S"
FOOD_CHAR = "F"

DIRECTIONS = {
    "right": (1, 0),
    "left": (-1, 0),
    "up": (0, -1),
    "down": (0, 1),
}

LEVELS_DIR = "levels"


class LevelError(Exception):
    """Raised when a map file cannot be understood."""

class Level:
    def __init__(self, name, cols, rows, walls, start, start_dir,
                 food_spots, speed, wrap, path="",
                 target=None, lives=None):
        self.name = name
        self.cols = cols
        self.rows = rows
        self.walls = walls
        self.start = start
        self.start_dir = start_dir
        self.food_spots = food_spots
        self.speed = speed
        self.wrap = wrap
        self.path = path
        self.target = target      # fruits needed to clear
        self.lives = lives        # per-level life override
        self.error = ""           # filled in when a file is broken

    def is_wall(self, pos):
        return pos in self.walls

    def free_cells(self):
        return [
            (x, y)
            for y in range(self.rows)
            for x in range(self.cols)
            if (x, y) not in self.walls
        ]


def _parse_meta(line, meta):
    """Parse a '@key value' header line."""
    parts = line[1:].strip().split(None, 1)
    if not parts:
        return
    key = parts[0].lower()
    value = parts[1].strip() if len(parts) > 1 else ""
    meta[key] = value


def load_level(path):
    """Read a .txt map file and return a Level object."""
    if not os.path.isfile(path):
        raise LevelError("Map file not found: %s" % path)

    with open(path, "r", encoding="utf-8") as handle:
        raw_lines = handle.read().splitlines()

    meta = {}
    grid = []
    for line in raw_lines:
        if line.startswith(";"):          # comment
            continue
        if line.startswith("@"):          # metadata
            _parse_meta(line, meta)
            continue
        if line.strip() == "" and not grid:
            continue
        grid.append(line.rstrip("\n"))

    while grid and grid[-1].strip() == "":
        grid.pop()
    if not grid:
        raise LevelError("Map has no grid rows: %s" % path)

    cols = max(len(row) for row in grid)
    rows = len(grid)
    grid = [row.ljust(cols, ".") for row in grid]   # pad short rows

    walls = set()
    food_spots = []
    start = None

    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            pos = (x, y)
            if char == WALL_CHAR:
                walls.add(pos)
            elif char == START_CHAR:
                if start is not None:
                    raise LevelError("More than one 'S' in %s" % path)
                start = pos
            elif char == FOOD_CHAR:
                food_spots.append(pos)
            elif char not in EMPTY_CHARS:
                raise LevelError(
                    "Unknown symbol '%s' at row %d col %d in %s"
                    % (char, y + 1, x + 1, path)
                )

    if start is None:
        raise LevelError("No start position 'S' in %s" % path)

    name = meta.get("name", os.path.splitext(os.path.basename(path))[0])
    start_dir = DIRECTIONS.get(meta.get("dir", "right").lower(), (1, 0))
    wrap = meta.get("wrap", "off").lower() in ("on", "true", "yes", "1")

    def _int_meta(key):
        try:
            value = int(meta.get(key, ""))
        except ValueError:
            return None
        return value if value > 0 else None

    try:
        speed = float(meta.get("speed", 0)) or None
    except ValueError:
        speed = None

    return Level(name, cols, rows, walls, start, start_dir,
                 food_spots, speed, wrap, path,
                 target=_int_meta("target"), lives=_int_meta("lives"))


def list_level_files():
    folder = paths.levels_dir()
    names = sorted(n for n in os.listdir(folder) if n.lower().endswith(".txt"))
    return [os.path.join(folder, n) for n in names]


def fallback_level():
    """Plain bordered arena used when no map file can be loaded."""
    import config
    cols, rows = config.GRID_COLS, config.GRID_ROWS
    walls = set()
    for x in range(cols):
        walls.add((x, 0))
        walls.add((x, rows - 1))
    for y in range(rows):
        walls.add((0, y))
        walls.add((cols - 1, y))
    return Level("Fallback Arena", cols, rows, walls,
                 (cols // 2, rows // 2), (1, 0), [], None, False)

DIR_NAMES = {(1, 0): "right", (-1, 0): "left",
             (0, -1): "up", (0, 1): "down"}


def level_to_text(name, grid, direction, speed, target, lives, wrap):
    """Build the full map file content as one string."""
    lines = [
        "@name %s" % name,
        "@speed %g" % speed,
        "@dir %s" % DIR_NAMES.get(direction, "right"),
        "@target %d" % target,
        "@lives %d" % lives,
    ]
    if wrap:
        lines.append("@wrap on")
    lines.append("")
    lines.extend("".join(row) for row in grid)
    return "\n".join(lines) + "\n"


def save_text(path, text):
    """Atomic write so a crash cannot destroy an existing map."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp_path, path)

