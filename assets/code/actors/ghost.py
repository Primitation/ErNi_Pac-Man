from Engine.ActorSubsystem.Components.animated_sprite_component import (
    AnimatedSpriteComponent)
from .actor import Actor
from Engine import Vector2, Input
from ..components.movement_components import (
    MovementComponent, FaceDirectionComponent)
from ..components.origin_marker_component import OriginMarkerComponent


class BasicGhost(Actor):
    """A basic ghost Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 100.0,
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
        )

        # Movement components
        self.movement = self.add_component(MovementComponent(speed=speed))
        self.add_component(FaceDirectionComponent())  # TODO: for ghosts only

        self.add_component(OriginMarkerComponent(color=0xFFFF0000, size=6.0))

    def update(self, dt):
        if Input.is_action_triggered("dead"):
            self.dead(self.animation)
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()


class RedGhost(BasicGhost):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
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
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=0,
                center=True,  # box is centered on actor.position, unrotated
            )
        )


class BlueGhost(BasicGhost):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
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
                "assets/texture/spritesheets/pacman_hd"
                "/PacManAssets-Ghosts.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=4,
                center=True,  # box is centered on actor.position, unrotated
            )
        )


class YellowGhost(BasicGhost):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
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
                "assets/texture/spritesheets/pacman_hd"
                "/PacManAssets-Ghosts.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=20,
                center=True,  # box is centered on actor.position, unrotated
            )
        )


class PinkGhost(BasicGhost):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
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
                "assets/texture/spritesheets/pacman_hd"
                "/PacManAssets-Ghosts.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=8,
                center=True,  # box is centered on actor.position, unrotated
            )
        )
