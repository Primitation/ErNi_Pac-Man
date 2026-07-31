from Engine.ActorSubsystem.Components.animated_sprite_component import (
    AnimatedSpriteComponent)
from assets.code.components.cheat_components import CheatComponent
from .actor import Actor
import random
from Engine import Vector2, Input
from ..components.movement_components import (
    ChasePlayerGridComponent, GhostFaceDirectionComponent, GridMovementComponent, FaceDirectionComponent)
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
            collision="Player"
        )

        # Movement components
        self.movement = self.add_component(GridMovementComponent(speed=speed))
        self.add_component(ChasePlayerGridComponent())
        facevalue = random.randrange(8)
        self.face = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=16, frame_height=16,
                frame_count=1, fps=1, loop=False, start_frame=160+facevalue,
                center=True, render_layer=2
            )
        )
        self._base_speed = self.movement.speed
        self.add_component(CheatComponent())

    def update(self, dt):
        if Input.is_action_triggered("dead"):
            self.dead(self.animation)
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()

    def freeze_input(self) -> None:
        if self.movement.speed == 0:
            self.movement.speed = self._base_speed
        else:
            self.movement.speed = 0

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
                center=True, render_layer=1
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
                center=True, render_layer=1
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
                center=True, render_layer=1
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
                center=True, render_layer=1
            )
        )
