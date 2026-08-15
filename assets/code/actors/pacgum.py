# pacgum.py
from typing import Any

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
        speed: float = 100.0
    ) -> None:
        """Initialize pacgum.

        Args:
            position: position
            velocity: velocity
            scale: scale
            tag: tag
            speed: speed
        """
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            collision=["Player"]
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets-Items.png",
                frame_width=16,
                frame_height=16,
                frame_count=1,
                start_frame=9,
                center=True,
            )
        )

    def _on_collision_begin(self, self_collider: Any,
                            other_collider: Any) -> None:
        """Action on collision.

        Args:
            self_collider: self collider
            other_collider: other collider
        """
        from .player import Player
        if isinstance(other_collider.owner, Player):
            self.destroy()

    def update(self, dt: float) -> None:
        """Updates

        Args:
            dt: dt time
        """

        super().update(dt)

    def destroy(self) -> None:
        """Destroy."""
        self.logger.debug("destroy")
        super().destroy()


class SuperPacgum(Actor):
    """A super pacgum Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Pacgum",
        speed: float = 100.0
    ) -> None:
        """Initialize superpacgum.

        Args:
            position: position
            velocity: velocity
            scale: scale
            tag: tag
            speed: speed
        """

        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            collision=["Player"]
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets-Items.png",
                frame_width=16,
                frame_height=16,
                frame_count=1,
                start_frame=9,
                center=True,
            )
        )

    def _on_collision_begin(self, self_collider: Any,
                            other_collider: Any) -> None:
        """Action on collision.

        Args:
            self_collider: self collider
            other_collider: other collider
        """
        from .player import Player
        if isinstance(other_collider.owner, Player):
            self.destroy()

    def update(self, dt: float) -> None:
        """Updates

        Args:
            dt: dt time
        """
        super().update(dt)

    def destroy(self) -> None:
        """Destroy."""
        self.logger.debug("destroy")
        super().destroy()
