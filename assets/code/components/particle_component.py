from Engine import Component
from Engine import Particles


class ParticleTrailComponent(Component):
    """Emits a small particle puff behind whatever actor it's
    attached to, while that actor is moving.

    Generic — doesn't care what's driving the movement (player
    input, AI, physics). It just reads actor.velocity and
    actor.rotation each frame, so it drops onto anything that has
    those two (e.g. anything with a MovementComponent /
    FaceDirectionComponent) without knowing about Player at all.

    Attach this AFTER whatever sets rotation for the frame (e.g.
    FaceDirectionComponent) — components update in the order they
    were added, so this one needs to run later to see this frame's
    rotation instead of last frame's.
    """

    def __init__(
        self,
        interval: float = 0.05,
        count: int = 3,
        color=0xAAFFFF33,
        speed=(10.0, 30.0),
        size=(2.0, 4.0),
        life=(0.15, 0.3),
        spread: float = 40.0,
        min_speed: float = 1.0,
        enabled: bool = True,
    ):
        super().__init__(enabled)

        self.interval = interval
        self.count = count
        self.color = color
        self.speed = speed
        self.size = size
        self.life = life
        self.spread = spread
        self.min_speed = min_speed

        self._timer = 0.0

    def update(self, dt):
        actor = self.actor
        velocity = getattr(actor, "velocity", None)

        moving = (
            velocity is not None
            and (velocity.x ** 2 + velocity.y ** 2) ** 0.5 > self.min_speed
        )

        if not moving:
            self._timer = 0.0
            return

        self._timer += dt / 1000.0

        if self._timer < self.interval:
            return

        self._timer = 0.0

        rotation = getattr(actor, "rotation", 0.0)

        Particles.emit(
            actor.position,
            count=self.count,
            color=self.color,
            speed=self.speed,
            size=self.size,
            life=self.life,
            direction=rotation + 180,
            spread=self.spread,
        )
