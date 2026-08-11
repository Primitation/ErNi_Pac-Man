# vector2.py
import math
from typing import Iterator, Tuple


class Vector2:
    """2D vector with basic operations."""

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        """Initialize vector 2D.

        Args:
            x: x
            y: y
        """

        self.x = x
        self.y = y

    def __repr__(self) -> str:
        """String representation

        Returns:
            Returns string representation.
        """
        return f"Vector2({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        """Test equality

        Args:
            other: other

        Returns:
            Returns if equals to other.
        """
        return isinstance(other, Vector2) \
            and self.x == other.x and self.y == other.y

    def __iter__(self) -> Iterator[float]:
        """Iterator on x and y.

        Returns:
            Returns iterator on x and y.
        """
        yield self.x
        yield self.y

    def __add__(self, other: "Vector2") -> "Vector2":
        """Addition operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2") -> "Vector2":
        """Substract operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector2(self.x - other.x, self.y - other.y)

    def __neg__(self) -> "Vector2":
        """Negative operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector2(-self.x, -self.y)

    def __mul__(self, scalar: float) -> "Vector2":
        """Multiplication operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> "Vector2":
        """True division operation.

        Args:
            scalar: scalar

        Returns:
            Returns operation applied with scalar.
        """
        return Vector2(self.x / scalar, self.y / scalar)

    def dot(self, other: "Vector2") -> float:
        """Dot operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vector2") -> float:
        """2D 'cross product' — a scalar.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return self.x * other.y - self.y * other.x

    def length(self) -> float:
        """Returns length.

        Returns:
            Returns length.
        """
        return math.hypot(self.x, self.y)

    def length_squared(self) -> float:
        """Returns length squared.

        Returns:
            Returns length squared.
        """
        return self.x * self.x + self.y * self.y

    def normalize(self) -> "Vector2":
        """Returns normalize.

        Returns:
            Returns normalize.
        """
        length = self.length()
        if length == 0:
            return Vector2(0, 0)
        return Vector2(self.x / length, self.y / length)

    def to_tuple(self) -> Tuple[float, float]:
        """Returns as tuple.

        Returns:
            Returns as tuple.
        """
        return (self.x, self.y)

    @classmethod
    def zero(cls) -> "Vector2":
        """Returns zeros.

        Returns:
            Returns zeros.
        """
        return cls(0.0, 0.0)

    @classmethod
    def one(cls) -> "Vector2":
        """Returns ones.

        Returns:
            Returns ones.
        """
        return cls(1.0, 1.0)
