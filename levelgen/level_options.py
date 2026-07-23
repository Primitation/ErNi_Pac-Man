"""Level options for generation."""

from time import time

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
                 seed: int | None) -> None:
        # TODO: width and height checking and modify with default min, same for pac_gum_count and seed
        self._width = width
        self._height = height
        self._pac_gum_count = pac_gum_count
        self._seed = seed if seed is not None else int(time() * 1000000)

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

    @property
    def seed(self) -> int:
        """The random seed."""
        return self._seed