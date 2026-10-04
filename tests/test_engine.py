# tests/test_engine.py -- Rules of the game, verified without pygame
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config                      # noqa: E402
import level as level_mod          # noqa: E402
from engine import GameEngine      # noqa: E402

RIGHT, LEFT, UP, DOWN = (1, 0), (-1, 0), (0, -1), (0, 1)


def build_level(rows, direction=RIGHT, speed=6.0, target=5, lives=3,
                wrap=False, name="test"):
    """Turn an ASCII sketch into a Level object. No disk access."""
    walls, foods, start = set(), [], None
    width = max(len(row) for row in rows)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == "#":
                walls.add((x, y))
            elif char == "o":
                foods.append((x, y))
            elif char == "S":
                start = (x, y)
    if start is None:
        raise AssertionError("test map has no S")
    return level_mod.Level(name, width, len(rows), walls, start, direction,
                           foods, speed, wrap, "", target=target, lives=lives)


def open_room(cols=14, rows=9, **kwargs):
    """An empty field with no border, start at the middle left."""
    grid = [["."] * cols for _ in range(rows)]
    grid[rows // 2][4] = "S"
    return build_level(["".join(r) for r in grid], **kwargs)


def head_of(game):
    return tuple(game.snake.body[0])


def run_steps(game, count):
    """Step n times and return the list of event names."""
    return [game.step() for _ in range(count)]


class TestMovement(unittest.TestCase):
    def setUp(self):
        self.game = GameEngine(open_room())

    def test_starts_at_level_start(self):
        self.assertEqual(head_of(self.game), self.game.level.start)
        self.assertEqual(self.game.snake.direction, RIGHT)

    def test_step_moves_one_cell(self):
        x, y = head_of(self.game)
        before = len(self.game.snake.body)
        self.assertEqual(self.game.step(), "none")
        self.assertEqual(head_of(self.game), (x + 1, y))
        self.assertEqual(len(self.game.snake.body), before)

    def test_turn_is_applied_on_next_step(self):
        self.game.snake.queue_direction(UP)
        x, y = head_of(self.game)
        self.game.step()
        self.assertEqual(head_of(self.game), (x, y - 1))
        self.assertEqual(self.game.snake.direction, UP)

    def test_reverse_is_ignored(self):
        self.game.snake.queue_direction(LEFT)
        self.game.step()
        self.assertEqual(self.game.snake.direction, RIGHT)

    def test_two_queued_turns_apply_in_order(self):
        """Fast UP then LEFT in one frame must not be swallowed."""
        self.game.snake.queue_direction(UP)
        self.game.snake.queue_direction(LEFT)
        self.game.step()
        self.assertEqual(self.game.snake.direction, UP)
        self.game.step()
        self.assertEqual(self.game.snake.direction, LEFT)

    def test_body_follows_the_head(self):
        self.game.step()
        self.game.step()
        body = [tuple(cell) for cell in self.game.snake.body]
        self.assertEqual(len(set(body)), len(body), "body overlaps itself")
        for near, far in zip(body, body[1:]):
            distance = abs(near[0] - far[0]) + abs(near[1] - far[1])
            self.assertEqual(distance, 1, "body is not contiguous")


class TestEating(unittest.TestCase):
    def _level_with_fruit_ahead(self, count=1, **kwargs):
        cols, rows = 16, 9
        grid = [["."] * cols for _ in range(rows)]
        mid = rows // 2
        grid[mid][4] = "S"
        for i in range(count):
            grid[mid][5 + i] = "o"
        return build_level(["".join(r) for r in grid], **kwargs)

    def test_eating_reports_eat(self):
        game = GameEngine(self._level_with_fruit_ahead())
        self.assertEqual(game.step(), "eat")
        self.assertEqual(game.fruits_eaten, 1)

    def test_eating_scores_and_grows(self):
        game = GameEngine(self._level_with_fruit_ahead())
        length = len(game.snake.body)
        game.step()
        self.assertGreater(game.score, 0)
        self.assertEqual(len(game.snake.body), length)

    def test_eating_speeds_up_but_is_capped(self):
        game = GameEngine(self._level_with_fruit_ahead(count=8, target=99))
        first = game.speed
        game.step()
        self.assertGreaterEqual(game.speed, first)
        run_steps(game, 7)
        self.assertLessEqual(game.speed, config.MAX_SPEED)

    def test_new_fruit_is_legal(self):
        game = GameEngine(self._level_with_fruit_ahead(count=3, target=99))
        game.step()
        food = game.food
        self.assertIsNotNone(food, "no fruit respawned after eating")
        self.assertNotIn(food, game.level.walls)
        self.assertNotIn(tuple(food), [tuple(c) for c in game.snake.body])
        self.assertTrue(0 <= food[0] < game.level.cols)
        self.assertTrue(0 <= food[1] < game.level.rows)

    def test_target_reached_reports_clear(self):
        game = GameEngine(self._level_with_fruit_ahead(count=2, target=2))
        self.assertEqual(game.step(), "eat")
        self.assertEqual(game.step(), "clear")
        self.assertEqual(game.fruits_eaten, game.target)


class TestCollisions(unittest.TestCase):
    def _wall_ahead(self, lives=3):
        return build_level([
            "..........",
            "..........",
            "...S#.....",
            "..........",
            "..........",
        ], lives=lives)

    def test_wall_costs_a_life(self):
        game = GameEngine(self._wall_ahead(lives=3))
        self.assertEqual(game.step(), "hit")
        self.assertEqual(game.lives, 2)
        self.assertTrue(game.dead)

    def test_last_life_reports_gameover(self):
        game = GameEngine(self._wall_ahead(lives=1))
        self.assertEqual(game.step(), "gameover")
        self.assertEqual(game.lives, 0)

    def test_leaving_the_board_is_a_crash(self):
        game = GameEngine(open_room(cols=8, rows=5, wrap=False, lives=3))
        events = run_steps(game, 6)
        self.assertIn("hit", events, "snake walked off the board unharmed")

    def test_wrap_mode_crosses_the_edge(self):
        game = GameEngine(open_room(cols=8, rows=5, wrap=True, target=99))
        events = run_steps(game, 6)
        self.assertNotIn("hit", events)
        self.assertNotIn("gameover", events)
        self.assertEqual(head_of(game)[0], (4 + 6) % 8)

    def test_biting_itself_is_a_crash(self):
        cols, rows = 16, 9
        grid = [["."] * cols for _ in range(rows)]
        mid = rows // 2
        grid[mid][4] = "S"
        for i in range(3):
            grid[mid][5 + i] = "o"
        game = GameEngine(build_level(["".join(r) for r in grid],
                                      target=99, lives=3))
        run_steps(game, 3)                      # grow to at least six cells
        self.assertGreaterEqual(len(game.snake.body), 5)

        game.snake.queue_direction(DOWN)
        game.step()
        game.snake.queue_direction(LEFT)
        game.step()
        game.snake.queue_direction(UP)
        self.assertEqual(game.step(), "hit")
        self.assertEqual(game.lives, 2)


class TestLifecycle(unittest.TestCase):
    def _crashed_game(self):
        game = GameEngine(build_level([
            "..........",
            "...S#.....",
            "..........",
        ], lives=3, target=99))
        game.step()
        return game

    def test_respawn_restores_the_snake(self):
        game = self._crashed_game()
        lives, score = game.lives, game.score
        game.respawn()
        self.assertFalse(game.dead)
        self.assertEqual(head_of(game), game.level.start)
        self.assertEqual(game.snake.direction, game.level.start_dir)
        self.assertEqual(game.lives, lives, "respawn must not cost a life")
        self.assertEqual(game.score, score, "respawn must keep the score")

    def test_retry_run_resets_everything(self):
        game = self._crashed_game()
        game.retry_run()
        self.assertEqual(game.score, 0)
        self.assertEqual(game.fruits_eaten, 0)
        self.assertFalse(game.dead)
        self.assertGreaterEqual(game.lives, 1)
        self.assertEqual(head_of(game), game.level.start)

    def test_start_level_can_keep_progress(self):
        game = GameEngine(open_room(target=99))
        game.score = 120
        game.lives = 2
        game.start_level(open_room(name="second"), keep_score=True,
                         keep_lives=True)
        self.assertEqual(game.score, 120)
        self.assertEqual(game.lives, 2)
        self.assertEqual(game.fruits_eaten, 0)
        self.assertEqual(game.level.name, "second")

    def test_start_level_can_reset_progress(self):
        game = GameEngine(open_room(target=99))
        game.score = 120
        game.start_level(open_room(name="fresh"), keep_score=False,
                         keep_lives=False)
        self.assertEqual(game.score, 0)


class TestLevelFileRoundTrip(unittest.TestCase):
    """level_to_text and the parser must agree with each other."""

    def test_save_then_load_gives_the_same_map(self):
        grid = [
            list("######"),
            list("#S..F#"),
            list("#.##.#"),
            list("######"),
        ]
        text = level_mod.level_to_text("Round Trip", grid, DOWN, 8.5, 4, 2,
                                       True)
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "round_trip.txt")
            level_mod.save_text(path, text)
            loaded = level_mod.load_level(path)
        finally:
            import shutil
            shutil.rmtree(folder, ignore_errors=True)

        self.assertEqual(loaded.name, "Round Trip")
        self.assertEqual(loaded.start, (1, 1))
        self.assertEqual(loaded.start_dir, DOWN)
        self.assertEqual(loaded.target, 4)
        self.assertEqual(loaded.lives, 2)
        self.assertTrue(loaded.wrap)
        self.assertEqual(loaded.cols, 6)
        self.assertEqual(loaded.rows, 4)
        self.assertIn((2, 2), loaded.walls)
        self.assertIn((4, 1), loaded.food_spots)


class TestArchitecture(unittest.TestCase):
    """The logic layer must stay free of pygame, or these tests get slow."""

    def test_engine_does_not_import_pygame(self):
        code = "import engine, sys; print('pygame' in sys.modules)"
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False",
                         "engine.py pulled pygame in through an import")


if __name__ == "__main__":
    unittest.main(verbosity=2)