# particlessubsystem.py
import math
import random
from typing import Optional, List, Any, Dict, Tuple, Union

from .. import Vector2, Log, log_timing
from .. import Assets, SpriteSheetKey, Animation


class Particle:
    """Plain data — no Component/Actor machinery."""

    __slots__ = (
        "position", "velocity", "color", "size",
        "life", "max_life", "gravity", "fade",
        "rotation", "angular_velocity", "face_velocity",
        "sprite_path", "scale",
        "_animation_key", "_animation", "_animation_time",
        "_fps", "_loop",
    )

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        color: int,
        size: float,
        life: float,
        gravity: float,
        fade: bool,
        rotation: float = 0.0,
        angular_velocity: float = 0.0,
        face_velocity: bool = False,
        sprite_path: Optional[str] = None,
        scale: float = 1.0,
        animation_key: Optional[SpriteSheetKey] = None,
        fps: float = 10.0,
        loop: bool = True,
    ) -> None:
        self.position = position
        self.velocity = velocity
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity
        self.fade = fade

        self.rotation = rotation
        self.angular_velocity = angular_velocity
        self.face_velocity = face_velocity

        self.sprite_path = sprite_path
        self.scale = scale

        self._animation_key = animation_key
        self._animation: Optional[Animation] = None
        self._animation_time = 0.0
        self._fps = fps
        self._loop = loop

    @property
    def t(self) -> float:
        """0.0 at spawn, 1.0 the instant it dies."""
        if self.max_life <= 0:
            return 1.0
        return 1.0 - max(0.0, self.life) / self.max_life

    @property
    def sprite(self) -> Optional[Any]:
        """This particle's current sprite, or None."""
        if self.sprite_path is not None:
            return Assets.get(self.sprite_path)

        if self._animation_key is not None:
            if self._animation is None:
                frames = \
                    Assets.get(self._animation_key)  # type: ignore[arg-type]
                if frames is None:
                    return None
                self._animation = Animation(frames,
                                            fps=self._fps,
                                            loop=self._loop)
            return self._animation.frame_at(self._animation_time)

        return None


class ParticleSubsystem:
    """One-shot particle bursts for visual feedback."""

    def __init__(self, max_particles: int = 2000) -> None:
        self._particles: List[Particle] = []
        self.max_particles = max_particles
        self._logger = Log.get("particles")

    def emit(
        self,
        position: Vector2,
        count: int = 12,
        color: Union[int, List[int], Tuple[int, ...]] = 0xFFFFFFFF,
        speed: Tuple[float, float] = (50.0, 150.0),
        size: Tuple[float, float] = (2.0, 4.0),
        life: Tuple[float, float] = (0.25, 0.5),
        direction: float = 0.0,
        spread: float = 360.0,
        gravity: float = 0.0,
        fade: bool = True,
        sprite: Optional[Union[str, List[str], Tuple[str, ...]]] = None,
        animation: Optional[Dict[str, Any]] = None,
        scale: Tuple[float, float] = (1.0, 1.0),
        rotation: Tuple[float, float] = (0.0, 0.0),
        angular_velocity: Tuple[float, float] = (0.0, 0.0),
        face_velocity: bool = False,
    ) -> None:
        """Spawn a one-shot burst of particles."""
        if len(self._particles) >= self.max_particles:
            return

        colors = color if isinstance(color, (list, tuple)) else (color,)
        count = min(count, self.max_particles - len(self._particles))

        sprite_paths: Optional[Tuple[str, ...]] = None
        if sprite is not None:
            sprite_paths = tuple(sprite) \
                if isinstance(sprite, (list, tuple)) else (sprite,)
            for path in sprite_paths:
                Assets.queue(path)

        animation_key: Optional[SpriteSheetKey] = None
        anim_fps, anim_loop = 10.0, True

        if sprite_paths is None and animation is not None:
            animation_key = SpriteSheetKey(
                animation["path"],
                animation["frame_width"],
                animation["frame_height"],
                animation.get("frame_count"),
                animation.get("columns"),
                animation.get("start_frame", 0),
            )
            anim_fps = animation.get("fps", 10.0)
            anim_loop = animation.get("loop", True)
            Assets.queue(animation_key)  # type: ignore[arg-type]

        for _ in range(count):
            spawn_angle = direction + random.uniform(-spread / 2, spread / 2)
            angle = math.radians(spawn_angle)
            spd = random.uniform(*speed)

            velocity = Vector2(math.cos(angle) * spd, math.sin(angle) * spd)

            start_rotation = spawn_angle \
                if face_velocity else random.uniform(*rotation)

            self._particles.append(
                Particle(
                    position=Vector2(position.x, position.y),
                    velocity=velocity,
                    color=random.choice(colors),
                    size=random.uniform(*size),
                    life=random.uniform(*life),
                    gravity=gravity,
                    fade=fade,
                    rotation=start_rotation,
                    angular_velocity=random.uniform(*angular_velocity),
                    face_velocity=face_velocity,
                    sprite_path=random.choice(sprite_paths)
                    if sprite_paths else None,
                    scale=random.uniform(*scale),
                    animation_key=animation_key,
                    fps=anim_fps,
                    loop=anim_loop,
                )
            )

    def clear(self) -> None:
        """Kill every live particle immediately."""
        self._particles.clear()

    @log_timing()
    def update(self, dt: float) -> None:
        """Call once per frame, dt in ms."""
        seconds = dt / 1000.0
        alive: List[Particle] = []

        for particle in self._particles:
            particle.life -= seconds

            if particle.life <= 0:
                continue

            particle.velocity.y += particle.gravity * seconds
            particle.position += particle.velocity * seconds

            if particle._animation_key is not None:
                particle._animation_time += dt

            if particle.face_velocity:
                particle.rotation = math.degrees(
                    math.atan2(particle.velocity.y, particle.velocity.x)
                )

            particle.rotation += particle.angular_velocity * seconds
            alive.append(particle)

        self._particles = alive

    def render(self, renderer: Any) -> None:
        """Call once per frame."""
        for particle in self._particles:
            sprite = particle.sprite

            if sprite is not None:
                if particle.fade:
                    base_alpha = (
                        (particle.color >> 24) & 0xFF
                        if isinstance(particle.color, int) else 255
                    )
                    if base_alpha * (1.0 - particle.t) < 1:
                        continue

                width = sprite.width * particle.scale
                height = sprite.height * particle.scale

                top_left = Vector2(
                    particle.position.x - width / 2,
                    particle.position.y - height / 2,
                )

                renderer.draw_sprite(
                    sprite,
                    top_left,
                    particle.scale,
                    particle.rotation,
                    (0.5, 0.5),
                )
                continue

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
    def count(self) -> int:
        return len(self._particles)


Particles = ParticleSubsystem()
