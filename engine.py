# engine.py -- Core game logic (no rendering here)
import random
from collections import deque

import config


class Snake:
    """Snake body stored as a deque; head is index 0."""

    def __init__(self, start_pos, start_dir=(1, 0), length=config.START_LENGTH):
        x, y = start_pos
        dx, dy = start_dir
        self.body = deque((x - i * dx, y - i * dy) for i in range(length))
        self.direction = start_dir
        self.input_queue = deque()
        self.grow_pending = 0

    @property
    def head(self):
        return self.body[0]

    def queue_direction(self, new_dir):
        if len(self.input_queue) >= 2:
            return
        last = self.input_queue[-1] if self.input_queue else self.direction
        if new_dir == last:
            return
        if new_dir[0] == -last[0] and new_dir[1] == -last[1]:
            return
        self.input_queue.append(new_dir)

    def move(self, wrap=False, cols=0, rows=0):
        if self.input_queue:
            self.direction = self.input_queue.popleft()

        hx, hy = self.head
        dx, dy = self.direction
        nx, ny = hx + dx, hy + dy
        if wrap:
            nx %= cols
            ny %= rows

        new_head = (nx, ny)
        self.body.appendleft(new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()
        return new_head

    def grow(self, amount=1):
        self.grow_pending += amount

    def hits_self(self):
        return self.head in list(self.body)[1:]


class GameEngine:
    """Owns level state, snake, food, score, lives and progress."""

    def __init__(self, level):
        self.level = level
        self.score = 0
        self.lives = config.START_LIVES
        self.start_level(level, keep_score=False, keep_lives=False)

    # ---------- level lifecycle ----------
    def start_level(self, level, keep_score=True, keep_lives=True):
        self.level = level
        if not keep_score:
            self.score = 0
        if not keep_lives:
            self.lives = level.lives or config.START_LIVES

        self.target = level.target or config.DEFAULT_TARGET
        self.fruits_eaten = 0
        self.level_cleared = False
        self.game_over = False
        self.dead = False
        self._food_index = 0
        self._reset_actors()

    def retry_run(self):
        """Full restart of the current level: score, lives, progress."""
        self.start_level(self.level, keep_score=False, keep_lives=False)

    def respawn(self):
        """Called after losing a life. Keeps score and fruit progress."""
        self._reset_actors()

    def _reset_actors(self):
        lv = self.level
        self.snake = Snake(lv.start, lv.start_dir)
        base = lv.speed or config.START_SPEED
        self.speed = min(base + config.SPEED_STEP * self.fruits_eaten,
                         config.MAX_SPEED)
        self.dead = False
        self.food = self._spawn_food()

    # ---------- food ----------
    def _spawn_food(self):
        occupied = self.level.walls | set(self.snake.body)
        spots = self.level.food_spots
        while self._food_index < len(spots):
            spot = spots[self._food_index]
            self._food_index += 1
            if spot not in occupied:
                return spot
        free = [c for c in self.level.free_cells() if c not in occupied]
        return random.choice(free) if free else None

    # ---------- per-step update ----------
    def step(self):
        """Advance one cell. Returns: none | eat | clear | hit | gameover."""
        if self.game_over or self.level_cleared or self.dead:
            return "none"

        lv = self.level
        head = self.snake.move(lv.wrap, lv.cols, lv.rows)

        if not lv.wrap and not self._inside_grid(head):
            return self._lose_life()
        if lv.is_wall(head):
            return self._lose_life()
        if self.snake.hits_self():
            return self._lose_life()

        if head == self.food:
            self.snake.grow()
            self.fruits_eaten += 1
            self.score += config.POINTS_PER_FRUIT
            self.speed = min(self.speed + config.SPEED_STEP, config.MAX_SPEED)
            self.food = self._spawn_food()

            if self.fruits_eaten >= self.target:
                self.level_cleared = True
                self.score += (config.LEVEL_CLEAR_BONUS
                               + self.lives * config.LIFE_BONUS)
                return "clear"
            return "eat"
        return "none"

    def _lose_life(self):
        self.dead = True
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.game_over = True
            return "gameover"
        return "hit"

    def _inside_grid(self, pos):
        x, y = pos
        return 0 <= x < self.level.cols and 0 <= y < self.level.rows