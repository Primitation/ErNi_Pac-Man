"""Game instance."""

from game.game_instance import player, score
from game.game_instance.game_config import GameConfig
from game.game_instance.game_mode import GameModeNormalLevels
from game.game_instance.player import Player


class GameInstance:
    """Instance of the game."""
    def __init__(self, config: GameConfig) -> None:
        """Initialize the instance of the game.
        
        Args:
            config: the configs for the game.
        """
        self._current_player = Player(config)
        self._game_mode_normal = GameModeNormalLevels(config.level_options)

        # TODO load here ?