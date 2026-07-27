"""Level options for generation."""

from time import time
from random import randint


class LevelOptions:
    """Options for level generation.

    Attributes:
        width: TODO: log <= 0 and set to default=?
        height: TODO: log <= 0 and set to default=?
        pac_gum_count: TODO
        seed (int | None): TODO
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
            pac_gum_count: the maximum number of pacgums ion the maze.
            seed: the seed for the maze generation.
        """
        # TODO: width and height checking and modify with
        # default min, same for pac_gum_count and seed
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
                else randint(int(time() * 1000000)))

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
