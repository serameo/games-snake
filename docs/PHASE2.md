# Phase 2 - Level Loading

Status: COMPLETE
Depends on: Phase 1

## 1. Goal

Move the arena out of the source code and into editable text files,
so a child can design a new map with Notepad and play it instantly.

## 2. Files Delivered

| File               | Responsibility                              |
|--------------------|---------------------------------------------|
| `level.py`         | Map parser, `Level` object, file discovery  |
| `levels/map1.txt`  | Green Garden - open beginner field          |
| `levels/map2.txt`  | Four Pillars - obstacles in the middle      |
| `levels/map3.txt`  | Tunnel Run - wrap-around edges              |
| `engine.py`        | Updated: takes a `Level` instead of a border|
| `main.py`          | Updated: level switching, window resize     |

## 3. Map File Format

### 3.1 Grid Symbols

| Symbol | Meaning                          |
|--------|----------------------------------|
| `#`    | Wall (deadly)                    |
| `.`    | Empty path                       |
| space  | Empty path (same as `.`)         |
| `S`    | Snake start (exactly one needed) |
| `F`    | Fruit spawn point (zero or more) |

### 3.2 Header Lines

Header lines appear above the grid and start with `@`.
Lines starting with `;` are comments and are ignored.

| Header   | Values                     | Default | Meaning                   |
|----------|----------------------------|---------|---------------------------|
| `@name`  | free text                  | file name | Level title in the HUD  |
| `@speed` | number, e.g. `6`           | 7.0     | Starting steps per second |
| `@dir`   | right, left, up, down      | right   | Initial heading           |
| `@wrap`  | on / off                   | off     | Pass through open edges   |

### 3.3 Example

```text
@name Green Garden
@speed 6
@dir right
; a wide open field
##############################
#............................#
#.........S..........F.......#
#............................#
##############################
```

## 4. Parser Rules

1. Grid size is taken from the file, not from `config.py`.
   The window resizes automatically for each map.
2. Short rows are padded with `.` so ragged files still work.
3. Trailing blank lines are removed.
4. Unknown symbols raise a `LevelError` naming the exact row and
   column, which is shown in the HUD in yellow.
5. Missing `S` or more than one `S` raises a `LevelError`.
6. On any error the game falls back to a plain bordered arena, so it
   never crashes while a child is editing a map.

## 5. Fruit Spawning Order

1. Use the map's `F` markers in file order.
2. When all `F` markers are used, pick a random free cell.
3. Cells occupied by walls or the snake are always skipped.

## 6. New Controls

| Key  | Action                                   |
|------|------------------------------------------|
| N    | Next map                                 |
| B    | Previous map                             |
| F5   | Reload current map file from disk        |

F5 is the key feature for kids: keep Notepad and the game open side by
side, save the file, press F5, and the new map appears at once.

## 7. Test Checklist

| Test              | How to test                        | Expected result             |
|-------------------|------------------------------------|-----------------------------|
| Map loads         | Start the game                     | Green Garden layout appears |
| Window resize     | Press N through all maps           | Window fits each map        |
| Level name        | Press N                            | HUD title changes           |
| Speed header      | Compare map1 and map3              | map3 starts faster          |
| Start direction   | Start any map                      | Snake moves as `@dir` says  |
| Fixed fruit       | Start map1                         | Fruit appears on the `F`    |
| Wrap edges        | map3, exit through an open edge    | Snake reappears opposite    |
| Bad symbol        | Put `X` in a map, press F5         | Yellow error, no crash      |
| Missing S         | Delete `S`, press F5               | Yellow error, no crash      |
| Hot reload        | Edit a wall in Notepad, press F5   | Map updates immediately     |

## 8. Handover to Phase 3

Ready for Phase 3: level clear conditions (fruit target per map),
lives, persistent high score and a start / level select menu.