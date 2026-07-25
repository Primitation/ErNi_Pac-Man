"""Configuration for the game."""


from typing import List
from game.levelgen import LevelOptions


class GameConfig:
    """Config from the json."""  # TODO
    def __init__(self) -> None:  # TODO store from config
        """Initilize the game configuration.

        TODO
        """
        self._points_per_pacgum = 5
        self._points_per_super_pacgum = 10
        self._points_per_ghost = 200
        self._seed = 42
        self._level_options = [  # TODO: notes: first seed, others None=random
            LevelOptions(200, 100, 4, self._seed),
            LevelOptions(250, 50, 8),
            LevelOptions(100, 150, 6),
            LevelOptions(100, 100, 11),
            LevelOptions(50, 50, 11)
        ]

    @property
    def points_per_pacgum(self) -> int:
        """Points per pacgum eaten."""
        return self._points_per_pacgum

    @property
    def points_per_super_pacgum(self) -> int:
        """Points per super pacgum eaten."""
        return self._points_per_super_pacgum

    @property
    def points_per_ghost(self) -> int:
        """Points per ghost eaten."""
        return self._points_per_ghost

    @property
    def seed(self) -> int:
        """The seed for the first maze."""
        return self._seed

    @property
    def level_options(self) -> List[LevelOptions]:
        """Options for each level from the config."""
        return self._level_options
