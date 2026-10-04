# config.py -- Global settings

# --- Grid & Window ---
GRID_COLS = 30
GRID_ROWS = 20
CELL_SIZE = 26
HUD_HEIGHT = 60

SCREEN_WIDTH = GRID_COLS * CELL_SIZE
SCREEN_HEIGHT = GRID_ROWS * CELL_SIZE + HUD_HEIGHT

# --- Timing ---
FPS = 60
START_SPEED = 7.0      # snake moves per second
SPEED_STEP = 0.4       # speed added per fruit
MAX_SPEED = 18.0

# --- Rules ---
START_LENGTH = 3
POINTS_PER_FRUIT = 10

# --- Colors (R, G, B) ---
COLOR_BG = (24, 30, 40)
COLOR_GRID = (34, 42, 54)
COLOR_WALL = (90, 100, 120)
COLOR_SNAKE = (80, 200, 120)
COLOR_HEAD = (140, 240, 160)
COLOR_FOOD = (240, 100, 100)
COLOR_HUD_BG = (16, 20, 28)
COLOR_TEXT = (235, 240, 245)
COLOR_ALERT = (250, 210, 90)

# --- Phase 3: progression ---
START_LIVES = 3            # lives when a fresh run begins
DEFAULT_TARGET = 5         # fruits needed to clear a level
RESPAWN_DELAY = 1.2        # seconds of pause after losing a life
LEVEL_CLEAR_BONUS = 50     # points for finishing a level
LIFE_BONUS = 25            # extra points per remaining life
SCORE_FILE = "scores.json" # high score storage

# --- Phase 3: menu ---
MENU_WIDTH = 780
MENU_HEIGHT = 580

COLOR_MENU_SEL = (80, 200, 120)
COLOR_LIFE = (240, 100, 100)
COLOR_GOOD = (140, 240, 160)

# --- Phase 4: audio ---
ASSETS_DIR = "assets"
AUDIO_ENABLED = True
AUDIO_RATE = 44100
AUDIO_BUFFER = 512
SFX_VOLUME = 0.55
MUSIC_ENABLED = True
MUSIC_VOLUME = 0.30

# --- Phase 4: visuals ---
USE_SPRITES = True
FRUIT_PULSE_FRAMES = 10
FRUIT_PULSE_SPEED = 1.4      # pulses per second

# --- Phase 4: assets ---
IMAGE_DIR = "assets/images"
SOUND_DIR = "assets/sounds"

SFX_VOLUME = 0.7
MUSIC_VOLUME = 0.30
AUDIO_FREQ = 22050
AUDIO_BUFFER = 512

# --- Phase 4: extra colors ---
COLOR_EYE = (25, 32, 28)
COLOR_PUPIL = (250, 250, 250)
COLOR_BODY_ALT = (70, 165, 95)
COLOR_LEAF = (110, 200, 110)
COLOR_WALL_EDGE = (74, 86, 104)

# --- Phase 5: editor ---
EDITOR_HUD = 84
EDITOR_FOOT = 60
MIN_COLS, MAX_COLS = 10, 44
MIN_ROWS, MAX_ROWS = 8, 28
UNDO_LIMIT = 40

COLOR_EDIT_BG = (26, 30, 38)
COLOR_EDIT_GRID = (52, 60, 74)
COLOR_EDIT_PANEL = (36, 42, 54)
COLOR_EDIT_ACTIVE = (250, 205, 90)
COLOR_EDIT_OK = (120, 220, 140)
COLOR_EDIT_BAD = (240, 110, 110)
COLOR_CURSOR = (255, 255, 255)

