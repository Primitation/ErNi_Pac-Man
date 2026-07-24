from Engine import Component
from Engine import Particles


class OriginMarkerComponent(Component):
    """Debug aid — draws a small solid dot at the actor's raw
    position (self.actor.position) every frame. Deliberately reads
    actor.position directly, not any component's rotated/offset
    get_world_position() — the point is to see exactly where the
    actor's own origin sits, e.g. to confirm whether a sprite is
    centered on it or drawn from it as a top-left corner.

    Piggybacks on ParticleSubsystem (re-emits a single short-lived,
    non-fading, zero-velocity particle every frame) instead of
    adding a new render hook — cheap and correctly timed since
    Particles already renders in the same frame as everything else.

    Remove this component once you're done checking — it's a
    debugging tool, not something to ship."""

    def __init__(self, color=0xFFFF0000, size=6.0, enabled=True):
        super().__init__(enabled)
        self.color = color
        self.size = size

    def update(self, dt):
        Particles.emit(
            self.actor.position,
            count=1,
            color=self.color,
            speed=(0.0, 0.0),
            size=(self.size, self.size),
            life=(0.1, 0.1),
            spread=0.0,
            gravity=0.0,
            fade=False,
        )
