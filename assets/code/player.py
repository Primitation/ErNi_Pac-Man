from .actor import Actor
from Engine import on_end_of_anim
from Engine import Vector2, Input
from Engine import AnimatedSpriteComponent


class Player(Actor):
    """A player-controlled Actor, moved via the Input subsystem."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 200.0,
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
        )

        # Units per second applied along whichever direction(s) are held.
        self.speed = speed

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets-PacMan.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=0
            )
        )

        Input.bind_action("dead", [Input.KEYS["t"]])

    @on_end_of_anim(lambda self: self.destroy())
    def dead(self, animation: AnimatedSpriteComponent):
        animation.set_animation(
            "assets/texture/spritesheets/pacman_hd/PacManAssets-PacMan.png",
            frame_width=32, frame_height=32,
            frame_count=8, fps=4, loop=False, start_frame=4
        )

    def update(self, dt):
        """Turn held movement actions into velocity, then move as usual."""

        move_x = 0.0
        move_y = 0.0

        if Input.is_action_held("left"):
            move_x -= 1.0
            self.rotation = 180
        if Input.is_action_held("right"):
            move_x += 1.0
            self.rotation = 0
        if Input.is_action_held("up"):
            move_y -= 1.0
            self.rotation = 270
        if Input.is_action_held("down"):
            move_y += 1.0
            self.rotation = 90
        if Input.is_action_triggered("dead"):
            self.dead(self.animation)

        # Normalize so diagonal movement isn't faster than cardinal movement.
        length = (move_x ** 2 + move_y ** 2) ** 0.5
        if length > 0:
            move_x /= length
            move_y /= length

        self.velocity = Vector2(move_x * self.speed, move_y * self.speed)

        # Actor.update() applies self.velocity * (dt / 1000) to position.
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()
