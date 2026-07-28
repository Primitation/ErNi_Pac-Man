"""Scores of the game."""

from typing import List, Tuple

from Engine.LogSubsystem.logsubsystem import Log

from .game_config import GameConfig
import json


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


class Scores:
    """Scores saved."""
    def __init__(self, scores: List[Tuple[str, int]]) -> None:
        """Initialize the scores.

        Args:
            scores: lists of name and scores
        """
        self._scores = scores

    @staticmethod
    def load_scores(game_config: GameConfig) -> "Scores":
        """Load scores.

        Args:
            game_config: game config for filename.

        Returns:
            Returns scores stored.
        """
        try:
            with open(game_config.highscore_filename, "r") as f:
                scores = json.load(f)
            if isinstance(scores, list):
                scores_list: List[Tuple[str, int]] = [
                    (player, int(score))
                    for player, score in scores
                ]
                return Scores(scores_list)
            else:
                raise ValueError("Scores: not a list.")
        except Exception:
            Log.get("main").error("Can't read scores in file"
                                  f" {game_config.highscore_filename}")
            return Scores([])

    def save_scores(self, game_config: GameConfig) -> None:
        """Saves scores.

        Args:
            game_config: game config for filename.

        Returns:
            Saves the scores in the filename.
        """
        try:
            with open(game_config.highscore_filename, "w") as f:
                json.dump(self._scores, f)
        except Exception:
            Log.get("main").error("Can't saves scores in file"
                                  f" {game_config.highscore_filename}")

    def add_score(self, name: str, score: int) -> None:
        """Adds a player name and score.

        Args:
            name: the player name.
            score: the player score.
        """
        self._scores.append((name, score))

    def get_top_scores(self, max_count: int | None = None
                       ) -> List[Tuple[str, int]]:
        """Returns the top scores.

        Args:
            max_count: the maximum number to returns. None is all scores.

        Returns:
            Returns the maximum number to returns. None is all scores.
        """
        self._scores.sort(key=lambda player_score: player_score[1],
                          reverse=True)
        limit = min(len(self._scores),
                    len(self._scores)
                    if max_count is None else max_count)
        return list(self._scores[:limit])
