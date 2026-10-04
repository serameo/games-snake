# Phase 3 - Gameplay Loop

Status: COMPLETE
Depends on: Phase 1, Phase 2

## 1. Goal

Turn a single endless arena into a real game: a level select menu,
a clear condition per level, a lives system, score carried across
levels, and high scores saved to disk.

## 2. Files Delivered

| File           | Change | Responsibility                        |
|----------------|--------|---------------------------------------|
| `scores.py`    | NEW    | Read and write `scores.json`          |
| `config.py`    | EDIT   | Lives, target, bonuses, menu size     |
| `level.py`     | EDIT   | Parse `@target` and `@lives`          |
| `engine.py`    | EDIT   | Lives, progress, clear state, events  |
| `main.py`      | EDIT   | Menu state, overlays, life HUD        |
| `levels/*.txt` | EDIT   | Added `@target` headers               |

## 3. New Map Headers

| Header    | Values          | Default | Meaning                     |
|-----------|-----------------|---------|-----------------------------|
| `@target` | positive number | 5       | Fruits needed to clear      |
| `@lives`  | positive number | 3       | Starting lives for the run  |

Example header block:

```text
@name Four Pillars
@speed 7
@dir right
@target 8
@lives 3
```

## 4. Game States

| State  | Description                                  |
|--------|----------------------------------------------|
| MENU   | Level list with per-level best score          |
| PLAY   | Active gameplay                               |

PLAY uses overlays instead of extra states:

| Overlay    | Trigger                    | Exit                     |
|------------|----------------------------|--------------------------|
| `paused`   | Press P                    | Press P                  |
| `dying`    | Lost a life, lives remain  | Auto after 1.2 s         |
| `clear`    | Fruit target reached       | ENTER to next level      |
| `gameover` | Lives reached zero         | R retry, ENTER menu      |
| `finished` | Cleared the final level    | ENTER menu               |

## 5. Engine Event Protocol

`GameEngine.step()` now returns a string so the presentation layer can
react without inspecting internal state.

| Return value | Meaning                          |
|--------------|----------------------------------|
| `none`       | Ordinary move                    |
| `eat`        | Fruit eaten, level not finished  |
| `clear`      | Fruit target reached             |
| `hit`        | Life lost, lives remain          |
| `gameover`   | Life lost, no lives remain       |

Phase 4 will hook sound effects onto these same return values.

## 6. Scoring

| Event                | Points                       |
|----------------------|------------------------------|
| Fruit eaten          | `POINTS_PER_FRUIT` = 10      |
| Level cleared        | `LEVEL_CLEAR_BONUS` = 50     |
| Each remaining life  | `LIFE_BONUS` = 25            |

Score and lives carry over to the next level. Losing a life keeps the
score and the fruit progress; only the snake position and length reset.
Speed is recomputed as `base + SPEED_STEP * fruits_eaten` so the
difficulty after respawn matches the progress already made.

## 7. High Score Storage

File: `scores.json` in the project root.

```json
{
  "(Full Run)": 640,
  "Four Pillars": 210,
  "Green Garden": 130
}
```

Rules:
1. One record per level name, plus `(Full Run)` for a complete playthrough.
2. Saved with a temporary file plus `os.replace`, so an interrupted
   write cannot corrupt the existing records.
3. A missing, empty or corrupt file is treated as no records at all.
4. If the folder is read-only the game keeps running without saving.

## 8. Controls

### Menu

| Key        | Action                       |
|------------|------------------------------|
| UP / DOWN  | Move selection               |
| ENTER      | Start selected level         |
| F5         | Rescan the `levels/` folder  |
| ESC        | Quit                         |

### Gameplay

| Key               | Action                          |
|-------------------|---------------------------------|
| Arrow keys / WASD | Turn                            |
| P                 | Pause / resume                  |
| R                 | Restart level, score and lives  |
| N / B             | Next / previous map             |
| F5                | Reload map file from disk       |
| M or ESC          | Back to menu                    |

## 9. Test Checklist

| Test               | How to test                          | Expected result               |
|--------------------|--------------------------------------|-------------------------------|
| Menu appears       | Start the game                       | Level list with best scores   |
| Selection          | Press UP and DOWN                    | Highlight moves and wraps     |
| Level clear        | Eat the target number of fruits      | LEVEL CLEAR banner            |
| Clear bonus        | Clear with 3 lives                   | Score gains 50 + 75           |
| Score carry over   | Press ENTER after a clear            | Next level keeps the score    |
| Life lost          | Hit a wall with 2+ lives             | OUCH banner, one dot removed  |
| Respawn progress   | Die at 3 of 5 fruits                 | Counter still reads 3/5       |
| Game over          | Lose the final life                  | GAME OVER banner              |
| New record         | Beat a stored best                   | NEW RECORD in green           |
| Persistence        | Close the game and reopen it         | Best scores still listed      |
| Corrupt score file | Put `hello` in `scores.json`         | Menu shows 0, no crash        |
| Finish the game    | Clear the last level                 | ALL LEVELS CLEAR banner       |
| Broken map         | Add `X` to a map, press F5 in play   | Yellow error line, no crash   |

## 10. Handover to Phase 4

Ready for Phase 4: sprites for the snake head and fruit, sound effects
mapped to the `eat` / `hit` / `clear` engine events, and a simple
background music track. Assets belong in `assets/`.