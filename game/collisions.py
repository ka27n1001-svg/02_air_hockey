"""
Collision handling for the Air Hockey game.
"""

import math


def handle_paddle_collision(puck, paddle):
    """Resolve a puck/paddle circle collision robustly.

    The puck is moved out of the paddle along the collision normal and its
    velocity is reflected across that normal.  The collision is only applied
    when the puck is moving toward the paddle, which prevents repeated
    vibration while the two circles are still touching.
    """
    dx = puck.x - paddle.x
    dy = puck.y - paddle.y
    distance_sq = dx * dx + dy * dy
    min_distance = puck.radius + paddle.radius

    if distance_sq >= min_distance * min_distance:
        return False

    distance = math.sqrt(distance_sq)
    if distance > 1e-9:
        nx = dx / distance
        ny = dy / distance
    else:
        # If the centers coincide, use the side from which the puck arrived.
        speed_sq = puck.vx * puck.vx + puck.vy * puck.vy
        if speed_sq > 1e-9:
            speed = math.sqrt(speed_sq)
            nx = -puck.vx / speed
            ny = -puck.vy / speed
        else:
            nx, ny = 1.0, 0.0
        distance = 0.0

    # Push the puck completely outside the paddle so it cannot remain stuck.
    overlap = min_distance - distance
    puck.x += nx * (overlap + 0.5)
    puck.y += ny * (overlap + 0.5)

    # Only bounce when the puck is travelling into the paddle.
    velocity_into_paddle = puck.vx * nx + puck.vy * ny
    if velocity_into_paddle < 0:
        puck.vx -= 2 * velocity_into_paddle * nx
        puck.vy -= 2 * velocity_into_paddle * ny

    return True
