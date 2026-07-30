from typing import Tuple

from .actor import Actor
from Engine import Vector2, AActor
from Engine import AnimatedSpriteComponent
from ..components.origin_marker_component import OriginMarkerComponent


class Wall(AActor):
    """A wall Actor."""

    local_offset_scaling: int = 1

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
            static=True,
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/"
                "PacManAssets_Map_TileSet.png",
                frame_width=frame_width, frame_height=frame_height,
                local_offset=(local_offset[0] * Wall.local_offset_scaling,
                              local_offset[1] * Wall.local_offset_scaling),
                frame_count=1, start_frame=0, loop=False,
                center=True,
                local_rotation=local_rotation
            )
        )

    def update(self, dt):
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()

    @staticmethod
    def local_offset_scaling(scale: float = 1) -> None:
        Wall.local_offset_scaling = scale


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
