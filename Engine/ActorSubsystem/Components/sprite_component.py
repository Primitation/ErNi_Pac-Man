from .component import Component
from ... import Assets
from ... import Vector2


class SpriteComponent(Component):
    """A static, single-image sprite component."""

    def __init__(
        self,
        path: str = None,
        local_offset=Vector2(0.0, 0.0),
        offset_rotates: bool = True,
        center: bool = False,
        enabled: bool = True,
        local_rotation: float = 0.0,
        scale=Vector2(1.0, 1.0),
        render_layer: int = 0,
    ):
        super().__init__(enabled, local_scale=scale, render_layer=render_layer)
        self._path = path
        self.local_position = local_offset
        self.offset_rotates = offset_rotates
        self.local_rotation = local_rotation
        self.center = center

    def on_added(self, actor) -> None:
        super().on_added(actor)
        if self._path is not None:
            Assets.queue(self._path)

    def set_sprite(self, path: str) -> None:
        """Swap to a different static image."""
        self._path = path
        Assets.queue(path)

    @property
    def sprite(self):
        if self._path is None:
            return None
        return Assets.get(self._path)

    @property
    def width(self) -> int:
        sprite = self.sprite
        return sprite.width if sprite is not None else 0

    @property
    def height(self) -> int:
        sprite = self.sprite
        return sprite.height if sprite is not None else 0

    def get_world_position(self) -> tuple[float, float]:
        """Get world position with centering support."""
        x, y = super().get_world_position()

        if self.center and self.actor is not None:
            world_scale = self.get_world_scale()
            width = self.width * world_scale.x
            height = self.height * world_scale.y
            x -= width / 2
            y -= height / 2

        return (x, y)

    def get_rect(self) -> tuple[float, float, float, float]:
        """Rect (x, y, width, height) from the actor's position."""
        world_pos = self.get_world_position()
        world_scale = self.get_world_scale()
        width = self.width * world_scale.x
        height = self.height * world_scale.y
        return (world_pos[0], world_pos[1], width, height)
