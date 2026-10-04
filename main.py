# main.py -- Game states, input and orchestration
import os
import sys

import pygame

import config
import level as level_mod
import scores as score_mod
from audio import Audio
from engine import GameEngine
from render import Renderer
from editor import Editor

STATE_MENU = "menu"
STATE_PLAY = "play"

KEY_MAP = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Game:
    def __init__(self):
        self.audio = Audio()          # must come before pygame.init()
        pygame.init()
        pygame.display.set_caption("Snake Adventure - Phase 4")
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode(
            (config.MENU_WIDTH, config.MENU_HEIGHT))
        self.renderer = Renderer(self.screen)
        self.audio.start_music()

        self.scan_levels()
        self.menu_index = 0
        self.engine = None
        self.state = STATE_MENU
        self.overlay = None
        self.overlay_timer = 0.0
        self.new_record = False
        self.move_timer = 0.0
        self.running = True
        self.test_mode = False
        self.in_session = False

    # ---------- level discovery ----------
    def scan_levels(self):
        self.level_files = level_mod.list_level_files()
        self.levels = [self._safe_load(p) for p in self.level_files]
        if not self.levels:
            self.levels = [level_mod.fallback_level()]
            self.level_files = [""]

    @staticmethod
    def _safe_load(path):
        try:
            return level_mod.load_level(path)
        except level_mod.LevelError as exc:
            broken = level_mod.fallback_level()
            broken.name = os.path.basename(path) + "  [ERROR]"
            broken.error = str(exc)
            return broken

    def _fresh_level(self, index):
        path = self.level_files[index]
        level = self._safe_load(path) if path else level_mod.fallback_level()
        self.levels[index] = level
        return level

    # ---------- state transitions ----------
    def start_level(self, index, keep_progress=False):
        self.menu_index = index % len(self.levels)
        level = self._fresh_level(self.menu_index)
        if self.engine is None or not keep_progress:
            self.engine = GameEngine(level)
        else:
            self.engine.start_level(level, keep_score=True, keep_lives=True)
        self._resize_window(level)
        self.state = STATE_PLAY
        self.overlay = None
        self.move_timer = 0.0
        self.new_record = False

    def next_level(self):
        if self.test_mode:
            self.in_session = False
            return
        if self.menu_index + 1 < len(self.levels):
            self.start_level(self.menu_index + 1, keep_progress=True)
        else:
            self.new_record = score_mod.submit(score_mod.RUN_KEY,
                                               self.engine.score)
            self.overlay = "finished"
            self.audio.play("clear")

    def back_to_menu(self):
        if self.test_mode:
            self.in_session = False
            return
        self.state = STATE_MENU
        self.overlay = None
        self._set_mode(config.MENU_WIDTH, config.MENU_HEIGHT)

    def _resize_window(self, level):
        self._set_mode(max(level.cols * config.CELL_SIZE, 480),
                       level.rows * config.CELL_SIZE + config.HUD_HEIGHT)

    def _set_mode(self, width, height):
        self.screen = pygame.display.set_mode((width, height))
        self.renderer.set_screen(self.screen)

    # ---------- main loop ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        self.audio.stop_music()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.audio.toggle_mute()
                elif self.state == STATE_MENU:
                    self._menu_keys(event.key)
                else:
                    self._play_keys(event.key)

    def _menu_keys(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(self.levels)
            self.audio.play("menu")
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(self.levels)
            self.audio.play("menu")
        elif key == pygame.K_F5:
            self.scan_levels()
            self.menu_index = min(self.menu_index, len(self.levels) - 1)
            self.audio.play("menu")
        elif key in CONFIRM_KEYS:
            self.audio.play("menu")
            self.start_level(self.menu_index)
        elif key == pygame.K_e:
            self.audio.play("menu")
            self.open_editor(self.levels[self.menu_index])
        elif key == pygame.K_F1:
            self.audio.play("menu")
            self.open_editor(None)

    def _play_keys(self, key):
        if self.overlay == "clear":
            if key in CONFIRM_KEYS:
                self.next_level()
            elif key == pygame.K_ESCAPE:
                self.back_to_menu()
            return
        if self.overlay in ("gameover", "finished"):
            if key == pygame.K_r:
                self.start_level(self.menu_index)
            elif key in CONFIRM_KEYS or key == pygame.K_ESCAPE:
                self.back_to_menu()
            return

        if key == pygame.K_ESCAPE:
            self.back_to_menu()
        elif key == pygame.K_p:
            self.overlay = None if self.overlay == "paused" else "paused"
        elif key == pygame.K_r:
            self.engine.retry_run()
            self.overlay = None
            self.move_timer = 0.0
        elif key == pygame.K_F5:
            self.start_level(self.menu_index)
        elif key == pygame.K_n:
            self.start_level(self.menu_index + 1)
        elif key == pygame.K_b:
            self.start_level(self.menu_index - 1)
        elif key in KEY_MAP:
            self.engine.snake.queue_direction(KEY_MAP[key])

    def update(self, dt):
        if self.state != STATE_PLAY:
            return
        if self.overlay in ("paused", "clear", "gameover", "finished"):
            return

        if self.overlay == "dying":
            self.overlay_timer -= dt
            if self.overlay_timer <= 0:
                self.engine.respawn()
                self.overlay = None
                self.move_timer = 0.0
            return

        self.move_timer += dt
        step_time = 1.0 / self.engine.speed
        while self.move_timer >= step_time:
            self.move_timer -= step_time
            result = self.engine.step()
            if result != "none":
                self._handle_result(result)
                break
            step_time = 1.0 / self.engine.speed

    def _handle_result(self, result):
        """Engine event names double as sound keys."""
        self.audio.play(result)
        if result == "hit":
            self.overlay = "dying"
            self.overlay_timer = config.RESPAWN_DELAY
        elif result == "gameover":
            self.overlay = "gameover"
            self.new_record = (not self.test_mode) and score_mod.submit(
                self.engine.level.name, self.engine.score)
        elif result == "clear":
            self.overlay = "clear"
            self.new_record = (not self.test_mode) and score_mod.submit(
                self.engine.level.name, self.engine.score)
            
    def draw(self):
        if self.state == STATE_MENU:
            self.renderer.draw_menu(self.levels, self.menu_index,
                                    self.audio.muted)
        else:
            self.renderer.draw_play(self.engine, self.overlay,
                                    self.new_record, self.audio.muted)
        pygame.display.flip()
    
    def open_window(self, width, height):
        """Shared by the editor so window handling lives in one place."""
        self._set_mode(width, height)
        return self.screen

    def open_editor(self, level=None):
        pygame.display.set_caption("Snake Adventure - Level Editor")
        Editor(self, level).run()
        pygame.display.set_caption("Snake Adventure - Phase 5")
        self.scan_levels()
        self.menu_index = min(self.menu_index, len(self.levels))
        self.back_to_menu()

    def run_test(self, level):
        """Modal play session used by the editor. Scores are not saved."""
        self.engine = GameEngine(level)
        self._resize_window(level)
        self.state = STATE_PLAY
        self.overlay = None
        self.move_timer = 0.0
        self.new_record = False
        self.test_mode = True
        self.in_session = True
        while self.in_session and self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        self.test_mode = False

if __name__ == "__main__":
    Game().run()