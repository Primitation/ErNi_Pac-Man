"""Maze analyzer"""

from typing import List, Tuple
from Engine import Vector2

class MazeAnalyzer:
    """Analyzes a maze.
    """
    @staticmethod
    def extract_open_cells(maze: List[List[int]],
                           ignore_cells: List[Vector2]=set()
                           ) -> List[Vector2]:
        """Extract cells with at least a open cell.

        Args:
            maze: maze wall format as bits 0 open and 1 closed of (W S E N).

        Returns:
            Returns the cells with at least a wall open.
        """
        open_cells: List[Vector2] = [
            Vector2(width_pos, height_pos)
            for height_pos in range(len(open_cells))
            for width_pos in range(len(open_cells[height_pos]))
            if ((width_pos, height_pos) not in ignore_cells
                and maze[height_pos][width_pos] != 0xF)
        ]
        return open_cells