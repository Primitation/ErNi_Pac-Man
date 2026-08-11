from __future__ import annotations

from .actor import Actor
from Engine import Vector2, ColliderComponent


class Entity(Actor):
    """Base Entity class."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor"
    ) -> None:
        """Initialize entity

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
            tag=tag
        )
        self._collider: ColliderComponent = self.add_component(
            ColliderComponent(
                get_rect=self.get_rect,
                tag="Actor",
                collides_with=None,
                blocking=False,
                bounce=0.8,
                static=False,
                enabled=True,
            )
        )

        self._collider.on_begin_overlap.bind(self._on_collision_begin)
        self._collider.on_end_overlap.bind(self._on_collision_end)
