"""Scores of the game."""

from .game_config import GameConfig


class Score:
    """The score of the current player"""
    def __init__(self, config: GameConfig) -> None:
        """Initialize the score and value per action.

        Args:
            config: the game config for the points.
        """
        self._score = 0
        self._points_per_pacgum = config.points_per_pacgum
        self._points_per_super_pacgum = config.points_per_super_pacgum
        self._points_per_ghost = config.points_per_ghost

    @property
    def score(self) -> int:
        """The score."""
        return self._score

    def eat_pacgum(self) -> None:
        """Add points for eating a pacgum."""
        self._score += self._points_per_pacgum

    def eat_super_pacgum(self) -> None:
        """Add points for eating a super pacgum."""
        self._score += self._points_per_super_pacgum

    def eat_ghost(self) -> None:
        """Add points for eating a ghost."""
        self._score += self._points_per_ghost

    def reset(self) -> None:
        """Reset the points to 0."""
        self._score = 0
