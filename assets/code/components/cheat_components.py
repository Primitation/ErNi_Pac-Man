from typing import Any

from Engine.ActorSubsystem.Components.component import Component
from Engine.InputSubsystem.inputsubsystem import Input
from Engine.LogSubsystem.logsubsystem import Log


class CheatComponent(Component):
    """Cheat input."""

    def __init__(self) -> None:
        """Initialize cheat  component."""
        from assets.code.actors.ghost import BasicGhost
        from assets.code.actors.player import Player

        super().__init__()
        self.player: Player | None = None
        self.ghost: BasicGhost | None = None
        self._log = Log.get("main")

    def on_added(self, actor: Any) -> None:
        """On added to actor.

        Args:
            actor: actor
        """
        from assets.code.actors.ghost import BasicGhost
        from assets.code.actors.player import Player

        super().on_added(actor)
        if isinstance(actor, BasicGhost):
            self.ghost = actor
        if isinstance(actor, Player):
            self.player = actor

    def update(self, dt: float) -> None:
        """Updates

        Args:
            dt: dt time.
        """
        from assets.code.actors.player import Player
        from Engine.ActorSubsystem.actorsubsystem import Actors

        if Input.is_action_triggered("invinsible"):
            if self.player:
                self.player.invinsible = not self.player.invinsible
                self._log.info(f"Cheat: Invinsible: {self.player.invinsible}")

        if Input.is_action_triggered("level win"):
            if self.player:
                Player.end_level = True
                self._log.info("Cheat: Win level")

        if Input.is_action_triggered("ghost freeze"):
            if self.ghost:
                self.ghost.freeze_input()
                self._log.info("Cheat: Activate/Deactivate freeze")

        if Input.is_action_triggered("extra live"):
            if self.player and Player.current_player:
                Player.current_player.add_live()
                self._log.info("Cheat: Add live")

        if Input.is_action_triggered("increase speed"):
            if self.player:
                self.player.speed_up()
                self._log.info("Cheat: speed up")

        if Input.is_action_triggered("decrease speed"):
            if self.player:
                self.player.speed_down()
                self._log.info("Cheat: speed down")

        if Input.is_action_triggered("time stop"):
            Actors.time_stop = not Actors.time_stop
            self._log.info(f"Cheat: Time stop: {Actors.time_stop}")
