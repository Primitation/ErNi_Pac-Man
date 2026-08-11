from typing import Tuple
from Engine import Vector2, AActor
from Engine import AnimatedSpriteComponent


class Wall(AActor):
    """A wall Actor."""

    local_offset_scaling: float = 1.0

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
    ) -> None:
        """Initialize wall.

        Args:
            position: position
            velocity: velocity
            scale: scale
            local_rotation: local rotation
            tag: tag
            frame_width: frame width
            frame_height: frame height
            local_offset: local offset
        """
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

    def update(self, dt: float) -> None:
        """Updates.

        Args:
            dt: dt time.
        """
        super().update(dt)

    def destroy(self) -> None:
        """Destroy."""
        self.logger.debug("destroy")
        super().destroy()

    @classmethod
    def set_local_offset_scaling(cls, scale: float = 1) -> None:
        """Set local offset scaling

        Args:
            scale: scale
        """
        cls.local_offset_scaling = scale


class WallNorth(Wall):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "WallNorth"
    ) -> None:
        """Initialize wall north

        Args:
            position: position
            velocity: velocity
            scale: scale
            tag: tag
        """
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
    ) -> None:
        """Initialize wall east

        Args:
            position: position
            velocity: velocity
            scale: scale
            tag: tag
        """
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
    ) -> None:
        """Initialize wall south

        Args:
            position: position
            velocity: velocity
            scale: scale
            tag: tag
        """
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
    ) -> None:
        """Initialize wall west

        Args:
            position: position
            velocity: velocity
            scale: scale
            tag: tag
        """
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
