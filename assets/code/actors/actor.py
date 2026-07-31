from Engine import AActor, Vector2
from Engine import ColliderComponent, SpriteComponent, AnimatedSpriteComponent


class Actor(AActor):
    """An Base Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        static: bool = False,
        tag: str = "Actor",
        collision: list[str] = None

    ):
        super().__init__(
            position=position,
            scale=scale,
            static=static
        )

        self.velocity = velocity
        self._start_position = Vector2(position.x, position.y)

        # The "resting" scale to animate around. Kept separate from
        # self.scale (which the renderer actually reads) so the punch
        # animation can freely push self.scale up and back down.
        self.base_scale = Vector2(scale.x, scale.y)

        # Register with collision system. get_rect is our own
        # override (below), not the ColliderComponent default, so
        # the hitbox stays pinned to base_scale regardless of what a
        # sprite/animation component on this actor is doing.
        self._collider = self.add_component(
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

        # Bind collision events for debugging
        self._collider.on_begin_overlap.bind(self._on_collision_begin)
        self._collider.on_end_overlap.bind(self._on_collision_end)

    def get_rect(self):
        """Return collider rect as (x, y, width, height).

        Collider is centered on actor.position, matching the sprite.
        Uses base_scale so animations do not resize the hitbox.
        """

        sprite_component = (
            self.get_component(SpriteComponent)
            or self.get_component(AnimatedSpriteComponent)
        )

        if (sprite_component is not None
                and sprite_component.sprite is not None):
            width = sprite_component.width * self.base_scale.x/2
            height = sprite_component.height * self.base_scale.y/2
        else:
            width = self.base_scale.x/2
            height = self.base_scale.y/2

        return (
            self.position.x - width / 2,
            self.position.y - height / 2,
            width,
            height
        )

    def _on_collision_begin(self, self_collider, other_collider):
        """Called when this bouncer start overlapping with another collider."""
        pass

    def _on_collision_end(self, self_collider, other_collider):
        """Called when this bouncer stops overlapping with another collider."""
        pass

    def update(self, dt):
        """Update position"""
        if not self.static:
            self.position += (
                self.velocity * (dt / 1000)
            )

    def destroy(self):
        """Clean up this bouncer. super().destroy() tears down every
        component this actor owns — including this._collider, which
        unregisters itself from Collision — so there's nothing left
        to do here manually."""
        super().destroy()

    def set_collider(self, collider: ColliderComponent):
        """Swap in a different ColliderComponent for this actor."""
        self.remove_component(self._collider)
        self._collider = self.add_component(collider)
        self._collider.on_begin_overlap.bind(self._on_collision_begin)
        self._collider.on_end_overlap.bind(self._on_collision_end)
