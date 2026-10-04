# Phase 4 - Sprites, Sound and Polish

Status: COMPLETE
Depends on: Phase 1, Phase 2, Phase 3

## 1. Goal

Give the game a face and a voice: optional sprite artwork, sound
effects wired to the engine events from Phase 3, looping background
music, and a rendering layer separated from the game loop.

## 2. Files Delivered

| File                  | Change | Responsibility                     |
|-----------------------|--------|------------------------------------|
| `assets.py`           | NEW    | Load and scale images safely       |
| `audio.py`            | NEW    | Sound effects, music, mute toggle  |
| `render.py`           | NEW    | All drawing for menu and gameplay  |
| `tools/make_sounds.py`| NEW    | Generate WAV effects with stdlib   |
| `main.py`             | EDIT   | Now only states, input, timing     |
| `config.py`           | EDIT   | Asset paths, volumes, new colors   |

## 3. Architecture After the Split

| Layer      | Module               | Knows about pygame |
|------------|----------------------|--------------------|
| Logic      | `engine.py`, `level.py`, `scores.py` | No |
| Presentation | `render.py`, `assets.py`, `audio.py` | Yes |
| Control    | `main.py`            | Yes                |

`main.py` shrank from roughly 300 lines to 230 because every drawing
method moved into `Renderer`. Adding a new visual effect now touches
one file only.

## 4. Sound Effects

Engine event names map directly onto sound file names, so
`self.audio.play(result)` in `_handle_result` needs no lookup table.

| Engine event | File            | When it plays              |
|--------------|-----------------|----------------------------|
| `eat`        | `eat.wav`       | Fruit collected            |
| `hit`        | `hit.wav`       | Life lost, lives remain    |
| `clear`      | `clear.wav`     | Level target reached       |
| `gameover`   | `gameover.wav`  | Last life lost             |
| (menu)       | `menu.wav`      | Menu move and confirm      |
| (music)      | `music.wav`     | Looping background track   |

Music accepts `music.ogg`, `music.wav` or `music.mp3`, checked in that
order. OGG is preferred for long tracks because it loads faster.

## 5. Generating Sounds Without Downloads

`tools/make_sounds.py` writes all six files using only `math`, `wave`
and `struct` from the standard library.

```powershell
python tools\make_sounds.py
```

Each note is a sine, square or triangle wave with a short attack and
release envelope so nothing clicks. Editing the `melody` list at the
bottom of the file changes the background music, which makes it a good
first "change one number and hear the result" exercise for a child.

## 6. Sprite Support

Drop any of these into `assets/images/`. All of them are optional.

| File        | Drawn as                                  |
|-------------|-------------------------------------------|
| `head.png`  | Snake head, auto rotated to face movement |
| `body.png`  | Body segment                              |
| `tail.png`  | Last segment                              |
| `fruit.png` | Fruit                                     |
| `wall.png`  | Wall block                                |

Rules:
1. Square PNG with transparency, ideally 64 x 64 or larger.
2. Images are scaled to `CELL_SIZE` once at startup, not per frame.
3. Draw the head facing right; rotation is handled in code.
4. A missing or corrupt file falls back to vector drawing, so the game
   always looks finished even with an empty `assets` folder.

## 7. Fallback Artwork

When no sprites are present the renderer draws:

- Head as a rounded square with two eyes placed along the direction
  vector, so the snake always looks where it is going.
- Body in two alternating greens for a striped, readable trail.
- Tail with a larger inset so it tapers.
- Fruit as a pulsing ellipse with a small leaf.
- Walls with a lighter outline for depth.
- The whole snake dimmed to half brightness during the death pause.

## 8. Failure Handling

| Problem                    | Behaviour                          |
|----------------------------|------------------------------------|
| No sound card or driver    | `Audio.ready` stays False, silent  |
| Missing sound file         | That effect is skipped             |
| Missing music file         | No music, effects still play       |
| Missing or broken image    | Vector fallback is used            |
| Read-only assets folder    | No effect, loading is read only    |

The game never crashes because of a missing asset. This is deliberate:
a child moving files around should not be able to break the program.

## 9. Controls Changed in This Phase

| Key | Before        | Now                    |
|-----|---------------|------------------------|
| M   | Back to menu  | Mute / unmute          |
| ESC | Quit or menu  | Back to menu, unchanged|

Mute works in every state and is shown as `[MUTED]` in the HUD and in
the menu footer.

## 10. Test Checklist

| Test                | How to test                            | Expected result                |
|---------------------|----------------------------------------|--------------------------------|
| Runs with no assets | Empty `assets/`, start the game        | Vector graphics, no sound      |
| Sound generation    | Run `tools\make_sounds.py`             | Six WAV files created          |
| Eat sound           | Collect a fruit                        | Rising two note blip           |
| Hit sound           | Crash with lives remaining             | Falling buzz, OUCH banner      |
| Clear sound         | Reach the fruit target                 | Arpeggio, CLEAR banner         |
| Game over sound     | Lose the last life                     | Descending phrase              |
| Music loop          | Idle in the menu for one minute        | Track repeats seamlessly       |
| Mute                | Press M                                | Silence, `[MUTED]` shown       |
| Mute persists       | Press M, then start a level            | Still muted                    |
| Head direction      | Turn in all four directions            | Eyes face the travel direction |
| Sprite override     | Add `fruit.png`                        | Image replaces the ellipse     |
| Broken image        | Rename a text file to `head.png`       | Vector head, no crash          |
| Death dimming       | Crash with lives remaining             | Snake greys out for 1.2 s      |
| Window resize       | Press N through every map              | Sprites stay correctly scaled  |

## 11. Handover to Phase 5

The core game is complete. Suggested Phase 5 work: a level editor
inside the game, extra fruit types with different effects, a moving
hazard, or packaging the project into a single `.exe` with PyInstaller
so it can be shared without installing Python.