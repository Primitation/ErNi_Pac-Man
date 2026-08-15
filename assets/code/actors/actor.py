from __future__ import annotations

from typing import List, Optional

from Engine import (AActor, Vector2, ColliderComponent,
                    SpriteComponent, AnimatedSpriteComponent)


class Actor(AActor):
    """An Base Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        static: bool = False,
        tag: str = "Actor",
        collision: Optional[List[str]] = None
    ) -> None:
        """Initialize actor

        Args:
            position: position
            velocity: velocity
            scale: scale
            static: static
            tag: tag
            collision: collision
        """

        super().__init__(
            position=position,
            scale=scale,
            static=static
        )

        self.velocity: Vector2 = velocity
        self._start_position: Vector2 = Vector2(position.x, position.y)

        self.base_scale: Vector2 = Vector2(scale.x, scale.y)

        self._collider: ColliderComponent = self.add_component(
            ColliderComponent(
                get_rect=self.get_rect,
                tag=tag,
                collides_with=collision,
                blocking=False,
                bounce=0.8,
                static=False,
                enabled=True,
            )
        )

        self._collider.on_begin_overlap.bind(self._on_collision_begin)
        self._collider.on_end_overlap.bind(self._on_collision_end)

    def get_rect(self) -> tuple[float, float, float, float]:
        """Returns collider rect as (x, y, width, height).

        Returns:
            Returns collider rect as (x, y, width, height)."""

        sprite_component = (
            self.get_component(SpriteComponent)
            or self.get_component(AnimatedSpriteComponent)
        )

        if (sprite_component is not None
                and sprite_component.sprite is not None):
            width = sprite_component.width * self.base_scale.x / 2
            height = sprite_component.height * self.base_scale.y / 2
        else:
            width = self.base_scale.x / 2
            height = self.base_scale.y / 2

        return (
            self.position.x - width / 2,
            self.position.y - height / 2,
            width,
            height
        )

    def _on_collision_begin(self, self_collider: ColliderComponent,
                            other_collider: ColliderComponent) -> None:
        """Called when overlap starts.

        Args:
            self_collider: self collider
            other_collider: other collider
        """
        pass

    def _on_collision_end(self, self_collider: ColliderComponent,
                          other_collider: ColliderComponent) -> None:
        """Called when overlap stops.

        Args:
            self_collider: self collider
            other_collider: other collider
        """
        pass

    def update(self, dt: float) -> None:
        """Update position

        Args:
            dt: dt time
        """
        if not self.static:
            self.position += (
                self.velocity * (dt / 1000)
            )

    def destroy(self) -> None:
        """Clean up this bouncer."""
        super().destroy()

    def set_collider(self, collider: ColliderComponent) -> None:
        """Swap in a different ColliderComponent for this actor.

        Args:
            collider: collider
        """
        self.remove_component(self._collider)
        self._collider = self.add_component(collider)
        self._collider.on_begin_overlap.bind(self._on_collision_begin)
        self._collider.on_end_overlap.bind(self._on_collision_end)
