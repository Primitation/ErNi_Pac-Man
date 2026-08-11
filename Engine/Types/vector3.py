# vector3.py
import math
from typing import Iterator, Tuple


class Vector3:
    """3D vector with basic operations."""

    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        """Initialize vector 3D.

        Args:
            x: x
            y: y
            z: z
        """
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self) -> str:
        """String representation

        Returns:
            Returns string representation.
        """
        return f"Vector3({self.x}, {self.y}, {self.z})"

    def __eq__(self, other: object) -> bool:
        """Test equality

        Args:
            other: other

        Returns:
            Returns if equals to other.
        """
        return (
            isinstance(other, Vector3)
            and self.x == other.x
            and self.y == other.y
            and self.z == other.z
        )

    def __iter__(self) -> Iterator[float]:
        """Iterator on x, y and z.

        Returns:
            Returns iterator on x, y and z.
        """
        yield self.x
        yield self.y
        yield self.z

    def __add__(self, other: "Vector3") -> "Vector3":
        """Addition operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        """Substract operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self) -> "Vector3":
        """Negative operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector3(-self.x, -self.y, -self.z)

    def __mul__(self, scalar: float) -> "Vector3":
        """Multiplication operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> "Vector3":
        """True division operation.

        Args:
            scalar: scalar

        Returns:
            Returns operation applied with scalar.
        """
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other: "Vector3") -> float:
        """Dot operation.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vector3") -> "Vector3":
        """3D 'cross product' — a scalar.

        Args:
            other: other

        Returns:
            Returns operation applied to other.
        """
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length(self) -> float:
        """Returns length.

        Returns:
            Returns length.
        """
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def length_squared(self) -> float:
        """Returns length squared.

        Returns:
            Returns length squared.
        """
        return self.x * self.x + self.y * self.y + self.z * self.z

    def normalize(self) -> "Vector3":
        """Returns normalize.

        Returns:
            Returns normalize.
        """
        length = self.length()
        if length == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / length, self.y / length, self.z / length)

    def to_tuple(self) -> Tuple[float, float, float]:
        """Returns as tuple.

        Returns:
            Returns as tuple.
        """
        return (self.x, self.y, self.z)

    @classmethod
    def zero(cls) -> "Vector3":
        """Returns zeros.

        Returns:
            Returns zeros.
        """
        return cls(0.0, 0.0, 0.0)

    @classmethod
    def one(cls) -> "Vector3":
        """Returns ones.

        Returns:
            Returns ones.
        """
        return cls(1.0, 1.0, 1.0)
