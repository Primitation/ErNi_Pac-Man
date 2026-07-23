"""Level LevelStructure."""

from typing import List, Tuple
from Engine import Vector2


class LevelStructure:
    """Structure of a level.
    
    Attributes:
        width (int): the width of the maze.
        height (int): the height of the maze.
        pacman (Tuple[int, int]): pacman position.
        ghosts: (List[Tuple[int, int]]): ghosts position.
        pacgums: (List[Tuple[int, int]]): pacgums position.
        super_pacgums: (List[Tuple[int, int]]): super_pacgums position.
        maze (List[List[int]]):
            maze wall format as bits 0 open and 1 closed of (W S E N).
    """
    def __init__(self,
                 width: int,
                 height: int,
                 pacman: Vector2,
                 ghosts: List[Vector2],
                 pacgums: List[Vector2],
                 super_pacgums: List[Vector2],
                 maze: List[List[int]]) -> None:
        """Initialize a level information.

        Args:
            width (int): the width of the maze.
            height (int): the height of the maze.
            pacman (Tuple[int, int]): pacman position.
            ghosts: (List[Tuple[int, int]]): ghosts position.
            pacgums: (List[Tuple[int, int]]): pacgums position.
            super_pacgums: (List[Tuple[int, int]]): super_pacgums position.
            maze (List[List[int]]):
                maze wall format as bits 0 open and 1 closed of (W S E N).
        """
        self._width = width
        self._height = height
        self._pacman = pacman
        self._ghosts = ghosts
        self._pacgums = pacgums
        self._super_pacgums = super_pacgums
        self._maze = maze

    @property
    def width(self) -> int:
        """The width of the maze."""
        return self._width

    @property
    def height(self) -> int:
        """The height of the maze."""
        return self._height

    @property
    def pacman(self) -> Vector2:
        """The position of the pacman (width, height)."""
        return self._pacman

    @property
    def ghosts(self) -> List[Vector2]:
        """The positions of the ghosts (width, height)."""
        return self._ghosts

    @property
    def pacgums(self) -> List[Vector2]:
        """The positions of the pacgums (width, height)."""
        return self._pacgums

    @property
    def super_pacgums(self) -> List[Vector2]:
        """The positions of the super pacgums (width, height)."""
        return self._super_pacgums

    @property
    def maze(self) -> List[List[int]]:
        """The base maze."""
        return self._maze
