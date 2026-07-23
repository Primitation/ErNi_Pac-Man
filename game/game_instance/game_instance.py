"""Game instance."""

from game.game_instance import PlayerInformation
from game.game_instance.game_config import GameConfig
from game.game_instance.game_mode import GameModeNormalLevels


class GameInstance:
    """Instance of the game."""
    def __init__(self, config: GameConfig) -> None:
        """Initialize the instance of the game.

        Args:
            config: the configs for the game.
        """
        self._current_player = PlayerInformation(config)
        self._game_mode_normal = GameModeNormalLevels(config.level_options)

        # TODO load here ?
