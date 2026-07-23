"""Scores of the game."""

from game.game_instance.game_config import GameConfig


class Score:
    """The score of the current player"""
    def __init__(self, config: GameConfig) -> None:
        """Initialize the score and value per action.
        """
        self._score = 0
        self._points_per_pacgum = config.points_per_pacgum
        self._points_per_super_pacgum = config.points_per_super_pacgum
        self._points_per_ghost = config.points_per_ghost

    @property
    def score(self) -> int:
        return self._score

    def eat_pacgum(self) -> None:
        self._score += self._points_per_pacgum

    def eat_super_pacgum(self) -> None:
        self._score += self._points_per_super_pacgum

    def eat_ghost(self) -> None:
        self._score += self._points_per_ghost