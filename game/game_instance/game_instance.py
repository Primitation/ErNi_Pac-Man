"""Game instance."""

from Engine.LogSubsystem.logsubsystem import Log
from assets.code.actors.player import Player
from game.game_instance.score import Scores
from .player_information import PlayerInformation
from .game_config import GameConfig
from .game_mode import GameModeNormalLevels


class GameInstance:
    """Instance of the game."""
    def __init__(self, config: GameConfig) -> None:
        """Initialize the instance of the game.

        Args:
            config: the configs for the game.
        """
        self._config = config
        self._current_player = PlayerInformation(config)
        self._game_mode_normal = GameModeNormalLevels(config.levels_options)
        self._scores = Scores.load_scores(config)

        self._game_mode_normal.reset()
        level_instance = self._game_mode_normal.next_level()
        while level_instance is not None:
            level_instance.load()
            level_instance = self._game_mode_normal.next_level()
        self._game_mode_normal.reset()
        self.log = Log.get("main")

    def _start_normal_levels(self) -> bool:
        """Initialize the game and start.

        Returns:
            Returns True if the game ended normally, False if the player quit
        """
        Player.end_game = False
        Player.quit = False
        self._current_player.reset()
        self._game_mode_normal.reset()
        log = Log.get("main")
        log.info("GameInstance: start normal levels")
        level_instance = self._game_mode_normal.next_level()
        while not Player.quit and level_instance is not None:
            Player.end_level = False
            level_name = self._game_mode_normal.current_level
            log.info(f"GameInstance: start normal level {level_name}")
            level_instance.start(self._current_player, str(level_name))
            level_instance = self._game_mode_normal.next_level()
        log.info("GameInstance: end normal levels")
        return not Player.quit

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
        from assets.code.ui.mainmenu import MainMenu

        while True:
            result = MainMenu(self._scores).show()
            self.log.info(f"Menu closed with result: {result}")

            if result == "play":
                normal_end = self.page_current_normal_levels()
                if normal_end:
                    self.page_player_name_for_score()
                # falls back into the while loop -> menu shows again
            else:
                break  # "quit" or window closed some other way

    def page_current_normal_levels(self) -> bool:
        """Normal current level page.

        Returns:
            Returns True if the levels are played, else False for quit.
        In:
            Menu
        Access:
            Pause
        Out:
            Menu
        """
        self.log.success("GameInstance: Normal level")
        # Returns to menu
        return self._start_normal_levels()

    def page_player_name_for_score(self) -> None:
        """Player score + ask name. (and victory text if wins)

        In:
            Menu
        Access:
            None
        Out:
            Menu
        """
        from assets.code.ui.end_screen import EndScreen

        self.log.success("GameInstance: Enter player name for score saving:")
        won = self._current_player.is_alive()
        player_score = self._current_player.score_info.score
        player_name = EndScreen(won, player_score).show()
        self._scores.add_score(player_name, player_score)
        # Returns to Menu
