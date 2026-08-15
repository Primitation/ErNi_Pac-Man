from typing import Any

from Engine import Component
from Engine import Particles, Vector2, Log


class ParticleTrailComponent(Component):
    """Emits particles behind a moving actor."""

    def __init__(
        self,
        interval: float = 0.05,
        count: int = 3,
        color: int = 0xAAFFFFFF,
        speed: tuple[float, float] = (10.0, 30.0),
        size: tuple[float, float] = (2.0, 4.0),
        life: tuple[float, float] = (0.15, 0.5),
        spread: float = 90.0,
        min_speed: float = 1.0,
        enabled: bool = True,
        local_offset: tuple[float, float] = (0.0, 0.0),
        offset_rotates: bool = True,
        emit_direction: str = "backward",
        emit_on_start: bool = False,
        emit_on_stop: bool = False
    ) -> None:
        """Initialize particle trail.

        Args:
            interval: interval
            count: count
            color: color
            speed: speed
            float]=(10.0: float]=(10.0
            30.0): 30.0)
            size: size
            float]=(2.0: float]=(2.0
            4.0): 4.0)
            life: life
            float]=(0.15: float]=(0.15
            0.5): 0.5)
            spread: spread
            min_speed: min speed
            enabled: enabled
            local_offset: local offset
            float]=(0.0: float]=(0.0
            0.0): 0.0)
            offset_rotates: offset rotates
            emit_direction: emit direction
            emit_on_start: emit on start
            emit_on_stop: emit on stop
        """
        super().__init__(enabled)

        self.interval = interval
        self.count = count
        self.color = color
        self.speed = speed
        self.size = size
        self.life = life
        self.spread = spread
        self.min_speed = min_speed
        self.local_position = local_offset
        self.offset_rotates = offset_rotates
        self.emit_direction = emit_direction
        self.emit_on_start = emit_on_start
        self.emit_on_stop = emit_on_stop

        self._timer = 0.0
        self._was_moving = False
        self._start_emitted = False
        self._logger = Log.get("particle_trail")

    def on_added(self, actor: Any) -> None:
        """Actions on added.

        Args:
            actor: actor
        """
        super().on_added(actor)
        if self.emit_on_start:
            self._emit_burst()

    def _get_emit_angle(self) -> float:
        """Get the angle for particle emission.

        Returns:
            Returns the angle for particle emission.
        """
        actor = self.actor
        if actor is None:
            return 0.0

        rotation = getattr(actor, "rotation", 0.0)

        if self.emit_direction == "backward":
            return rotation + 180
        elif self.emit_direction == "forward":
            return rotation
        elif self.emit_direction == "random":
            return 0.0
        else:
            try:
                return rotation + float(self.emit_direction)
            except (ValueError, TypeError):
                return rotation + 180

    def _emit_burst(self) -> None:
        """Emit a single particle burst."""
        if self.actor is None:
            return

        pos_x, pos_y = self.get_world_position()
        position = Vector2(pos_x, pos_y)

        if self.emit_direction == "random":
            direction = 0.0
            spread = 360.0
        else:
            direction = self._get_emit_angle()
            spread = self.spread

        Particles.emit(
            position,
            count=self.count,
            color=self.color,
            speed=self.speed,
            size=self.size,
            life=self.life,
            direction=direction,
            spread=spread,
        )

    def update(self, dt: float) -> None:
        """Update trail emission.

        Args:
            dt: dt
        """
        actor = self.actor
        velocity = getattr(actor, "velocity", None)

        moving = (
            velocity is not None
            and (velocity.x ** 2 + velocity.y ** 2) ** 0.5 > self.min_speed
        )

        if self.emit_on_stop and self._was_moving and not moving:
            self._emit_burst()

        self._was_moving = moving

        if not moving:
            self._timer = 0.0
            return

        self._timer += dt / 1000.0

        if self._timer < self.interval:
            return

        self._timer = 0.0
        self._emit_burst()
