from Engine import Component
from Engine import Particles, Vector2, Log


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
        color=0xAAFFFFFF,
        speed=(10.0, 30.0),
        size=(2.0, 4.0),
        life=(0.15, 0.5),
        spread: float = 90.0,
        min_speed: float = 1.0,
        enabled: bool = True,
        local_offset=(0.0, 0.0),
        offset_rotates: bool = True,
        emit_direction: str = "backward",
        emit_on_start: bool = False,
        emit_on_stop: bool = False,
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
        self.local_position = local_offset
        self.offset_rotates = offset_rotates
        self.emit_direction = emit_direction
        self.emit_on_start = emit_on_start
        self.emit_on_stop = emit_on_stop

        self._timer = 0.0
        self._was_moving = False
        self._start_emitted = False
        self._logger = Log.get("particle_trail")

    def on_added(self, actor):
        super().on_added(actor)
        if self.emit_on_start:
            self._emit_burst()

    def _get_emit_angle(self):
        """Get the angle for particle emission based on emit_direction setting."""
        actor = self.actor
        if actor is None:
            return 0.0
            
        rotation = getattr(actor, "rotation", 0.0)
        
        if self.emit_direction == "backward":
            # Emit behind the actor (opposite of facing direction)
            return rotation + 180
        elif self.emit_direction == "forward":
            # Emit in front of the actor (facing direction)
            return rotation
        elif self.emit_direction == "random":
            # Completely random direction
            return 0.0
        else:
            # Custom angle (in degrees) relative to actor's rotation
            try:
                return rotation + float(self.emit_direction)
            except (ValueError, TypeError):
                return rotation + 180

    def _emit_burst(self):
        """Emit a single particle burst at the current position."""
        if self.actor is None:
            return
            
        # Use the component's world position (handles rotation of the offset)
        pos_x, pos_y = self.get_world_position()
        position = Vector2(pos_x, pos_y)
        
        # Get emission direction for particle velocity
        if self.emit_direction == "random":
            direction = 0.0
            spread = 360.0
        else:
            direction = self._get_emit_angle()
            spread = self.spread
        
        # Emit particles from the rotated position
        # The particles will move independently based on their velocity
        Particles.emit(
            position,           # Position where particles spawn (rotated offset)
            count=self.count,
            color=self.color,
            speed=self.speed,   # Speed of particles (they move independently)
            size=self.size,
            life=self.life,
            direction=direction,  # Direction particles fly
            spread=spread,      # Spread of particles
        )

    def update(self, dt):
        actor = self.actor
        velocity = getattr(actor, "velocity", None)

        # Check if moving (velocity magnitude > min_speed)
        moving = (
            velocity is not None
            and (velocity.x ** 2 + velocity.y ** 2) ** 0.5 > self.min_speed
        )

        # Handle emit_on_stop
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
