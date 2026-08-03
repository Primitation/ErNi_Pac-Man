from .component import Component
from Engine import Collision


class ColliderComponent(Component):
    """Thin component wrapper around CollisionSubsystem's Collider."""

    def __init__(
        self,
        get_rect=None,
        tag: str = "default",
        collides_with=None,
        blocking: bool = False,
        bounce: float = 0.0,
        static: bool = False,
        enabled: bool = True,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        width: float = None,
        height: float = None,
    ):
        self._collider = None
        self._get_rect_override = get_rect
        self.tag = tag
        self.collides_with = collides_with
        self.blocking = blocking
        self.bounce = bounce
        self.static = static

        self.offset_x = offset_x
        self.offset_y = offset_y
        self.manual_width = width
        self.manual_height = height

        super().__init__(enabled)

    def on_added(self, actor) -> None:
        super().on_added(actor)

        self._collider = Collision.register(
            owner=actor,
            get_rect=self._get_rect_override or self._default_get_rect,
            tag=self.tag,
            collides_with=self.collides_with,
            blocking=self.blocking,
            bounce=self.bounce,
            static=self.static,
            enabled=self.enabled,
        )

    def _find_sprite_component(self):
        """Find the first component that has a get_rect method."""
        if self.actor is None:
            return None

        for component in self.actor.components:
            if component is self:
                continue
            if hasattr(component, "get_rect"):
                return component
        return None

    def _default_get_rect(self):
        sprite = self._find_sprite_component()

        if sprite is not None:
            rect = sprite.get_rect()

            center_x = rect[0] + rect[2] / 2
            center_y = rect[1] + rect[3] / 2

            w = self.manual_width if self.manual_width is not None else rect[2]
            h = self.manual_height if self.manual_height \
                is not None else rect[3]

            return (
                center_x - w / 2 + self.offset_x,
                center_y - h / 2 + self.offset_y,
                w,
                h,
            )

        actor = self.actor

        if actor is None:
            return (0, 0, 16, 16)

        w = self.manual_width or actor.scale.x
        h = self.manual_height or actor.scale.y

        return (
            actor.position.x - w / 2 + self.offset_x,
            actor.position.y - h / 2 + self.offset_y,
            w,
            h,
        )

    @property
    def collider(self):
        return self._collider

    @property
    def on_begin_overlap(self):
        return self._collider.on_begin_overlap

    @property
    def on_end_overlap(self):
        return self._collider.on_end_overlap

    def rect(self):
        return self._collider.rect()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if self._collider is not None:
            self._collider.enabled = value

    def destroy(self) -> None:
        if self._collider is not None:
            Collision.unregister(self._collider)
            self._collider = None
        super().destroy()
