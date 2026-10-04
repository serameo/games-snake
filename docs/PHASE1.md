# Phase 1 - Engine Setup

Status: COMPLETE
Target: Windows 10/11, Python 3.10+, pygame 2.x

## 1. Goal

Build a playable single-arena Snake prototype: window, game loop,
snake movement, growth, collision detection and an on-screen HUD.

## 2. Environment Setup

```powershell
mkdir snake_game; cd snake_game
mkdir assets, levels, docs
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install pygame
```

If PowerShell blocks the activation script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. Files Delivered

| File        | Responsibility                                      |
|-------------|-----------------------------------------------------|
| `config.py` | Global constants: grid size, colors, speed, scoring |
| `engine.py` | Pure game logic: Snake class, GameEngine class      |
| `main.py`   | Pygame window, input handling, rendering, HUD       |

Design rule: `engine.py` must never import pygame. This keeps the
logic testable and lets Phase 2 swap the arena without touching
rendering code.

## 4. Key Settings in config.py

| Constant        | Value | Meaning                          |
|-----------------|-------|----------------------------------|
| `GRID_COLS`     | 30    | Default arena width in cells     |
| `GRID_ROWS`     | 20    | Default arena height in cells    |
| `CELL_SIZE`     | 26    | Pixel size of one cell           |
| `HUD_HEIGHT`    | 60    | Pixel height of the top bar      |
| `FPS`           | 60    | Render frame rate                |
| `START_SPEED`   | 7.0   | Snake steps per second           |
| `SPEED_STEP`    | 0.4   | Speed gained per fruit           |
| `MAX_SPEED`     | 18.0  | Upper speed limit (kid friendly) |
| `START_LENGTH`  | 3     | Initial snake segments           |

## 5. Core Mechanics

1. Snake body is a `deque`; the head is index 0.
2. Movement appends a new head and pops the tail unless
   `grow_pending > 0`.
3. Turn requests go into `input_queue` (max 2 buffered) so fast
   double taps are not lost. 180 degree reversals are rejected.
4. `GameEngine.step()` resolves collisions in this order:
   out of grid, wall hit, self hit, food eaten.
5. Movement uses a fixed time step in `main.py`, so snake speed is
   identical on fast and slow machines.

## 6. Controls

| Key             | Action        |
|-----------------|---------------|
| Arrow keys / WASD | Turn        |
| P               | Pause / resume|
| R               | Restart       |
| ESC             | Quit          |

## 7. Test Checklist

| Test              | How to test             | Expected result          |
|-------------------|-------------------------|--------------------------|
| Movement          | Press all four arrows   | Snake turns immediately  |
| Reverse block     | Go right, press left    | Direction unchanged      |
| Growth            | Eat a fruit             | +1 segment, +10 points   |
| Wall collision    | Drive into the border   | GAME OVER banner         |
| Self collision    | Coil into own body      | GAME OVER banner         |
| Restart           | Press R                 | Score and speed reset    |
| Speed scaling     | Eat several fruits      | HUD speed value rises    |

## 8. Known Temporary Code

`GameEngine._build_border_walls()` hard-codes a rectangular border.
Phase 2 replaces it with a text file map loader.