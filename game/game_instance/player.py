"""Current player."""

from game.game_instance.game_config import GameConfig
from game.game_instance.score import Score


class PlayerInformation:
    def __init__(self,
                 config: GameConfig,
                 lives: int=3,
                 score: Score=None) -> None:
        """Initialize a player with a score and lives."""
        self._lives = lives
        if self._lives < 1:
            # TODO: Log default lives
            self._lives = 3
        self._score = score if score is not None else Score(config)

    @property
    def score_info(self) -> Score:
        """The score information."""
        return self._score

    @property
    def lives(self) -> int:
        """The number of lives.

        Returns:
            Returns the number of lives >= 0.
        """
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
    