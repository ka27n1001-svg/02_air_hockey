"""
GameEngine: owns the puck, paddles, score, timer and match state.
"""

import random
import pygame

from game.puck import Puck
from game.paddle import Paddle
from game.ai import ComputerAI
from game.collisions import handle_paddle_collision
from game.renderer import WIDTH, HEIGHT, MARGIN, GOAL_TOP, GOAL_BOTTOM

PLAYER_SPEED = 6
PUCK_RADIUS = 12
PADDLE_RADIUS = 28
INITIAL_PUCK_SPEED = 4.5
MATCH_DURATION_SECONDS = 30
PHYSICS_SUBSTEPS = 6


class GameEngine:
    def __init__(self):
        self.player = Paddle(
            x=WIDTH * 0.15, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=MARGIN + PADDLE_RADIUS, max_x=WIDTH / 2 - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.computer = Paddle(
            x=WIDTH * 0.85, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=WIDTH / 2 + PADDLE_RADIUS, max_x=WIDTH - MARGIN - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.ai = ComputerAI()
        self.puck = Puck(WIDTH / 2, HEIGHT / 2, PUCK_RADIUS)
        self.player_score = 0
        self.computer_score = 0
        self.match_start_ms = pygame.time.get_ticks()
        self.remaining_time = MATCH_DURATION_SECONDS
        self.match_active = True
        self.result_text = ""
        self._launch_puck()

    def _launch_puck(self):
        angle_choices = [0.3, 0.6, -0.3, -0.6]
        direction = random.choice([-1, 1])
        vy_factor = random.choice(angle_choices)
        self.puck.vx = INITIAL_PUCK_SPEED * direction
        self.puck.vy = INITIAL_PUCK_SPEED * vy_factor

    def handle_input(self, keys_pressed):
        if not self.match_active:
            return

        dx = dy = 0
        if keys_pressed[pygame.K_UP]:
            dy -= PLAYER_SPEED
        if keys_pressed[pygame.K_DOWN]:
            dy += PLAYER_SPEED
        if keys_pressed[pygame.K_LEFT]:
            dx -= PLAYER_SPEED
        if keys_pressed[pygame.K_RIGHT]:
            dx += PLAYER_SPEED
        self.player.move_by(dx, dy)

    def update(self):
        if not self.match_active:
            return

        elapsed = (pygame.time.get_ticks() - self.match_start_ms) / 1000.0
        self.remaining_time = max(0, MATCH_DURATION_SECONDS - elapsed)
        if self.remaining_time <= 0:
            self.remaining_time = 0
            self.match_active = False
            self.puck.vx = 0
            self.puck.vy = 0
            self.result_text = self._result_text()
            return

        self.ai.update(self.computer, self.puck)

        # Multiple smaller physics steps prevent the puck from tunnelling
        # through a paddle between 60-FPS frames.
        for _ in range(PHYSICS_SUBSTEPS):
            if not self.match_active:
                break

            self.puck.move_substep(PHYSICS_SUBSTEPS)
            self.puck.bounce_off_walls(HEIGHT, MARGIN)

            handle_paddle_collision(self.puck, self.player)
            handle_paddle_collision(self.puck, self.computer)

            if self._handle_goals():
                break

    def _handle_goals(self):
        # A goal counts only after the whole puck has crossed the goal line.
        # The puck must also be fully within the goal opening vertically.
        fully_in_goal_vertical = (
            self.puck.y - self.puck.radius >= GOAL_TOP
            and self.puck.y + self.puck.radius <= GOAL_BOTTOM
        )

        if self.puck.x + self.puck.radius < MARGIN:
            if fully_in_goal_vertical:
                self.computer_score += 1
                self._reset_puck()
                return True
            self.puck.x = MARGIN + self.puck.radius
            self.puck.vx = abs(self.puck.vx)

        elif self.puck.x - self.puck.radius > WIDTH - MARGIN:
            if fully_in_goal_vertical:
                self.player_score += 1
                self._reset_puck()
                return True
            self.puck.x = WIDTH - MARGIN - self.puck.radius
            self.puck.vx = -abs(self.puck.vx)

        return False

    def _reset_puck(self):
        # Put the puck exactly at the center.
        self.puck.x = WIDTH / 2
        self.puck.y = HEIGHT / 2

        # Clear any previous momentum/state.
        self.puck.vx = 0.0
        self.puck.vy = 0.0

        # Start the next point from the center.
        self._launch_puck()

    def _result_text(self):
        if self.player_score > self.computer_score:
            return "PLAYER WINS!"
        if self.computer_score > self.player_score:
            return "COMPUTER WINS!"
        return "DRAW"

    def restart(self):
        self.player.move_to(WIDTH * 0.15, HEIGHT / 2)
        self.computer.move_to(WIDTH * 0.85, HEIGHT / 2)
        self.ai = ComputerAI()
        self.player_score = 0
        self.computer_score = 0
        self.match_start_ms = pygame.time.get_ticks()
        self.remaining_time = MATCH_DURATION_SECONDS
        self.match_active = True
        self.result_text = ""
        self.puck.x = WIDTH / 2
        self.puck.y = HEIGHT / 2
        self._launch_puck()

    def draw(self, surface, font):
        from game import renderer
        renderer.draw_table(surface)
        renderer.draw_paddle(surface, self.player, renderer.COLOR_PLAYER)
        renderer.draw_paddle(surface, self.computer, renderer.COLOR_COMPUTER)
        renderer.draw_puck(surface, self.puck)

        renderer.draw_text(
            surface, font, f"Player: {self.player_score}", (40, 28)
        )
        time_text = f"Time: {int(self.remaining_time):02d}"
        renderer.draw_text(surface, font, time_text, (WIDTH // 2 - 65, 28))
        computer_text = f"Computer: {self.computer_score}"
        renderer.draw_text(surface, font, computer_text, (WIDTH - 240, 28))

        if not self.match_active:
            renderer.draw_banner(surface, font, self.result_text)
            renderer.draw_text(
                surface, font, "Press R to restart", (WIDTH // 2 - 105, HEIGHT // 2 + 35)
            )
