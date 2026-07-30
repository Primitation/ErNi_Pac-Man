from .actor import Actor
from Engine import on_end_of_anim
from Engine import Vector2, Input
from Engine import AnimatedSpriteComponent
from ..components.movement_components import (
    GridMovementComponent, PlayerGridInput, FaceDirectionComponent)
from ..components.particle_component import ParticleTrailComponent
from ..components.origin_marker_component import OriginMarkerComponent


class Player(Actor):
    """A player-controlled Actor, moved via the Input subsystem."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Player",
        speed: float = 100.0,
        static: bool = False,
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag="Player",
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
        self.movement = self.add_component(GridMovementComponent(speed=100))
        self.add_component(PlayerGridInput())
        self.add_component(FaceDirectionComponent())

        Input.bind_action("dead", [Input.KEYS["t"]])

    @on_end_of_anim(lambda self: self.destroy())
    def dead(self, component):
        component.set_animation(
            "assets/texture/spritesheets/pacman_hd/PacManAssets-PacMan.png",
            frame_width=32,
            frame_height=32,
            frame_count=8,
            fps=4,
            loop=False,
            start_frame=4
        )

    def update(self, dt):
        if Input.is_action_triggered("dead"):
            self.dead()
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()
