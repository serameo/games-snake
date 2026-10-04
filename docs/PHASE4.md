# Phase 4 - Sprites and Audio

Status: COMPLETE
Depends on: Phase 1, Phase 2, Phase 3

## 1. Goal

Give the game a face and a voice: directional snake sprites, an
animated fruit, textured walls, sound effects tied to engine events,
and looping background music. Everything works with zero external
asset files.

## 2. Design Decision: Synthesise First, Load If Present

No binary assets ship with the project. Instead:

1. On startup the game looks inside `assets/` for a matching file.
2. If the file exists it is loaded and scaled to the cell size.
3. If not, the sprite is drawn with `pygame.draw` and the sound is
   synthesised as raw 16-bit stereo samples.

The result is a project that always runs, yet upgrades instantly the
moment a child drops in their own drawing or recording.

## 3. Files Delivered

| File         | Change | Responsibility                          |
|--------------|--------|-----------------------------------------|
| `audio.py`   | NEW    | Sound effects, music, mute toggles      |
| `sprites.py` | NEW    | Sprite creation, rotation, animation    |
| `config.py`  | EDIT   | Audio and visual settings               |
| `main.py`    | EDIT   | Sprite rendering, sound on events       |

## 4. Optional Asset Files

Drop any of these into `assets/` to override the built-in version.

| File name         | Replaces                          |
|-------------------|-----------------------------------|
| `snake_head.png`  | Snake head, must face right       |
| `snake_body.png`  | Body segment                      |
| `snake_tail.png`  | Tail, tapering to the left        |
| `fruit.png`       | Fruit                             |
| `wall.png`        | Wall tile                         |
| `eat.wav`         | Fruit eaten sound                 |
| `hit.wav`         | Life lost sound                   |
| `clear.wav`       | Level cleared sound               |
| `gameover.wav`    | Game over sound                   |
| `select.wav`      | Menu move and confirm sound       |
| `music.ogg`       | Gameplay music loop               |
| `menu_music.ogg`  | Menu music loop                   |

Images are scaled automatically, so any square size works.
`.ogg` is preferred over `.wav` for music because it is far smaller.

## 5. Sprite System

| Sprite | How it is built                                            |
|--------|------------------------------------------------------------|
| Head   | Rounded body, two eyes with pupils, small tongue           |
| Body   | Rounded rectangle with a lighter gloss strip on top        |
| Tail   | Triangle tapering away from the body                       |
| Wall   | Tile with a light top edge, dark bottom edge, brick lines  |
| Fruit  | Circle with highlight, stem and leaf                       |

Rotation: every base sprite faces right and is pre-rotated once into
the four compass directions, so no rotation happens during the frame
loop.

Fruit animation: `FRUIT_PULSE_FRAMES` frames are rendered at startup
with sizes following a sine wave, then cycled by elapsed time. Zero
per-frame cost.

Tail direction is computed from the last two body cells. The helper
clamps large coordinate jumps, so the tail still points correctly on
wrap-around maps.

## 6. Audio System

### 6.1 Synthesis

Tones are generated as `array("h")` buffers of signed 16-bit stereo
samples and handed to `pygame.mixer.Sound(buffer=...)`.
Each tone supports a frequency slide, a harmonic mix and a decay curve.

| Event      | Built-in sound                            |
|------------|-------------------------------------------|
| `eat`      | Short blip sliding 700 Hz to 1050 Hz      |
| `hit`      | Falling buzz, 330 Hz down to 90 Hz        |
| `clear`    | Rising arpeggio C E G C                   |
| `gameover` | Descending four note phrase               |
| `select`   | Very short 900 Hz click                   |

Music is one melody rendered once and looped by the mixer. The menu
version uses a slower beat than the gameplay version. Tracks are built
lazily on first use so startup stays fast.

### 6.2 Event Mapping

Phase 3 made `GameEngine.step()` return an event string. Phase 4 simply
attaches a sound to each one, with no change to game logic.

| Engine return | Sound      | Visual reaction     |
|---------------|------------|---------------------|
| `eat`         | `eat`      | none                |
| `hit`         | `hit`      | OUCH overlay        |
| `gameover`    | `gameover` | GAME OVER overlay   |
| `clear`       | `clear`    | LEVEL CLEAR overlay |

### 6.3 Safety

1. `audio.pre_init()` runs before `pygame.init()` so the mixer uses a
   512 sample buffer and sounds are not delayed.
2. If the mixer cannot start, `AudioManager.ready` stays False and every
   method becomes a no-op. The game still runs in silence.
3. Corrupt or unreadable asset files fall back to the built-in version.
4. Music pauses with the P key and resumes on unpause.

## 7. New Controls

| Key | Action                       |
|-----|------------------------------|
| F2  | Sound effects on / off       |
| F3  | Music on / off               |

Both work in the menu and during gameplay. The current state is always
shown in the bottom line of the HUD.

## 8. Test Checklist

| Test              | How to test                        | Expected result                |
|-------------------|------------------------------------|--------------------------------|
| Head direction    | Turn all four ways                 | Eyes always face forward       |
| Tail direction    | Watch the tail on a turn           | Tail points along the body     |
| Tail on wrap      | map3, cross an open edge           | Tail still points correctly    |
| Fruit pulse       | Watch an uneaten fruit             | Smooth grow and shrink         |
| Wall texture      | Look at any border                 | Tiles with light and dark edges|
| Eat sound         | Eat a fruit                        | Short rising blip              |
| Hit sound         | Hit a wall with lives left         | Falling buzz plus OUCH         |
| Clear sound       | Reach the fruit target             | Rising arpeggio                |
| Game over sound   | Lose the last life                 | Descending phrase              |
| Menu music        | Sit on the menu                    | Slow loop plays                |
| Music switch      | Press ENTER to play                | Faster loop starts             |
| Pause music       | Press P                            | Music pauses and resumes       |
| Mute sfx          | Press F2                           | HUD reads sfx:off, no effects  |
| Mute music        | Press F3                           | Music stops, effects remain    |
| Custom sprite     | Add any square `fruit.png`         | New fruit appears              |
| Custom sound      | Add any `eat.wav`                  | New sound on eating            |
| No audio device   | Disable sound in Windows, run game | Game runs silently, no crash   |

## 9. Handover to Phase 5

Ready for Phase 5: packaging and polish. Build a single Windows `.exe`
with PyInstaller, add a settings screen for volume and cell size, write
a short child friendly manual, and add a simple in-game map editor.