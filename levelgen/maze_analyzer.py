"""Maze analyzer"""

from typing import List, Tuple


class MazeAnalyzer:
    """Analyzes a maze.
    """
    @staticmethod
    def extract_open_cells(maze: List[List[int]]) -> List[Tuple[int, int]]:
        """Extract cells with at least a open cell.

        Args:
            maze: maze wall format as bits 0 open and 1 closed of (W S E N).

        Returns:
            Returns the cells with at least a wall open.
        """
        open_cells: List[Tuple[int, int]] = [
            (width_pos, height_pos)
            for height_pos in range(len(open_cells))
            for width_pos in range(len(open_cells[height_pos]))
            if maze[height_pos][width_pos] != 0xF
        ]
        return open_cells