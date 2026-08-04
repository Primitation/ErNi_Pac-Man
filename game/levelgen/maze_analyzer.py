"""Maze analyzer"""

from typing import List, Tuple
from Engine import Vector2


class MazeAnalyzer:
    """Analyzes a maze.
    """
    @staticmethod
    def extract_open_cells(maze: List[List[int]],
                           ignore_cells: List[Vector2] = []
                           ) -> List[Vector2]:
        """Extract cells with at least a open cell.

        Args:
            maze: maze wall format as bits 0 open and 1 closed of (W S E N).
            ignore_cells: ignore the cells in the list.
        Returns:
            Returns the cells with at least a wall open.
        """
        open_cells: List[Vector2] = [
            Vector2(width_pos, height_pos)
            for height_pos in range(len(maze))
            for width_pos in range(len(maze[height_pos]))
            if ((width_pos, height_pos) not in ignore_cells
                and maze[height_pos][width_pos] != 0xF)
        ]
        return open_cells

    @staticmethod
    def extract_walls(maze: List[List[int]],
                      north: float = 0,
                      next_clockwise: float = 90
                      ) -> List[Tuple[Vector2, float]]:
        """Extract the walls in the format: list of position, rotation.

        Args:
            maze: the maze generated.
            north: the rotation for the north.
            next_clockwise:
                the next rotation clockwise.
                east = north + next_clockwise
                south = east + next_clockwise
                west = south + next_clockwise

        Returns:
            Returns the walls in the format: list of position, rotation.
        """
        walls: List[Tuple[Vector2, float]] = []
        for x_pos in range(len(maze)):
            for y_pos in range(len(maze[x_pos])):
                if maze[x_pos][y_pos] & 1:
                    walls.append((Vector2(y_pos, x_pos),
                                  north + next_clockwise * 0))
                if maze[x_pos][y_pos] & 2:
                    walls.append((Vector2(y_pos, x_pos),
                                  north + next_clockwise * 1))
                if maze[x_pos][y_pos] & 4:
                    walls.append((Vector2(y_pos, x_pos),
                                  north + next_clockwise * 2))
                if maze[x_pos][y_pos] & 8:
                    walls.append((Vector2(y_pos, x_pos),
                                  north + next_clockwise * 3))
        return walls
