from Engine import AActor, Vector2, Collision
from Engine.CollisionSubsystem.collider import Collider


class Actor(AActor):
    """An Base Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        sprite_path: str,
        tag: str = "Actor",

    ):
        super().__init__(
            position=position,
            scale=scale,
        )

        self.velocity = velocity
        self.set_sprite(sprite_path)

        # The "resting" scale to animate around. Kept separate from
        # self.scale (which the renderer actually reads) so the punch
        # animation can freely push self.scale up and back down.
        self.base_scale = Vector2(scale.x, scale.y)

        # Squash/pop animation state, triggered on collision.
        self._punch_time = 0.0
        self._punch_duration = 0.18
        self._punch_strength = 0.6
        self._punching = False
        # Register with collision system
        self._collider = Collision.register(
            owner=self,
            get_rect=self.get_rect,
            tag="Actor",
            collides_with=None,
            blocking=False,
            bounce=0.8,
            static=False,
            enabled=True
        )

        # Bind collision events for debugging
        self._collider.on_begin_overlap.bind(self._on_collision_begin)
        self._collider.on_end_overlap.bind(self._on_collision_end)

    def get_rect(self):
        """Return a rect as (x, y, width, height).

        Uses base_scale rather than the animated self.scale — the
        punch effect is purely visual, so the collider stays a
        constant size and doesn't feed back into itself (a growing
        collider would trigger more collisions, which would retrigger
        more growth, etc.)."""

        sprite = self.sprite
        if sprite is not None:
            width = sprite.width * self.base_scale.x
            height = sprite.height * self.base_scale.y
        else:
            # Fallback to scale if sprite not loaded yet
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
        """Update bouncer position and handle wall bouncing."""

        # Move the bouncer
        self.position += (
            self.velocity * (dt / 1000)
        )

    def destroy(self):
        """Clean up this bouncer."""
        Collision.unregister(self._collider)
        self.alive = False

    def set_collider(self, _collider: Collider):
        if self._collider:
            Collision.unregister(self._collider)
        self.set_collider = _collider
