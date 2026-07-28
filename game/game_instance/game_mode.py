"""Type of game level."""

from abc import ABC, abstractmethod
from typing import List

from game.level_instance import LevelInstance
from game.levelgen import LevelOptions


class GameModeLevels(ABC):
    """Generator of levels."""

    @abstractmethod
    def current_level(self) -> int:
        """The current level.

        Returns:
            Returns the current level.
        """
        pass

    @abstractmethod
    def next_level(self) -> LevelInstance | None:
        """Returns a level untils no more level.

        Returns:
            Returns a level instance untils no more level.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the current level."""
        pass


class GameModeNormalLevels(GameModeLevels):
    """Generator of 10 levels."""
    def __init__(self, levels_options: List[LevelOptions]) -> None:
        """Initialize a level generator of 10.

        Args:
            levels_options: options for each level.
        """
        self._curr_level = 0
        self._pregenerated_levels = [
            LevelInstance(level_option)
            for level_option in levels_options
        ]

    @property
    def current_level(self) -> int:
        """The current level."""
        return self._curr_level

    def next_level(self) -> LevelInstance | None:
        """Returns a level untils no more level.

        Returns:
            Returns a level instance untils no more level.
        """
        if self._curr_level >= len(self._pregenerated_levels):
            return None

        curr_level_instance = self._pregenerated_levels[self._curr_level]
        self._curr_level += 1
        return curr_level_instance

    def reset(self) -> None:
        """Reset the current level."""
        self._curr_level = 0
