from .actor import Actor
from Engine import Vector2
from Engine import AnimatedSpriteComponent


class Pacgum(Actor):
    """A pacgum Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Pacgum",
        speed: float = 100.0,
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            collision="Player"
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets-Items.png",
                frame_width=16, frame_height=16,
                frame_count=1, start_frame=9,
                center=True,
            )
        )

    def _on_collision_begin(self, collider, other):
        from .player import Player
        if isinstance(other.owner, Player):
            self.destroy()

    def update(self, dt):
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()


class SuperPacgum(Actor):
    """A pacgum Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Pacgum",
        speed: float = 100.0,
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            collision="Player"
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets-Items.png",
                frame_width=16, frame_height=16,
                frame_count=1, start_frame=9,
                center=True,
            )
        )

    def _on_collision_begin(self, collider, other):
        from .player import Player
        if isinstance(other.owner, Player):
            self.destroy()

    def update(self, dt):
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()
