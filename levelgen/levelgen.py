"""Level Generator."""

import random
from levelgen import LevelStructure
from levelgen import LevelOptions
from mazegen import MazeGenerator


class LevelGenerator:
    """Generate a level with the options.

    Attributes:
        seed:
            the generator generate the same level with the same options
            in the same order.

    Do not use random.random() in another thread while generating.
    Do not use multiples LevelGenerator.generate() at the same time.
    """
    def __init__(self, seed=0) -> None:
        """Initialize a level generator.

        Args:
            seed: the generator seed.
        """
        self._random = random.Random(seed)
        self._max_rand_range = 1 << 32

    def generate(self, level_options: LevelOptions) -> LevelStructure:
        """Generates a level from options.

        Args:
            level_options: level options

        Returns:
            Returns a level with maze, pacman, ghost, points.

        Raises:
            Error: MazeGenerator
            Error: Invalid width or height in options

        Do not use multiples LevelGenerator.generate() at the same time.
        """
        if level_options.width <= 0: # TODO min size
            raise ValueError(f"Invalid width <= 0: {level_options.width}")
        if level_options.height <= 0: # TODO min size
            raise ValueError(f"Invalid width <= 0: {level_options.height}")
        maze_generator_seed = self._random.randrange(stop=self._max_rand_range)
        try:
              start = (0, 0) # TODO pick good start
              end = (0, 1) # TODO pick good end close to start (faster useless path)
              maze = MazeGenerator(size=(level_options.width,
                                         level_options.height),
                                   perfect=False,
                                   entry_cell=start,
                                   exit_cell=end,
                                   seed=maze_generator_seed)
        except Exception as exception:
              # TODO what to do if mazegenerator fail ?
              raise ValueError(f"LevelGenerator: error from maze generator:"
                               f" {exception}")
        # TODO: add pacman, ghosts, gums, special gums
        return None # TODO