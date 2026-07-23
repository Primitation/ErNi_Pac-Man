from .actor import Actor
from Engine import on_end_of_anim
from Engine import Vector2, Input
from Engine import AnimatedSpriteComponent
from ..components.movement_components import (
    MovementComponent, PlayerMovementInput, FaceDirectionComponent)


class Player(Actor):
    """A player-controlled Actor, moved via the Input subsystem."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 200.0,
    ):
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
        )

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd/PacManAssets-PacMan.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=4, loop=True, start_frame=0
            )
        )

        # Movement is now delegated to generic components:
        # MovementComponent handles the physics (direction -> velocity),
        # PlayerMovementInput reads Input and feeds it a direction,
        # FaceDirectionComponent turns velocity into a facing rotation.
        self.movement = self.add_component(MovementComponent(speed=speed))
        self.add_component(PlayerMovementInput())
        self.add_component(FaceDirectionComponent())

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

        # Components (added above) handle movement/rotation each frame
        # via their own update() calls, so Player.update just needs to
        # check its own state and defer to Actor for position integration.
        super().update(dt)

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()
