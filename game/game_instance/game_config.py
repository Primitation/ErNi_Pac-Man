"""Configuration for the game."""


from typing import List

from game.levelgen.level_options import LevelOptions


class GameConfig:
    """Config from the json."""  # TODO
    def __init__(self) -> None: # TODO store from config
        self._points_per_pacgum = 5
        self._points_per_super_pacgum = 10
        self._points_per_ghost = 200
        self._seed = 42
        self._level_options = [ # TODO: notes: first seed, others none (random)
            LevelOptions(200, 100, 4, self._seed),
            LevelOptions(250, 50, 8),
            LevelOptions(100, 150, 6),
            LevelOptions(170, 100, 12),
            LevelOptions(200, 170, 3),
            LevelOptions(100, 100, 11),
            LevelOptions(50, 50, 11)
        ]

    @property
    def points_per_pacgum(self) -> int:
        """TODO"""
        return self._points_per_pacgum

    @property
    def points_per_super_pacgum(self) -> int:
        """TODO"""
        return self._points_per_super_pacgum

    @property
    def points_per_ghost(self) -> int:
        """TODO"""
        return self._points_per_ghost

    @property
    def seed(self) -> int:
        """TODO"""
        return self._seed

    @property
    def level_options(self) -> List[LevelOptions]:
        """TODO"""
        return self._level_options