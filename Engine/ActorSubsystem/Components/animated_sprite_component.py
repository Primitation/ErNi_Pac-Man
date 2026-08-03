# animated_sprite_component.py
from typing import Optional, Callable, Tuple, Any
from .component import Component
from ... import Assets, SpriteSheetKey, Animation


class AnimatedSpriteComponent(Component):
    """Sprite-sheet animation component."""

    def __init__(
        self,
        path: str,
        frame_width: int,
        frame_height: int,
        frame_count: Optional[int] = None,
        columns: Optional[int] = None,
        start_frame: int = 0,
        fps: float = 10.0,
        loop: bool = True,
        on_complete: Optional[Callable[[], None]] = None,
        enabled: bool = True,
        local_offset: Tuple[float, float] = (0.0, 0.0),
        offset_rotates: bool = True,
        center: bool = False,
        local_rotation: float = 0.0,
        scale: Tuple[float, float] = (1.0, 1.0),
        render_layer: int = 0,
    ) -> None:
        super().__init__(enabled, local_scale=scale, render_layer=render_layer)

        self._key: Optional[SpriteSheetKey] = None
        self._animation: Optional[Animation] = None
        self._time: float = 0.0
        self._fps: float = fps
        self._loop: bool = loop
        self._on_complete: Optional[Callable[[], None]] = on_complete
        self._complete_fired: bool = False
        self.local_position = local_offset
        self.offset_rotates = offset_rotates
        self.center = center
        self.local_rotation = local_rotation

        self.set_animation(
            path, frame_width, frame_height, frame_count, columns,
            start_frame, fps, loop, on_complete,
        )

    def set_animation(
        self,
        path: str,
        frame_width: int,
        frame_height: int,
        frame_count: Optional[int] = None,
        columns: Optional[int] = None,
        start_frame: int = 0,
        fps: float = 10.0,
        loop: bool = True,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """Switch to a different sheet/slicing/clip."""
        self._key = SpriteSheetKey(
            path, frame_width, frame_height, frame_count, columns, start_frame
        )
        self._animation = None
        self._time = 0.0
        self._fps = fps
        self._loop = loop
        self._on_complete = on_complete
        self._complete_fired = False

        if self._key is not None:
            Assets.queue(self._key)  # type: ignore[arg-type]

    @property
    def fps(self) -> float:
        return self._fps

    def set_fps(self, fps: float) -> None:
        """Change playback speed in place."""
        self._fps = fps
        if self._animation is not None:
            self._animation.set_fps(fps)

    @property
    def sprite(self) -> Optional[Any]:
        if self._animation is None and self._key is not None:
            frames = Assets.get(self._key)  # type: ignore[arg-type]
            if frames is None:
                return None
            self._animation = Animation(frames, fps=self._fps, loop=self._loop)
        if self._animation is not None:
            return self._animation.frame_at(self._time)
        return None

    @property
    def width(self) -> int:
        sprite = self.sprite
        return sprite.width if sprite is not None else 0

    @property
    def height(self) -> int:
        sprite = self.sprite
        return sprite.height if sprite is not None else 0

    def get_world_position(self) -> Tuple[float, float]:
        """Get world position with centering support."""
        x, y = super().get_world_position()

        if self.center and self.actor is not None:
            world_scale = self.get_world_scale()
            width = self.width * world_scale.x
            height = self.height * world_scale.y
            x -= width / 2
            y -= height / 2

        return (x, y)

    def get_rect(self) -> Tuple[float, float, float, float]:
        """Rect (x, y, width, height) from the actor's position."""
        world_pos = self.get_world_position()
        world_scale = self.get_world_scale()
        width = self.width * world_scale.x
        height = self.height * world_scale.y
        return (world_pos[0], world_pos[1], width, height)

    def update(self, dt: float) -> None:
        """Update animation."""
        self._time += dt

        if (
            self._animation is not None
            and not self._complete_fired
            and self._animation.finished(self._time)
        ):
            self._complete_fired = True

            if self._on_complete is not None:
                self._on_complete()
