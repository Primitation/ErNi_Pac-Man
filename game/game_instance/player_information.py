"""Current player."""

from .game_config import GameConfig
from .score import Score


class PlayerInformation:
    """Player information in the game."""
    def __init__(self,
                 config: GameConfig,
                 score: Score = None) -> None:
        """Initialize a player with a score and lives.

        Args:
            config: the game config.
            lives: the number of lives (> 0) for the player.
            score: the player score.
        """
        self._lives = config.lives
        self._base_lives = self._lives
        self._score = score if score is not None else Score(config)

    @property
    def score_info(self) -> Score:
        """The score information."""
        return self._score

    @property
    def lives(self) -> int:
        """The number of lives."""
        return self._lives

    def is_alive(self) -> bool:
        """Returns true if the player have live, False otherwise.

        Returns:
            Returns true if the player have live, False otherwise.
        """
        return self._lives > 0

    def loss_live(self) -> None:
        """The player lose a live if possible."""
        if self._lives > 0:
            self._lives -= 1

    def add_live(self) -> None:
        """The player add 1 live"""
        if self._lives > 0:
            self._lives += 1

    def reset(self) -> None:
        """Reset the player to starting values."""
        self._lives = self._base_lives
        self._score.reset()
