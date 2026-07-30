"""Level Generator."""

import random
from typing import List
from .level_structure import LevelStructure
from .level_options import LevelOptions
from .maze_analyzer import MazeAnalyzer
from Engine import Vector2
from mazegenerator import MazeGenerator


class LevelGenerator:
    """Generate a level with the options.

    Do not use random.random() in another thread while generating.
    Do not use multiples LevelGenerator.generate() at the same time.
    """
    @staticmethod
    def generate(level_options: LevelOptions) -> LevelStructure:
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
        if level_options.width <= 0:
            raise ValueError(f"Invalid width <= 0: {level_options.width}")
        if level_options.height <= 0:
            raise ValueError(f"Invalid width <= 0: {level_options.height}")

        try:
            start = (0, 0)  # TODO pick good start
            end = (0, 1)  # TODO pick good close s, e (faster useless path)
            maze_generated = MazeGenerator(
                size=(level_options.width, level_options.height),
                perfect=False,
                entry_cell=start,
                exit_cell=end,
                seed=level_options.seed)
            maze = maze_generated.maze
        except Exception as exception:
            # TODO what to do if mazegenerator fail ?
            raise ValueError(f"LevelGenerator: error from maze generator:"
                             f" {exception}")

        random.seed(level_options.seed)

        # TODO: good position: right now 20x20 or 10x10 is inside the 42
        pacman = Vector2((level_options.width // 2)-1, level_options.height // 2)

        corners = [(0, 0),
                   (0, level_options.height - 1),
                   (level_options.width - 1, 0),
                   (level_options.width - 1, level_options.height - 1)]

        ghosts = [Vector2(width, height) for width, height in corners]

        super_pacgums = [Vector2(width, height) for width, height in corners]

        open_cells: List[Vector2] = MazeAnalyzer.extract_open_cells(
             maze=maze,
             ignore_cells=[pacman] + super_pacgums)
        random.shuffle(open_cells)
        pacgums = open_cells[:min(len(open_cells),
                                  level_options.pac_gum_count)]

        return LevelStructure(width=level_options.width,
                              height=level_options.height,
                              maze=maze, pacman=pacman, ghosts=ghosts,
                              super_pacgums=super_pacgums, pacgums=pacgums)
