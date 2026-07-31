

from typing import Any

from Engine.ActorSubsystem.Components.component import Component
from Engine.InputSubsystem.inputsubsystem import Input
from Engine.LogSubsystem.logsubsystem import Log



class CheatComponent(Component):
    """Cheat input."""

    def __init__(self):
        from assets.code.actors.ghost import BasicGhost
        from assets.code.actors.player import Player

        super().__init__()
        self.player: Player | None = None
        self.ghost: BasicGhost | None = None
        self._log = Log.get("main")

    def on_added(self, actor: Any):
        from assets.code.actors.ghost import BasicGhost
        from assets.code.actors.player import Player

        super().on_added(actor)
        if isinstance(actor, BasicGhost):
            self.ghost = actor
        if isinstance(actor, Player):
            self.player = actor

    def update(self, dt):
        from assets.code.actors.player import Player
        if Input.is_action_held("invinsible"):
            if self.player:
                self.player.invinsible = not self.player.invinsible
                self._log.info(f"Cheat: Invinsible: {self.player.invinsible}")

        if Input.is_action_held("level win"):
            if self.player:
                Player.end_game = True
                self._log.info(f"Cheat: Win level")

        if Input.is_action_held("ghost freeze"):
            if self.ghost:
                self.ghost.freeze_input()
                self._log.info(f"Cheat: Activate/Deactivate freeze")

        if Input.is_action_held("extra live"):
            if self.player:
                Player.current_player.add_live()
                self._log.info(f"Cheat: Add live")

        if Input.is_action_held("increase speed"):
            if self.player:
                self.player.speed_up()

        if Input.is_action_held("decrease speed"):
            if self.player:
                self.player.speed_down()
