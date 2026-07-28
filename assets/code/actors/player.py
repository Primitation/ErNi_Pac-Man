from .actor import Actor
from Engine import on_end_of_anim
from Engine import Vector2, Input
from Engine import AnimatedSpriteComponent
from ..components.movement_components import (
    MovementComponent, PlayerMovementInput, FaceDirectionComponent)
from ..components.particle_component import ParticleTrailComponent
from ..components.origin_marker_component import OriginMarkerComponent


class Player(Actor):
    """A player-controlled Actor, moved via the Input subsystem."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 100.0,
        static: bool = False,
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            static=static
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd"
                "/PacManAssets-PacMan.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=0,
                center=True,  # box is centered on actor.position, unrotated
            )
        )

        # Movement components
        self.movement = self.add_component(MovementComponent(speed=speed))
        self.add_component(PlayerMovementInput())
        self.add_component(FaceDirectionComponent())

        # Particle trail with rotation
        self.add_component(ParticleTrailComponent(
            local_offset=(-16, 0),    # Offset to the left of the actor center
            offset_rotates=True,      # Rotate with the actor
            interval=0.02,
            count=3,
            color=0xFFFF8800,         # Orange
            speed=(20, 50),
            size=(3, 6),
            life=(0.2, 10),
            spread=45.0,
            min_speed=10.0,
            emit_direction="backward"  # Emit behind the actor
        ))

        # Debug: red dot at the actor's raw origin (actor.position),
        # so we can see whether the sprite is actually centered on it
        # or drawn with its top-left corner there. Remove once
        # confirmed.
        self.add_component(OriginMarkerComponent(color=0xFFFF0000, size=6.0))

        Input.bind_action("dead", [Input.KEYS["t"]])

    @on_end_of_anim(lambda self: self.destroy())
    def dead(self, animation: AnimatedSpriteComponent):
        animation.set_animation(
            "assets/texture/spritesheets/pacman_hd/PacManAssets-PacMan.png",
            frame_width=32, frame_height=32,
            frame_count=8, fps=4, loop=False, start_frame=4
        )

    def update(self, dt):
        if Input.is_action_triggered("dead"):
            self.dead(self.animation)
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()
