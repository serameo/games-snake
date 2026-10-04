# render.py -- Every pixel is drawn here
import pygame

import assets
import config
import scores as score_mod

ANGLES = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.images = assets.load_images(config.CELL_SIZE)
        self.font = pygame.font.SysFont("consolas", 20, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 16)
        self.big_font = pygame.font.SysFont("consolas", 42, bold=True)

    def set_screen(self, screen):
        self.screen = screen

    # ---------- geometry ----------
    def _cell_rect(self, pos, inset=0):
        x, y = pos
        return pygame.Rect(
            x * config.CELL_SIZE + inset,
            y * config.CELL_SIZE + config.HUD_HEIGHT + inset,
            config.CELL_SIZE - inset * 2,
            config.CELL_SIZE - inset * 2,
        )

    def _blit_image(self, key, pos, angle=0):
        image = self.images.get(key)
        if image is None:
            return False
        if angle:
            image = pygame.transform.rotate(image, angle)
        self.screen.blit(image, self._cell_rect(pos).topleft)
        return True

    # ---------- menu ----------
    def draw_menu(self, levels, index, muted):
        self.screen.fill(config.COLOR_BG)
        width = self.screen.get_width()
        table = score_mod.load_scores()

        title = self.big_font.render("SNAKE ADVENTURE", True, config.COLOR_HEAD)
        self.screen.blit(title, title.get_rect(center=(width // 2, 70)))
        sub = self.font.render("Select a level", True, config.COLOR_TEXT)
        self.screen.blit(sub, sub.get_rect(center=(width // 2, 115)))

        for i, level in enumerate(levels):
            row = pygame.Rect(60, 160 + i * 44, width - 120, 38)
            selected = i == index
            if selected:
                pygame.draw.rect(self.screen, config.COLOR_HUD_BG, row,
                                 border_radius=8)
                pygame.draw.rect(self.screen, config.COLOR_MENU_SEL, row,
                                 width=2, border_radius=8)
            color = config.COLOR_MENU_SEL if selected else config.COLOR_TEXT
            label = self.font.render("%d.  %s" % (i + 1, level.name),
                                     True, color)
            target = level.target or config.DEFAULT_TARGET
            info = self.small_font.render(
                "target %d   best %d" % (target, table.get(level.name, 0)),
                True, config.COLOR_TEXT)
            self.screen.blit(label, (row.x + 16, row.y + 9))
            self.screen.blit(info,
                             (row.right - info.get_width() - 16, row.y + 12))

        best = table.get(score_mod.RUN_KEY, 0)
        foot1 = self.small_font.render("Best full run: %d" % best,
                                       True, config.COLOR_ALERT)
        foot2 = self.small_font.render(
            "ENTER play   E edit   F1 new map   M %s   F5 rescan   ESC quit"
            % ("unmute" if muted else "mute"),
            True, config.COLOR_TEXT)
        self.screen.blit(foot1, foot1.get_rect(
            center=(width // 2, config.MENU_HEIGHT - 70)))
        self.screen.blit(foot2, foot2.get_rect(
            center=(width // 2, config.MENU_HEIGHT - 40)))

    # ---------- gameplay ----------
    def draw_play(self, engine, overlay, new_record, muted):
        self.screen.fill(config.COLOR_BG)
        self._draw_grid(engine.level)
        self._draw_walls(engine.level.walls)
        if engine.food:
            self._draw_fruit(engine.food)
        self._draw_snake(engine.snake, dim=engine.dead)
        self._draw_hud(engine, muted)
        self._draw_overlay(engine, overlay, new_record)

    def _draw_grid(self, level):
        for x in range(level.cols + 1):
            px = x * config.CELL_SIZE
            pygame.draw.line(self.screen, config.COLOR_GRID,
                             (px, config.HUD_HEIGHT),
                             (px, self.screen.get_height()))
        for y in range(level.rows + 1):
            py = y * config.CELL_SIZE + config.HUD_HEIGHT
            pygame.draw.line(self.screen, config.COLOR_GRID,
                             (0, py), (self.screen.get_width(), py))

    def _draw_walls(self, walls):
        for pos in walls:
            if self._blit_image("wall", pos):
                continue
            rect = self._cell_rect(pos, 1)
            pygame.draw.rect(self.screen, config.COLOR_WALL, rect,
                             border_radius=3)
            pygame.draw.rect(self.screen, config.COLOR_WALL_EDGE, rect,
                             width=1, border_radius=3)

    def _draw_fruit(self, pos):
        if self._blit_image("fruit", pos):
            return
        pulse = (pygame.time.get_ticks() // 120) % 6
        inset = 4 + abs(3 - pulse) // 2
        rect = self._cell_rect(pos, inset)
        pygame.draw.ellipse(self.screen, config.COLOR_FOOD, rect)
        leaf = pygame.Rect(rect.centerx, rect.top - 3,
                           max(3, rect.width // 3), 4)
        pygame.draw.ellipse(self.screen, config.COLOR_LEAF, leaf)

    def _draw_snake(self, snake, dim=False):
        body = list(snake.body)
        for index in range(len(body) - 1, 0, -1):
            is_tail = index == len(body) - 1
            self._draw_segment(body[index], index, is_tail, dim)
        self._draw_head(body[0], snake.direction, dim)

    def _draw_segment(self, pos, index, is_tail, dim):
        key = "tail" if is_tail else "body"
        if self._blit_image(key, pos):
            return
        color = config.COLOR_SNAKE if index % 2 else config.COLOR_BODY_ALT
        if dim:
            color = tuple(c // 2 for c in color)
        inset = 4 if is_tail else 2
        pygame.draw.rect(self.screen, color, self._cell_rect(pos, inset),
                         border_radius=6)

    def _draw_head(self, pos, direction, dim):
        if self._blit_image("head", pos, ANGLES.get(direction, 0)):
            return
        color = config.COLOR_HEAD
        if dim:
            color = tuple(c // 2 for c in color)
        rect = self._cell_rect(pos, 1)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)

        dx, dy = direction
        px, py = -dy, dx                       # perpendicular axis
        cx, cy = rect.center
        side = config.CELL_SIZE * 0.22
        ahead = config.CELL_SIZE * 0.16
        radius = max(2, int(config.CELL_SIZE * 0.13))

        for sign in (1, -1):
            ex = int(cx + dx * ahead + px * side * sign)
            ey = int(cy + dy * ahead + py * side * sign)
            pygame.draw.circle(self.screen, config.COLOR_PUPIL, (ex, ey),
                               radius)
            pygame.draw.circle(self.screen, config.COLOR_EYE,
                               (int(ex + dx * 2), int(ey + dy * 2)),
                               max(1, radius // 2))

    def _draw_hud(self, engine, muted):
        width = self.screen.get_width()
        pygame.draw.rect(self.screen, config.COLOR_HUD_BG,
                         pygame.Rect(0, 0, width, config.HUD_HEIGHT))

        line1 = self.font.render(
            "SCORE %d   FRUIT %d/%d   SPEED %.1f"
            % (engine.score, engine.fruits_eaten, engine.target, engine.speed),
            True, config.COLOR_TEXT)
        self.screen.blit(line1, (16, 10))

        for i in range(engine.lives):
            pygame.draw.circle(self.screen, config.COLOR_LIFE,
                               (width - 24 - i * 24, 22), 8)

        error = getattr(engine.level, "error", "")
        hint = "%s%s   |   N/B map  F5 reload  P pause  M mute  ESC menu" % (
            engine.level.name, "  [MUTED]" if muted else "")
        line2 = self.small_font.render(
            error or hint, True,
            config.COLOR_ALERT if error else config.COLOR_GRID)
        self.screen.blit(line2, (16, 38))

    def _draw_overlay(self, engine, overlay, new_record):
        texts = {
            "dying": ("OUCH!", "Lives left: %d" % engine.lives),
            "paused": ("PAUSED", "Press P to continue"),
            "clear": ("LEVEL CLEAR!",
                      "Score %d   ENTER = next level" % engine.score),
            "gameover": ("GAME OVER", "R = retry   ENTER = menu"),
            "finished": ("ALL LEVELS CLEAR!",
                         "Total %d   ENTER = menu" % engine.score),
        }
        if overlay not in texts:
            return
        title, subtitle = texts[overlay]

        shade = pygame.Surface(self.screen.get_size())
        shade.set_alpha(170)
        shade.fill((0, 0, 0))
        self.screen.blit(shade, (0, 0))

        cx = self.screen.get_width() // 2
        cy = self.screen.get_height() // 2
        head = self.big_font.render(title, True, config.COLOR_ALERT)
        sub = self.font.render(subtitle, True, config.COLOR_TEXT)
        self.screen.blit(head, head.get_rect(center=(cx, cy - 24)))
        self.screen.blit(sub, sub.get_rect(center=(cx, cy + 24)))

        if new_record:
            record = self.font.render("NEW RECORD!", True, config.COLOR_GOOD)
            self.screen.blit(record, record.get_rect(center=(cx, cy + 64)))