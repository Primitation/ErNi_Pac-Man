from Engine.ActorSubsystem.Components.animated_sprite_component import (
    AnimatedSpriteComponent)
from assets.code.components.cheat_components import CheatComponent
from .actor import Actor
import random
from Engine import Vector2, Input
from ..components.movement_components import (
    ChasePlayerGridComponent, GhostFaceDirectionComponent, GridMovementComponent, FaceDirectionComponent)
from ..components.origin_marker_component import OriginMarkerComponent


EDIBLEGHOST_INDEX = 32

class BasicGhost(Actor):
    """A basic ghost Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 100.0,
        color_index: int = 0
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

        self.color_index = color_index

        self._edible = False
        self._base_speed = self.movement.speed
        self.add_component(CheatComponent())

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=color_index,
                center=True, render_layer=1
            )
        )

    @property
    def edible(self) -> bool:
        return self._edible

    @edible.setter
    def edible(self, value: bool) -> None:
        if self._edible == value:
            return

        self._edible = value

        self.update_ghost_mode()

    def update_ghost_mode(self):
        if self.edible:
            self.animation.set_animation(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=32, frame_height=32,
                frame_count=8, fps=4, loop=True, start_frame=EDIBLEGHOST_INDEX
            )
            self.face.enabled = False
        else:
            self.animation.set_animation(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=self.color_index
            )
            self.face.enabled = True

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
            color_index=0
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
            color_index=4
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
            color_index=20
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
            color_index=8
        )
