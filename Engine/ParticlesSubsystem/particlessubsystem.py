import math
import random

from .. import Vector2, Log, log_timing


class Particle:
    """Plain data — no Component/Actor machinery. A burst can be
    dozens of these at once and they only live a fraction of a
    second, so keeping them cheap matters more than giving them the
    full actor lifecycle."""

    __slots__ = (
        "position", "velocity", "color", "size",
        "life", "max_life", "gravity", "fade",
    )

    def __init__(self, position, velocity, color, size, life, gravity, fade):
        self.position = position
        self.velocity = velocity
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity
        self.fade = fade

    @property
    def t(self):
        """0.0 at spawn, 1.0 the instant it dies — drives the fade
        curve in ParticleSubsystem.render()."""
        if self.max_life <= 0:
            return 1.0
        return 1.0 - max(0.0, self.life) / self.max_life


class ParticleSubsystem:
    """One-shot particle bursts for visual feedback — impacts,
    deaths, pickups, whatever needs a bit of juice. Not tied to
    Actors/Components at all: emit() fires a burst of plain
    position/velocity/color/lifetime particles that this subsystem
    itself ticks and draws as flat-colored squares
    (Renderer.draw_rect), no sprite required.

    Call update(dt) once per frame (same dt-in-ms convention as
    ActorSubsystem/CollisionSubsystem) and render(Renderer) once per
    frame, after Renderer.render(world) so particles draw on top.
    """

    def __init__(self, max_particles: int = 2000):
        self._particles = []
        self.max_particles = max_particles
        self._logger = Log.get("particles")

    def emit(
        self,
        position,
        count: int = 12,
        color=0xFFFFFFFF,
        speed=(50.0, 150.0),
        size=(2.0, 4.0),
        life=(0.25, 0.5),
        direction: float = 0.0,
        spread: float = 360.0,
        gravity: float = 0.0,
        fade: bool = True,
    ):
        """Spawn a one-shot burst of `count` particles at `position`
        (a Vector2 — copied per-particle, not shared/mutated).

        speed / size / life: (min, max) ranges. Each particle rolls
        its own value uniformly inside that range so a burst doesn't
        look perfectly uniform.

        direction: center angle in degrees the burst is aimed along
        (0 = +x/right, 90 = +y/down — same convention as
        AActor.rotation). spread: total cone width in degrees around
        direction — 360 (default) scatters evenly in every direction;
        a small spread gives a directional spray, e.g. sparks off a
        wall bounce.

        color: a single 0xAARRGGBB int, or a list/tuple of them to
        pick from randomly per particle (e.g. a couple of yellow/
        orange shades for an explosion).

        gravity: units/sec^2 added to vertical velocity every frame —
        0 for particles that just drift on their initial velocity,
        positive to have them arc/fall.

        fade: if True, alpha ramps from the color's own alpha down to
        0 over the particle's lifetime; if False it's constant until
        the particle just disappears.
        """

        if len(self._particles) >= self.max_particles:
            return

        colors = color if isinstance(color, (list, tuple)) else (color,)
        count = min(count, self.max_particles - len(self._particles))

        for _ in range(count):
            angle = math.radians(direction + random.uniform(-spread / 2, spread / 2))
            spd = random.uniform(*speed)

            velocity = Vector2(math.cos(angle) * spd, math.sin(angle) * spd)

            self._particles.append(
                Particle(
                    position=Vector2(position.x, position.y),
                    velocity=velocity,
                    color=random.choice(colors),
                    size=random.uniform(*size),
                    life=random.uniform(*life),
                    gravity=gravity,
                    fade=fade,
                )
            )

    def clear(self):
        """Kill every live particle immediately (e.g. on level
        reset)."""
        self._particles.clear()

    @log_timing()
    def update(self, dt):
        """Call once per frame, dt in ms — same convention as
        ActorSubsystem.update(dt)."""

        seconds = dt / 1000.0
        alive = []

        for particle in self._particles:
            particle.life -= seconds

            if particle.life <= 0:
                continue

            particle.velocity.y += particle.gravity * seconds
            particle.position += particle.velocity * seconds

            alive.append(particle)

        self._particles = alive

    def render(self, renderer):
        """Call once per frame — draws every live particle as a
        small flat-colored square centered on its position, fading
        alpha out over its lifetime when fade=True. Call this after
        renderer.render(world) so particles draw on top of actors."""

        for particle in self._particles:
            color = particle.color

            if particle.fade:
                base_alpha = (color >> 24) & 0xFF
                alpha = int(base_alpha * (1.0 - particle.t))
                color = (alpha << 24) | (color & 0x00FFFFFF)

            half = particle.size / 2
            renderer.draw_rect(
                particle.position.x - half,
                particle.position.y - half,
                particle.size,
                particle.size,
                color,
            )

    @property
    def count(self):
        return len(self._particles)


# Global particle system
Particles = ParticleSubsystem()
