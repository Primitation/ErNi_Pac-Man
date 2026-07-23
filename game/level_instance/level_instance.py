"""Level instance"""

from levelgen.level_gen import LevelGenerator
from levelgen.level_options import LevelOptions


class LevelInstance:
    """Level instance.

    TODO
    """
    def __init__(self, level_options: LevelOptions) -> None:
        """Initializes a level instance.
        
        Args:
            level_options: options for the current level
        """
        self._level_options = level_options

    def load(self) -> None:
        self._level_structure = LevelGenerator.generate(self._level_options)
        # TODO: set the world

    def start(self, ) -> "TODO":
        """Start the level.
        """
        # TODO: set the players and ghosts, etc in the world
        pass # TODO start the game