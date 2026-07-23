from .actor import Actor
from Engine import Vector2, Input


class Player(Actor):
    """A player-controlled Actor, moved via the Input subsystem."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        sprite_path: str,
        tag: str = "Actor",
        speed: float = 200.0,
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            sprite_path=sprite_path,
            tag=tag,
        )

        # Units per second applied along whichever direction(s) are held.
        self.speed = speed

    def update(self, dt):
        """Turn held movement actions into velocity, then move as usual."""

        move_x = 0.0
        move_y = 0.0

        if Input.is_action_held("left"):
            move_x -= 1.0
        if Input.is_action_held("right"):
            move_x += 1.0
        if Input.is_action_held("up"):
            move_y -= 1.0
        if Input.is_action_held("down"):
            move_y += 1.0

        # Normalize so diagonal movement isn't faster than cardinal movement.
        length = (move_x ** 2 + move_y ** 2) ** 0.5
        if length > 0:
            move_x /= length
            move_y /= length

        self.velocity = Vector2(move_x * self.speed, move_y * self.speed)

        # Actor.update() applies self.velocity * (dt / 1000) to position.
        super().update(dt)
