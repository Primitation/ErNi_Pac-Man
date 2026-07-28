from .actor import Actor
from Engine import on_end_of_anim
from Engine import Vector2, Input
from Engine import AnimatedSpriteComponent, SpriteComponent
from ..components.movement_components import (
    MovementComponent, PlayerMovementInput, FaceDirectionComponent)
from ..components.particle_component import ParticleTrailComponent
from ..components.origin_marker_component import OriginMarkerComponent


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
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets-Items.png",
                frame_width=16, frame_height=16,
                frame_count=1, start_frame=8,
                center=True,
            )
        )

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
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets-Items.png",
                frame_width=16, frame_height=16,
                frame_count=1, start_frame=9,
                center=True,
            )
        )

    def update(self, dt):
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()
