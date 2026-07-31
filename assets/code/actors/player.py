from Engine.LogSubsystem.logsubsystem import Log
from Engine.World.world import World
from assets.code.actors.ghost import BasicGhost
from assets.code.actors.pacgum import Pacgum, SuperPacgum
from assets.code.components.cheat_components import CheatComponent
from game.game_instance.player_information import PlayerInformation

from .actor import Actor
from Engine import on_end_of_anim
from Engine import Vector2, Input
from Engine import AnimatedSpriteComponent
from ..components.movement_components import (
    GridMovementComponent, PlayerGridInput, FaceDirectionComponent)
from ..components.particle_component import ParticleTrailComponent
from ..components.origin_marker_component import OriginMarkerComponent
from time import perf_counter

class Player(Actor):
    """A player-controlled Actor, moved via the Input subsystem."""

    current_player: PlayerInformation | None = None
    current_level: str = "None"
    end_game: bool = False
    quit: bool = False

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
        self._start_super_pacman: float | None = None

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
        self.invinsible = False
        self.add_component(CheatComponent())
        self._base_speed = self.movement.speed

    @on_end_of_anim(lambda self: self.destroy_after_dead())
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

    @staticmethod
    def game_ended() -> bool:
        return Player.end_game or Player.quit

    def update(self, dt):
        super().update(dt)
        if World.find(Pacgum) is None:
            Log.get("main").success("No more pacgum.")
            Player.end_game = True

    def _super_pacman_time(self) -> float:
        return 10  # TODO: super pacmann time: here 10 seconds

    def _super_pacman(self) -> None:
        self._start_super_pacman = perf_counter()

    def _is_super_pacman(self) -> bool:
        return (self.invinsible
                or (self._start_super_pacman is not None and
                    (perf_counter() - self._start_super_pacman
                     <= self._super_pacman_time())))

    @staticmethod
    def set_player_information(player: PlayerInformation | None) -> None:
        Player.current_player = player

    def destroy_after_dead(self):
        self.destroy()
        Player.end_game = True

    def destroy(self):
        self.logger.debug("destroy")
        super().destroy()

    def _on_collision_begin(self, self_collider, other_collider) -> None:
        if Player.current_player is None:
            Log.get("main").error(f"Player._on_collision_begin: no player registered !")
            return
        if not Player.current_player.is_alive():
            return
        if isinstance(other_collider.owner, Pacgum):
            Player.current_player.score_info.eat_pacgum()
        elif isinstance(other_collider.owner, SuperPacgum):
            Player.current_player.score_info.eat_super_pacgum()
            self._super_pacman()
        elif isinstance(other_collider.owner, BasicGhost):
            if self._is_super_pacman():
                Player.current_player.score_info.eat_ghost()
                # TODO: temporary respawning
                other_collider.owner.position.x = (
                    other_collider.owner._start_position.x)
                other_collider.owner.position.y = (
                    other_collider.owner._start_position.y)
                other_collider.owner.movement.current_cell = None
                other_collider.owner.movement.stop()
            else:
                Player.current_player.loss_live()
                if Player.current_player.is_alive():
                    # TODO: temporary respawning
                    self.position.x = self._start_position.x
                    self.position.y = self._start_position.y
                    self.movement.current_cell = None
                    self.movement.stop()
                else:
                    self.dead(self.animation)
        Log.get("main").info(f"Player._on_collision_begin score "
                             f"{Player.current_player.score_info.score}.")

    def speed_up(self) -> None:
        self.movement.speed += self._base_speed * 0.1

    def speed_down(self) -> None:
            self.movement.speed -= self._base_speed * 0.1
