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

        # TODO: example game 10 only


    def page_menu(self) -> None:
        """Menu page.

        Main page.
        Access:
            instructions
            in-game (current_normal_levels)
            page_scores
        Out:
            exit program
        """
        pass

    def page_instructions(self) -> None:
        """Instruction page.

        Access:
            None
        Out:
            Menu
        """
        pass

    def page_current_normal_levels(self) -> None:
        """Normal current level page.

        Access:
            Pause
        Out:
            Menu
        """
        # TODO start the current level
        pass

    def end_page_current_normal_levels(self) -> None:
        """End of normal page.

        Access (direct change):
            current_normal_levels
            player_name_for_score
        Out:
            None
        """
        # TODO next level or lose or end
        pass

    def page_pause(self) -> None:
        """Pause page.

        Access:
            None
        Out:
            in-game (current_normal_levels)
        """
        pass

    def page_player_name_for_score(self) -> None:
        """Player score + ask name. (and victory text if wins)
        
        Access:
            None
        Out:
            Menu
        """
        pass

    def page_scores(self) -> None:
        """Page for the scores.

        Access:
            None
        Out:
            Menu
        """
        # TODO: read file scores then show it
        pass
