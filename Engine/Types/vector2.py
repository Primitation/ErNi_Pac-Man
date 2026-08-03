import math


class Vector2:
    """2D vector with basic operations."""

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Vector2({self.x}, {self.y})"

    def __eq__(self, other) -> bool:
        return isinstance(other, Vector2) and self.x == other.x \
            and self.y == other.y

    def __iter__(self):
        yield self.x
        yield self.y

    def __add__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x - other.x, self.y - other.y)

    def __neg__(self) -> "Vector2":
        return Vector2(-self.x, -self.y)

    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> "Vector2":
        return Vector2(self.x / scalar, self.y / scalar)

    def dot(self, other: "Vector2") -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vector2") -> float:
        """2D 'cross product' — a scalar."""
        return self.x * other.y - self.y * other.x

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalize(self) -> "Vector2":
        length = self.length()
        if length == 0:
            return Vector2(0, 0)
        return Vector2(self.x / length, self.y / length)

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    @classmethod
    def zero(cls) -> "Vector2":
        return cls(0.0, 0.0)

    @classmethod
    def one(cls) -> "Vector2":
        return cls(1.0, 1.0)
