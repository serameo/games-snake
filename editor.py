# editor.py -- Mouse driven map editor with live test play
import os
import re

import pygame

import assets
import config
import level as level_mod
import paths

EMPTY, WALL, START, FOOD = ".", "#", "S", "o"
TOOL_ORDER = [WALL, FOOD, START, EMPTY]
TOOL_LABEL = {WALL: "Wall", FOOD: "Fruit", START: "Start", EMPTY: "Erase"}
DIRECTIONS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
DIR_LABEL = {(1, 0): "right", (0, 1): "down",
             (-1, 0): "left", (0, -1): "up"}


def slugify(name):
    clean = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return clean or "custom_map"


class Editor:
    """Blocking editor loop. Returns when the user leaves with ESC."""

    def __init__(self, game, level=None):
        self.game = game
        self.images = assets.load_images(config.CELL_SIZE)
        self.font = pygame.font.SysFont("consolas", 18, bold=True)
        self.small = pygame.font.SysFont("consolas", 15)
        self.big = pygame.font.SysFont("consolas", 34, bold=True)

        self.tool = WALL
        self.undo_stack = []
        self.painting = False
        self.dirty = False
        self.message = ""
        self.message_timer = 0.0
        self.naming = False
        self.name_buffer = ""
        self.running = True

        self._load(level)

    # ---------- model ----------
    def _load(self, level):
        if level is None:
            self._new_map()
            return
        self.cols, self.rows = level.cols, level.rows
        self.name = level.name
        self.speed = level.speed or config.START_SPEED
        self.direction = level.start_dir
        self.target = level.target or config.DEFAULT_TARGET
        self.lives = level.lives or config.START_LIVES
        self.wrap = level.wrap
        self.path = level.path

        self.grid = [[EMPTY] * self.cols for _ in range(self.rows)]
        for x, y in level.walls:
            self._put(x, y, WALL)
        for x, y in level.food_spots:
            self._put(x, y, FOOD)
        self._put(level.start[0], level.start[1], START)

    def _new_map(self):
        self.cols, self.rows = 24, 16
        self.name = "My Map"
        self.speed = 6.0
        self.direction = (1, 0)
        self.target = 5
        self.lives = 3
        self.wrap = False
        self.path = ""
        self.grid = [[EMPTY] * self.cols for _ in range(self.rows)]
        self._border()
        self._put(2, self.rows // 2, START)

    def _put(self, x, y, char):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.grid[y][x] = char

    def _border(self):
        for x in range(self.cols):
            self.grid[0][x] = WALL
            self.grid[self.rows - 1][x] = WALL
        for y in range(self.rows):
            self.grid[y][0] = WALL
            self.grid[y][self.cols - 1] = WALL

    def _find(self, char):
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == char:
                    return (x, y)
        return None

    def _free_cells(self):
        return sum(row.count(EMPTY) + row.count(FOOD) + row.count(START)
                   for row in self.grid)

    # ---------- undo ----------
    def _snapshot(self):
        self.undo_stack.append([row[:] for row in self.grid])
        if len(self.undo_stack) > config.UNDO_LIMIT:
            self.undo_stack.pop(0)

    def _undo(self):
        if not self.undo_stack:
            self._say("Nothing to undo")
            return
        self.grid = self.undo_stack.pop()
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self._apply_window()
        self.dirty = True

    # ---------- painting ----------
    def _cell_at(self, mouse):
        mx, my = mouse
        x = mx // config.CELL_SIZE
        y = (my - config.EDITOR_HUD) // config.CELL_SIZE
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return (x, y)
        return None

    def _paint(self, cell, erase=False):
        if cell is None:
            return
        x, y = cell
        char = EMPTY if erase else self.tool
        if self.grid[y][x] == char:
            return
        if char == START:
            old = self._find(START)
            if old:
                self.grid[old[1]][old[0]] = EMPTY
        elif self.grid[y][x] == START and char == WALL:
            pass  # allowed: the start marker is simply replaced
        self.grid[y][x] = char
        self.dirty = True

    # ---------- resizing ----------
    def _resize(self, d_cols=0, d_rows=0):
        cols = max(config.MIN_COLS, min(config.MAX_COLS, self.cols + d_cols))
        rows = max(config.MIN_ROWS, min(config.MAX_ROWS, self.rows + d_rows))
        if (cols, rows) == (self.cols, self.rows):
            return
        self._snapshot()
        grid = [[EMPTY] * cols for _ in range(rows)]
        for y in range(min(rows, self.rows)):
            for x in range(min(cols, self.cols)):
                grid[y][x] = self.grid[y][x]
        self.grid, self.cols, self.rows = grid, cols, rows
        if self._find(START) is None:
            self._put(1, rows // 2, START)
        self.dirty = True
        self._apply_window()

    # ---------- validation and saving ----------
    def problems(self):
        issues = []
        if self._find(START) is None:
            issues.append("no start cell")
        if self._free_cells() < 12:
            issues.append("too few open cells")
        if self.target > max(1, self._free_cells() - 2):
            issues.append("target higher than open cells")
        return issues

    def save(self, as_new=False):
        issues = self.problems()
        if issues:
            self._say("Cannot save: " + ", ".join(issues), bad=True)
            return
        path = self.path
        if as_new or not path:
            path = self._next_free_path()
        text = level_mod.level_to_text(self.name, self.grid, self.direction,
                                       self.speed, self.target, self.lives,
                                       self.wrap)
        try:
            level_mod.save_text(path, text)
        except OSError as exc:
            self._say("Save failed: %s" % exc, bad=True)
            return
        self.path = path
        self.dirty = False
        self._say("Saved " + os.path.basename(path))
        self.game.scan_levels()

    def _next_free_path(self):
        folder = paths.levels_dir()
        base = slugify(self.name)
        candidate = os.path.join(folder, base + ".txt")
        counter = 2
        while os.path.exists(candidate):
            candidate = os.path.join(folder, "%s_%d.txt" % (base, counter))
            counter += 1
        return candidate

    def to_level(self):
        walls, foods = set(), []
        for y in range(self.rows):
            for x in range(self.cols):
                char = self.grid[y][x]
                if char == WALL:
                    walls.add((x, y))
                elif char == FOOD:
                    foods.append((x, y))
        start = self._find(START) or (1, 1)
        return level_mod.Level(self.name, self.cols, self.rows, walls, start,
                               self.direction, foods, self.speed, self.wrap,
                               self.path, target=self.target, lives=self.lives)

    def _test(self):
        issues = self.problems()
        if issues:
            self._say("Cannot test: " + ", ".join(issues), bad=True)
            return
        self.game.run_test(self.to_level())
        self._apply_window()

    # ---------- feedback ----------
    def _say(self, text, bad=False):
        self.message = text
        self.message_bad = bad
        self.message_timer = 2.5

    # ---------- window ----------
    def _apply_window(self):
        width = max(self.cols * config.CELL_SIZE, 640)
        height = (config.EDITOR_HUD + self.rows * config.CELL_SIZE
                  + config.EDITOR_FOOT)
        self.screen = self.game.open_window(width, height)

    # ---------- main loop ----------
    def run(self):
        self._apply_window()
        clock = pygame.time.Clock()
        while self.running and self.game.running:
            dt = clock.tick(config.FPS) / 1000.0
            self.message_timer = max(0.0, self.message_timer - dt)
            self._events()
            self._draw()
            pygame.display.flip()

    def _events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.KEYDOWN:
                if self.naming:
                    self._name_keys(event)
                else:
                    self._keys(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.naming:
                if event.button in (1, 3):
                    self._snapshot()
                    self.painting = event.button
                    self._paint(self._cell_at(event.pos), event.button == 3)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.painting = False
            elif event.type == pygame.MOUSEMOTION and self.painting:
                self._paint(self._cell_at(event.pos), self.painting == 3)

    def _name_keys(self, event):
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.name = self.name_buffer.strip() or self.name
            self.naming = False
            self.dirty = True
        elif event.key == pygame.K_ESCAPE:
            self.naming = False
        elif event.key == pygame.K_BACKSPACE:
            self.name_buffer = self.name_buffer[:-1]
        elif event.unicode and event.unicode.isprintable():
            if len(self.name_buffer) < 28:
                self.name_buffer += event.unicode

    def _keys(self, event):
        key = event.key
        ctrl = event.mod & pygame.KMOD_CTRL

        if key == pygame.K_ESCAPE:
            if self.dirty:
                self._say("Unsaved! Ctrl+S to save, ESC again to leave", True)
                self.dirty = False
            else:
                self.running = False
        elif ctrl and key == pygame.K_s:
            self.save()
        elif key == pygame.K_F12:
            self.save(as_new=True)
        elif key == pygame.K_F5:
            self._test()
        elif key == pygame.K_F2:
            self.naming = True
            self.name_buffer = self.name
        elif ctrl and key == pygame.K_z:
            self._undo()
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self.tool = TOOL_ORDER[key - pygame.K_1]
        elif key == pygame.K_LEFTBRACKET:
            self._resize(d_cols=-1)
        elif key == pygame.K_RIGHTBRACKET:
            self._resize(d_cols=1)
        elif key == pygame.K_MINUS:
            self._resize(d_rows=-1)
        elif key == pygame.K_EQUALS:
            self._resize(d_rows=1)
        elif key == pygame.K_COMMA:
            self.target = max(1, self.target - 1)
            self.dirty = True
        elif key == pygame.K_PERIOD:
            self.target += 1
            self.dirty = True
        elif key == pygame.K_9:
            self.speed = max(2.0, self.speed - 1)
            self.dirty = True
        elif key == pygame.K_0:
            self.speed = min(config.MAX_SPEED, self.speed + 1)
            self.dirty = True
        elif key == pygame.K_l:
            self.lives = self.lives % 9 + 1
            self.dirty = True
        elif key == pygame.K_t:
            self.wrap = not self.wrap
            self.dirty = True
        elif key == pygame.K_d:
            index = DIRECTIONS.index(self.direction)
            self.direction = DIRECTIONS[(index + 1) % 4]
            self.dirty = True
        elif key == pygame.K_b:
            self._snapshot()
            self._border()
            self.dirty = True
        elif key == pygame.K_c:
            self._snapshot()
            self.grid = [[EMPTY] * self.cols for _ in range(self.rows)]
            self._put(1, self.rows // 2, START)
            self.dirty = True

    # ---------- drawing ----------
    def _draw(self):
        self.screen.fill(config.COLOR_EDIT_BG)
        self._draw_canvas()
        self._draw_panel()
        self._draw_footer()
        if self.naming:
            self._draw_name_box()

    def _rect(self, x, y, inset=0):
        return pygame.Rect(x * config.CELL_SIZE + inset,
                           y * config.CELL_SIZE + config.EDITOR_HUD + inset,
                           config.CELL_SIZE - inset * 2,
                           config.CELL_SIZE - inset * 2)

    def _draw_canvas(self):
        board = pygame.Rect(0, config.EDITOR_HUD,
                            self.cols * config.CELL_SIZE,
                            self.rows * config.CELL_SIZE)
        pygame.draw.rect(self.screen, config.COLOR_BG, board)

        for y in range(self.rows):
            for x in range(self.cols):
                char = self.grid[y][x]
                if char == WALL:
                    self._sprite("wall", x, y, config.COLOR_WALL)
                elif char == FOOD:
                    self._sprite("fruit", x, y, config.COLOR_FOOD, oval=True)
                elif char == START:
                    self._draw_start(x, y)

        for x in range(self.cols + 1):
            px = x * config.CELL_SIZE
            pygame.draw.line(self.screen, config.COLOR_EDIT_GRID,
                             (px, config.EDITOR_HUD), (px, board.bottom))
        for y in range(self.rows + 1):
            py = config.EDITOR_HUD + y * config.CELL_SIZE
            pygame.draw.line(self.screen, config.COLOR_EDIT_GRID,
                             (0, py), (board.right, py))

        hover = self._cell_at(pygame.mouse.get_pos())
        if hover:
            pygame.draw.rect(self.screen, config.COLOR_CURSOR,
                             self._rect(*hover), width=2)

    def _sprite(self, key, x, y, color, oval=False):
        image = self.images.get(key)
        if image is not None:
            self.screen.blit(image, self._rect(x, y).topleft)
            return
        rect = self._rect(x, y, 3 if oval else 1)
        if oval:
            pygame.draw.ellipse(self.screen, color, rect)
        else:
            pygame.draw.rect(self.screen, color, rect, border_radius=3)

    def _draw_start(self, x, y):
        rect = self._rect(x, y, 2)
        pygame.draw.rect(self.screen, config.COLOR_HEAD, rect, border_radius=6)
        dx, dy = self.direction
        cx, cy = rect.center
        reach = config.CELL_SIZE // 3
        pygame.draw.line(self.screen, config.COLOR_EDIT_BG, (cx, cy),
                         (cx + dx * reach, cy + dy * reach), 3)

    def _draw_panel(self):
        width = self.screen.get_width()
        pygame.draw.rect(self.screen, config.COLOR_EDIT_PANEL,
                         pygame.Rect(0, 0, width, config.EDITOR_HUD))

        title = "%s%s" % (self.name, " *" if self.dirty else "")
        self.screen.blit(self.font.render(title, True, config.COLOR_TEXT),
                         (16, 10))
        info = ("%dx%d   speed %g   target %d   lives %d   dir %s   wrap %s"
                % (self.cols, self.rows, self.speed, self.target, self.lives,
                   DIR_LABEL[self.direction], "on" if self.wrap else "off"))
        self.screen.blit(self.small.render(info, True, config.COLOR_GRID),
                         (16, 34))

        x = 16
        for char in TOOL_ORDER:
            label = "%d %s" % (TOOL_ORDER.index(char) + 1, TOOL_LABEL[char])
            surface = self.small.render(label, True, config.COLOR_EDIT_BG
                                        if char == self.tool
                                        else config.COLOR_TEXT)
            box = pygame.Rect(x, 54, surface.get_width() + 16, 22)
            pygame.draw.rect(self.screen,
                             config.COLOR_EDIT_ACTIVE if char == self.tool
                             else config.COLOR_HUD_BG, box, border_radius=5)
            self.screen.blit(surface, (box.x + 8, box.y + 3))
            x = box.right + 8

        issues = self.problems()
        status = "READY" if not issues else "FIX: " + ", ".join(issues)
        color = config.COLOR_EDIT_OK if not issues else config.COLOR_EDIT_BAD
        surface = self.small.render(status, True, color)
        self.screen.blit(surface, (width - surface.get_width() - 16, 58))

    def _draw_footer(self):
        width = self.screen.get_width()
        top = self.screen.get_height() - config.EDITOR_FOOT
        pygame.draw.rect(self.screen, config.COLOR_EDIT_PANEL,
                         pygame.Rect(0, top, width, config.EDITOR_FOOT))

        line1 = ("LMB paint   RMB erase   [ ] width   - = height   "
                 ", . target   9 0 speed   L lives   T wrap   D dir")
        line2 = ("B border   C clear   Ctrl+Z undo   Ctrl+S save   "
                 "F12 save as new   F2 rename   F5 test   ESC menu")
        self.screen.blit(self.small.render(line1, True, config.COLOR_GRID),
                         (16, top + 10))
        self.screen.blit(self.small.render(line2, True, config.COLOR_GRID),
                         (16, top + 32))

        if self.message_timer > 0:
            color = (config.COLOR_EDIT_BAD if getattr(self, "message_bad",
                                                      False)
                     else config.COLOR_EDIT_OK)
            surface = self.font.render(self.message, True, color)
            box = surface.get_rect(center=(width // 2, top - 22))
            pygame.draw.rect(self.screen, config.COLOR_EDIT_PANEL,
                             box.inflate(20, 12), border_radius=6)
            self.screen.blit(surface, box)

    def _draw_name_box(self):
        width, height = self.screen.get_size()
        shade = pygame.Surface((width, height))
        shade.set_alpha(180)
        shade.fill((0, 0, 0))
        self.screen.blit(shade, (0, 0))

        box = pygame.Rect(0, 0, min(520, width - 60), 130)
        box.center = (width // 2, height // 2)
        pygame.draw.rect(self.screen, config.COLOR_EDIT_PANEL, box,
                         border_radius=10)
        pygame.draw.rect(self.screen, config.COLOR_EDIT_ACTIVE, box, width=2,
                         border_radius=10)

        prompt = self.font.render("Map name", True, config.COLOR_TEXT)
        value = self.big.render(self.name_buffer + "_", True,
                                config.COLOR_EDIT_ACTIVE)
        self.screen.blit(prompt, (box.x + 20, box.y + 16))
        self.screen.blit(value, (box.x + 20, box.y + 50))
        hint = self.small.render("ENTER accept   ESC cancel", True,
                                 config.COLOR_GRID)
        self.screen.blit(hint, (box.x + 20, box.bottom - 26))