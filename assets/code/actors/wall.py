from typing import Tuple

from .actor import Actor
from Engine import on_end_of_anim
from Engine import Vector2, Input
from Engine import AnimatedSpriteComponent, SpriteComponent
from ..components.movement_components import (
    MovementComponent, PlayerMovementInput, FaceDirectionComponent)
from ..components.particle_component import ParticleTrailComponent
from ..components.origin_marker_component import OriginMarkerComponent
import sys

class Wall(Actor):
    """A wall Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        local_rotation: float = 0,
        tag: str = "Wall",
        frame_width: int = 48,
        frame_height: int = 8,
        local_offset: Tuple[int, int] = (0, -20)
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            static=False if len(sys.argv) == 1 else True, # TODO: put to true
            tag=tag,
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets_Map_TileSet.png",
                frame_width=frame_width, frame_height=frame_height,
                local_offset=local_offset,
                frame_count=1, start_frame=0, loop=False,
                center=True,  # box is centered on actor.position, unrotated
                local_rotation=local_rotation
            )
        )
        self.add_component(OriginMarkerComponent(color=0xFFFF0000, size=6.0))

    def update(self, dt):
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()


class WallNorth(Wall):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "WallNorth"
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            local_rotation=0
        )


class WallEast(Wall):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "WallNorth"
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            local_rotation=0,
            local_offset=(20, 0),
            frame_width=8,
            frame_height=48,
        )


class WallSouth(Wall):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "WallNorth"
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            local_rotation=180
        )


class WallWest(Wall):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "WallNorth"
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            local_rotation=180,
            local_offset=(20, 0),
            frame_width=8,
            frame_height=48,
        )
