from Engine.LogSubsystem.logsubsystem import Log
from assets.code.actors.ghost import BasicGhost
from assets.code.actors.pacgum import Pacgum, SuperPacgum
from game.game_instance.player_information import PlayerInformation

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

    current_player: PlayerInformation | None = None

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

    @staticmethod
    def set_player_information(player: PlayerInformation | None) -> None:
        Player.current_player = player

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()

    def _on_collision_begin(self, self_collider, other_collider):
        if Player.current_player is None:
            Log.get("main").error(f"Player._on_collision_begin: no player registered !")
            return
        if isinstance(other_collider.owner, Pacgum):
            Player.current_player.score_info.eat_pacgum()
            other_collider.owner.destroy()
        elif isinstance(other_collider.owner, SuperPacgum):
            Player.current_player.score_info.eat_super_pacgum()
            other_collider.owner.destroy()
        elif isinstance(other_collider.owner, BasicGhost):
            # TODO: super pacman
            Player.current_player.score_info.eat_ghost()
            other_collider.owner.destroy()
        Log.get("main").info(f"Player._on_collision_begin score "
                             f"{Player.current_player.score_info.score}.")