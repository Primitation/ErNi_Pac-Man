"""Game instance."""

from Engine.LogSubsystem.logsubsystem import Log
from game.game_instance.player import PlayerInformation
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

        # TODO load here ? or not ?
        self._game_mode_normal.reset()
        level_instance = self._game_mode_normal.next_level()
        while level_instance is not None:
            level_instance.load()
            level_instance = self._game_mode_normal.next_level()
        self._game_mode_normal.reset()

        # TODO: example game 10 only


    def _start_normal_levels(self) -> None:
        """Initialize the game and start.
        """
        self._current_player.reset()
        self._game_mode_normal.reset()
        """TODO: this is an example of loop with levels."""
        log = Log.get("main")
        log.info("GameInstance: start normal levels")
        level_name = self._game_mode_normal.current_level
        level_instance = self._game_mode_normal.next_level()
        while self._current_player.is_alive() and level_instance is not None:
            log.info(f"GameInstance: start normal level {level_name}")
            level_instance.start(self._current_player)
            level_instance = self._game_mode_normal.next_level()
        log.info("GameInstance: end normal levels")
        # TODO: call score page
        log.info("GameInstance: Calls player score saving page (TODO)")
        self.page_player_name_for_score()

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
        log = Log.get("main")
        log.info("GameInstance: Menu (TODO)")
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
        log = Log.get("main")
        log.info("GameInstance: Ask player name for score saving (TODO)")
        # TODO: got to page menu
        self.page_menu()

    def page_scores(self) -> None:
        """Page for the scores.

        Access:
            None
        Out:
            Menu
        """
        # TODO: read file scores then show it
        pass
