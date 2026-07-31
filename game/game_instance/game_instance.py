"""Game instance."""

from typing import List, Tuple

from Engine.LogSubsystem.logsubsystem import Log
from game.game_instance.score import Scores
from .player_information import PlayerInformation
from .game_config import GameConfig
from .game_mode import GameModeNormalLevels


class AskUI:
    @staticmethod
    def menu() -> str:  # temporary return type
        msg = "Menu = start/s, highscores/h, instructions/i, exit/e:\n"
        log = Log.get("main")
        log.warning(msg)
        inv = input()
        while inv not in ("start", "highscores", "instructions",
                          "exit", "s", "h", "i", "e"):
            log.warning(msg)
            inv = input()
        d = {"i": "instructions", "s": "start", "h": "highscores", "e": "exit"}
        if inv in d:
            inv = d[inv]
        return inv

    @staticmethod
    def ask_name(message: str, score: int) -> str:
        # TODO: check <= 10 characters, letters/digit only
        print(message)
        return input(f"Player name for the score: {score}\n")

    @staticmethod
    def view_scores(names_scores: List[Tuple[str, int]]) -> None:
        print("\n".join([
            f"{str(i + 1)}. {name_score[0]} - {name_score[1]} pts"
            for i, name_score in enumerate(names_scores)
        ]))
        input("Enter for exit highscores page:\n")

    @staticmethod
    def view_instructions(message: str) -> None:
        print(message)
        input("Enter for exit instructions page:\n")


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

        # TODO load here ? or not ?
        self._game_mode_normal.reset()
        level_instance = self._game_mode_normal.next_level()
        while level_instance is not None:
            level_instance.load()
            level_instance = self._game_mode_normal.next_level()
        self._game_mode_normal.reset()
        self.log = Log.get("main")

    def _start_normal_levels(self) -> None:
        """Initialize the game and start."""
        self._current_player.reset()
        self._game_mode_normal.reset()
        log = Log.get("main")
        log.info("GameInstance: start normal levels")
        level_instance = self._game_mode_normal.next_level()
        while self._current_player.is_alive() and level_instance is not None:
            level_name = self._game_mode_normal.current_level
            log.info(f"GameInstance: start normal level {level_name}")
            level_instance.start(self._current_player, level_name)
            level_instance = self._game_mode_normal.next_level()
        log.info("GameInstance: end normal levels")

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
        exit_menu = False
        while not exit_menu:
            self.log.success("GameInstance: Menu")
            next_page = AskUI.menu()
            if next_page == "start":
                self.page_current_normal_levels()
                self.page_player_name_for_score()
            elif next_page == "instructions":
                self.page_instructions()
            elif next_page == "highscores":
                self.page_scores()
            elif next_page == "exit":
                self._scores.save_scores(self._config)
                exit_menu = True

    def page_instructions(self) -> None:
        """Instruction page.

        In:
            Menu
        Access:
            None
        Out:
            Menu
        """
        self.log.success("GameInstance: Instructions")
        instructions = "Instructions here"  # TODO: instruction text
        AskUI.view_instructions(instructions)
        # Returns to menu

    def page_current_normal_levels(self) -> None:
        """Normal current level page.

        In:
            Menu
        Access:
            Pause  #TODO
        Out:
            Menu
        """
        self.log.success("GameInstance: Normal level")
        self._start_normal_levels()
        # Returns to menu

    def page_pause(self) -> None:
        """Pause page.

        In:
            ingame # TODO
        Access:
            None
        Out:
            in-game (current_normal_levels)
        """
        pass

    def page_player_name_for_score(self) -> None:
        """Player score + ask name. (and victory text if wins)

        In:
            Menu
        Access:
            None
        Out:
            Menu
        """
        self.log.success("GameInstance: Enter player name for score saving:")
        message_for_player = ("Winner\n"
                              if self._current_player.is_alive()
                              else "Well played\n")
        player_score = self._current_player.score_info.score
        player_name = AskUI.ask_name(message_for_player, player_score)
        self._scores.add_score(player_name, player_score)
        # Returns to Menu

    def page_scores(self) -> None:
        """Page for the scores.

        In:
            Menu
        Access:
            None
        Out:
            Menu
        """
        self.log.success("GameInstance: HighScores")
        AskUI.view_scores(self._scores.get_top_scores(10))
        # Returns to Menu
