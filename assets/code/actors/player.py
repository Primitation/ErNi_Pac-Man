from typing import Any

from Engine.LogSubsystem.logsubsystem import Log
from Engine.World.world import World
from assets.code.actors.ghost import BasicGhost
from assets.code.actors.pacgum import Pacgum, SuperPacgum
from assets.code.components.cheat_components import CheatComponent
from game.game_instance.player_information import PlayerInformation

from .actor import Actor
from Engine import on_end_of_anim
from Engine import Vector2
from Engine import AnimatedSpriteComponent
from ..components.movement_components import (
    GridMovementComponent, PlayerGridInput, FaceDirectionComponent)
from threading import Timer


class Player(Actor):
    """A player-controlled Actor, moved via the Input subsystem."""

    current_player: PlayerInformation | None = None
    current_level: str = "None"
    end_game: bool = False
    end_level: bool = False
    quit: bool = False

    _fps: int = 16

    @property
    def fps(self) -> int:
        """fps"""
        if self.movement.is_moving:
            return self._fps
        return 0

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Player",
        speed: float = 100.0,
        static: bool = False
    ) -> None:
        """Initialize player.

        Args:
            position: position
            velocity: velocity
            scale: scale
            tag: tag
            speed: speed
            static: static
        """
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag="Player",
            static=static
        )
        self._start_super_pacman: float | None = None

        # Movement components
        self.movement = self.add_component(GridMovementComponent(speed=100))
        self.add_component(PlayerGridInput())
        self.add_component(FaceDirectionComponent())
        self._invinsible = False
        self._super_pacman = False
        self._super_pacman_timer: Timer | None = None
        self.add_component(CheatComponent())
        self._base_speed = self.movement.speed

        self.animation = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets/pacman_hd"
                "/PacManAssets-PacMan.png",
                frame_width=32, frame_height=32,
                frame_count=4, fps=self.fps, loop=True, start_frame=0,
                center=True,  # box is centered on actor.position, unrotated
            )
        )

    @on_end_of_anim(lambda self: self.destroy_after_dead())
    def dead(self, component: Any) -> None:
        """Action on dead.

        Args:
            component: component
        """
        component.set_animation(
            "assets/texture/spritesheets/pacman_hd/PacManAssets-PacMan.png",
            frame_width=32,
            frame_height=32,
            frame_count=8,
            fps=4,
            loop=False,
            start_frame=4
        )

    @property
    def invinsible(self) -> bool:
        """Returns if invinsible.

        Returns:
            Returns if invinsible.
        """
        return self._invinsible

    @invinsible.setter
    def invinsible(self, value: bool) -> None:
        """Invinsible setter."""
        self._invinsible = value
        self.change_ghosts_mode()

    @property
    def super_pacman(self) -> bool:
        """Super pacman property."""
        return self._super_pacman

    @super_pacman.setter
    def super_pacman(self, value: bool) -> None:
        """Super pacman setter."""
        if self._super_pacman_timer:
            self._super_pacman_timer.cancel()
            self._super_pacman_timer = None

        self._super_pacman = value

        if value:
            self._super_pacman_timer = Timer(
                self._super_pacman_time(),
                lambda: setattr(self, "super_pacman", False)
            )
            self._super_pacman_timer.start()

        self.change_ghosts_mode()

    def change_ghosts_mode(self) -> None:
        """Chenge ghosts mode."""
        edible = self.super_pacman or self.invinsible

        ghosts = World.find_all(BasicGhost)

        Log.get("main").debug(
            f"Changing ghost mode: edible={edible}, ghosts={len(ghosts)}"
        )

        for ghost in ghosts:
            ghost.edible = edible

    @staticmethod
    def game_ended() -> bool:
        """Returns if game ended.

        Returns:
            Returns if game ended.
        """
        return Player.end_game or Player.quit or Player.end_level

    def update(self, dt: float) -> None:
        """Updates.

        Args:
            dt: dt time
        """

        super().update(dt)
        if self.animation.fps != self.fps:
            self.animation.set_fps(self.fps)
        if World.find(Pacgum) is None:
            Log.get("main").success("No more pacgum.")
            Player.end_level = True

    def _super_pacman_time(self) -> float:
        """Returns super pacman time.

        Returns:
            Returns super pacman time.
        """
        return 10

    def _is_super_pacman(self) -> bool:
        """Returns if is super pacman.

        Returns:
            Returns if is super pacman.
        """
        return (self.super_pacman or self.invinsible)

    @staticmethod
    def set_player_information(player: PlayerInformation | None) -> None:
        """Set player information.

        Args:
            player: player
        """
        Player.current_player = player

    def destroy_after_dead(self) -> None:
        """Destroy after dead."""
        self.destroy()
        Player.end_game = True

    def destroy(self) -> None:
        """Destroy the player."""
        self.logger.debug("destroy")
        super().destroy()

    def _on_collision_begin(self, self_collider: Any,
                            other_collider: Any) -> None:
        """Actions on collision.

        Args:
            self_collider: self collider
            other_collider: other collider
        """
        if Player.current_player is None:
            Log.get("main").error("Player._on_collision_begin:"
                                  "no player registered !")
            return
        if not Player.current_player.is_alive():
            return
        if isinstance(other_collider.owner, Pacgum):
            Player.current_player.score_info.eat_pacgum()
        elif isinstance(other_collider.owner, SuperPacgum):
            Player.current_player.score_info.eat_super_pacgum()
            self.super_pacman = True
        elif isinstance(other_collider.owner, BasicGhost):
            if other_collider.owner.dead:
                return
            if self._is_super_pacman():
                Player.current_player.score_info.eat_ghost()
                # TODO: temporary respawning
                other_collider.owner.dead = True
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
        """Speed up the player."""
        self.movement.speed += self._base_speed * 0.1

    def speed_down(self) -> None:
        """Speed down the player."""
        self.movement.speed = max(
            0, self.movement.speed - self._base_speed * 0.1)
