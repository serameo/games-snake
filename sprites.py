# sprites.py -- Procedural sprites, overridable by PNG files in assets/
import math
import os

import pygame

import config

FILES = {
    "head": "snake_head.png",
    "body": "snake_body.png",
    "tail": "snake_tail.png",
    "fruit": "fruit.png",
    "wall": "wall.png",
}
# All base sprites are drawn facing right; these are the rotations.
ANGLES = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}


def shift(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color[:3])


class SpriteSet:
    def __init__(self, cell):
        self.cell = cell
        custom = self._load_custom()

        self.body_img = custom.get("body") or self._draw_body()
        self.wall_img = custom.get("wall") or self._draw_wall()

        head = custom.get("head") or self._draw_head()
        tail = custom.get("tail") or self._draw_tail()
        self.head_imgs = {d: pygame.transform.rotate(head, a)
                          for d, a in ANGLES.items()}
        self.tail_imgs = {d: pygame.transform.rotate(tail, a)
                          for d, a in ANGLES.items()}
        self.fruit_frames = self._build_fruit(custom.get("fruit"))

    # ---------- optional PNG override ----------
    def _load_custom(self):
        found = {}
        for key, name in FILES.items():
            path = os.path.join(config.ASSETS_DIR, name)
            if not os.path.isfile(path):
                continue
            try:
                image = pygame.image.load(path).convert_alpha()
                found[key] = pygame.transform.smoothscale(
                    image, (self.cell, self.cell))
            except pygame.error:
                pass
        return found

    def _surface(self):
        return pygame.Surface((self.cell, self.cell), pygame.SRCALPHA)

    # ---------- procedural drawing ----------
    def _draw_body(self):
        cell = self.cell
        surface = self._surface()
        outer = pygame.Rect(1, 1, cell - 2, cell - 2)
        pygame.draw.rect(surface, shift(config.COLOR_SNAKE, -35), outer,
                         border_radius=cell // 4)
        inner = outer.inflate(-4, -4)
        pygame.draw.rect(surface, config.COLOR_SNAKE, inner,
                         border_radius=cell // 5)
        gloss = pygame.Rect(inner.x + 3, inner.y + 3, inner.w - 6, inner.h // 3)
        pygame.draw.rect(surface, shift(config.COLOR_SNAKE, 30), gloss,
                         border_radius=cell // 6)
        return surface

    def _draw_head(self):
        cell = self.cell
        surface = self._surface()
        outer = pygame.Rect(1, 1, cell - 2, cell - 2)
        pygame.draw.rect(surface, shift(config.COLOR_HEAD, -45), outer,
                         border_radius=cell // 3)
        pygame.draw.rect(surface, config.COLOR_HEAD, outer.inflate(-3, -3),
                         border_radius=cell // 3)

        eye_r = max(2, int(cell * 0.11))
        pupil_r = max(1, int(cell * 0.055))
        for ey in (cell * 0.32, cell * 0.68):
            center = (int(cell * 0.66), int(ey))
            pygame.draw.circle(surface, (250, 250, 250), center, eye_r)
            pygame.draw.circle(surface, (20, 25, 35),
                               (center[0] + pupil_r, center[1]), pupil_r)

        pygame.draw.line(surface, (230, 70, 90),
                         (cell - 3, cell // 2), (cell - 1, cell // 2), 2)
        return surface

    def _draw_tail(self):
        cell = self.cell
        surface = self._surface()
        points = [(cell - 2, 4), (cell - 2, cell - 4), (3, cell // 2)]
        pygame.draw.polygon(surface, shift(config.COLOR_SNAKE, -35), points)
        inner = [(cell - 4, 7), (cell - 4, cell - 7), (6, cell // 2)]
        pygame.draw.polygon(surface, config.COLOR_SNAKE, inner)
        return surface

    def _draw_wall(self):
        cell = self.cell
        surface = self._surface()
        rect = pygame.Rect(0, 0, cell, cell)
        pygame.draw.rect(surface, config.COLOR_WALL, rect, border_radius=3)
        pygame.draw.line(surface, shift(config.COLOR_WALL, 35),
                         (1, 1), (cell - 2, 1), 2)
        pygame.draw.line(surface, shift(config.COLOR_WALL, -40),
                         (1, cell - 2), (cell - 2, cell - 2), 2)
        pygame.draw.line(surface, shift(config.COLOR_WALL, -25),
                         (0, cell // 2), (cell, cell // 2), 1)
        pygame.draw.line(surface, shift(config.COLOR_WALL, -25),
                         (cell // 2, 0), (cell // 2, cell // 2), 1)
        return surface

    def _build_fruit(self, custom):
        frames = []
        count = max(2, config.FRUIT_PULSE_FRAMES)
        for i in range(count):
            wave = math.sin(i / count * math.pi * 2.0)
            scale = 0.86 + 0.14 * (wave * 0.5 + 0.5)
            frames.append(self._draw_fruit(scale, custom))
        return frames

    def _draw_fruit(self, scale, custom):
        cell = self.cell
        surface = self._surface()
        if custom is not None:
            size = max(4, int(cell * scale))
            scaled = pygame.transform.smoothscale(custom, (size, size))
            surface.blit(scaled, scaled.get_rect(
                center=(cell // 2, cell // 2)))
            return surface

        radius = max(3, int(cell * 0.36 * scale))
        center = (cell // 2, int(cell * 0.56))
        pygame.draw.circle(surface, shift(config.COLOR_FOOD, -55),
                           center, radius)
        pygame.draw.circle(surface, config.COLOR_FOOD, center, radius - 2)
        pygame.draw.circle(surface, shift(config.COLOR_FOOD, 60),
                           (center[0] - radius // 3, center[1] - radius // 3),
                           max(1, radius // 4))
        pygame.draw.line(surface, (110, 80, 50),
                         (center[0], center[1] - radius),
                         (center[0], int(cell * 0.14)), 2)
        leaf = pygame.Rect(0, 0, max(4, cell // 3), max(3, cell // 6))
        leaf.center = (center[0] + cell // 6, int(cell * 0.17))
        pygame.draw.ellipse(surface, (90, 190, 110), leaf)
        return surface

    # ---------- public accessors ----------
    def head(self, direction):
        return self.head_imgs.get(direction, self.head_imgs[(1, 0)])

    def tail(self, direction):
        return self.tail_imgs.get(direction, self.tail_imgs[(1, 0)])

    def fruit(self, anim_time):
        count = len(self.fruit_frames)
        index = int(anim_time * config.FRUIT_PULSE_SPEED * count) % count
        return self.fruit_frames[index]