"""Type of game level."""

from abc import ABC, abstractmethod
from typing import List

from game.level_instance.level_instance import LevelInstance
from levelgen.level_options import LevelOptions


class GameModeLevels(ABC):
    """Generator of levels."""
    @abstractmethod
    def next_level(self) -> LevelInstance:
        pass


class GameModeNormalLevels(GameModeLevels):
    """Generator of 10 levels."""
    def __init__(self, level_options: List[LevelOptions]) -> None:
        """Initialize a level generator of 10."""
        self._curr_level = 0
        self._pregenerated_levels = [
            LevelInstance(level_option)
            for level_option in level_options
        ]
        # TODO: load now ? or thread ? or etc
        # TODO: at least 10 levels ! (defaults ?)

    @property
    def current_level(self) -> str:  # TODO or int
        """The current level."""
        return str(self._curr_level)

    def next_level(self) -> LevelInstance | None:
        """Returns a level untils no more level.

        Returns:
            Returns a level instance untils no more level.
        """
        if self._curr_level + 1 >= len(self._pregenerated_levels):
            return None

        self._curr_level += 1
        return self._pregenerated_levels[self._curr_level]
