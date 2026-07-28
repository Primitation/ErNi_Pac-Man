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

    ):
        super().__init__(
            position=position,
            scale=scale,
            static=static
        )

        self.velocity = velocity

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
                tag="Actor",
                collides_with=None,
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
        """Return a rect as (x, y, width, height).

        Uses base_scale rather than the animated self.scale
        Reads size off whatever sprite/animated-sprite component this
        actor happens to have;"""

        sprite_component = (
            self.get_component(SpriteComponent)
            or self.get_component(AnimatedSpriteComponent)
        )

        if sprite_component is not None and sprite_component.sprite is not None:
            width = sprite_component.width * self.base_scale.x
            height = sprite_component.height * self.base_scale.y
        else:
            # Fallback if there's no sprite component yet, or its
            # sprite hasn't finished loading.
            width = self.base_scale.x
            height = self.base_scale.y

        return (
            self.position.x,
            self.position.y,
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
