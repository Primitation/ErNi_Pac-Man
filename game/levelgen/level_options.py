"""Level options for generation."""

from time import time
from random import randrange


class LevelOptions:
    """Options for level generation.

    Attributes:
        width: the width of the level
        height: the height of the level
        pac_gum_count: the maximum number of pacgums in the maze
        seed (int | None): the maze generator seed (None mean random)
    """
    def __init__(self,
                 width: int,
                 height: int,
                 pac_gum_count: int,
                 seed: int | None = None) -> None:
        """Initilize a level options.

        Args:
            width: the width of the maze.
            height: the height of the maze.
            pac_gum_count: the maximum number of pacgums in the maze.
            seed: the seed for the maze generation.
        """
        self._width = width
        self._height = height
        self._pac_gum_count = pac_gum_count
        self._seed = seed

    @property
    def width(self) -> int:
        """The width of the maze."""
        return self._width

    @property
    def height(self) -> int:
        """The height of the maze."""
        return self._height

    @property
    def pac_gum_count(self) -> int:
        """The number of pacgums to put in the maze."""
        return self._pac_gum_count

    @pac_gum_count.setter
    def pac_gum_count(self, pac_gum: int) -> None:
        """Set the number of pacgums to put in the maze."""
        self._pac_gum_count = pac_gum

    @property
    def seed(self) -> int:
        """The random seed."""
        return (self._seed
                if self._seed is not None
                else randrange(int(time() * 1000000)))

    @seed.setter
    def seed(self, seed: int | None) -> None:
        """Set the random seed."""
        self._seed = seed

    def __str__(self) -> str:
        """Returns a string representation.

        Returns:
            Returns a string representation.
        """
        return (f"LevelOptions width={self._width} height={self._height} "
                f"pac_gum_count={self._pac_gum_count} seed={self._seed}")
