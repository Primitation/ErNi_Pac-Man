# euler.py
import math
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .quaternion import Quaternion


class Euler:
    """Rotation as three axis angles, in radians."""

    __slots__ = ("pitch", "yaw", "roll")

    def __init__(self, pitch: float = 0.0, yaw: float = 0.0,
                 roll: float = 0.0) -> None:
        """Initialize euler calculus.

        Args:
            roll: rotation x axis.
            pitch: rotation y axis.
            yaw: rotation z axis.
        """
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll

    def __repr__(self) -> str:
        """String representation.

        Returns:
            Returns string representation.
        """
        return f"Euler({self.pitch}, {self.yaw}, {self.roll})"

    def __eq__(self, other: object) -> bool:
        """Test equality.

        Args:
            other: other object.

        Returns:
            Returns if self is equal to other.
        """
        return (
            isinstance(other, Euler)
            and self.pitch == other.pitch
            and self.yaw == other.yaw
            and self.roll == other.roll
        )

    @classmethod
    def from_degrees(cls, pitch: float, yaw: float, roll: float) -> "Euler":
        """Initialize a Euler from values.

        Args:
            roll: rotation x axis.
            pitch: rotation y axis.
            yaw: rotation z axis.

        Returns:
            Returns the Euler.
        """
        return cls(math.radians(pitch), math.radians(yaw), math.radians(roll))

    def to_degrees(self) -> Tuple[float, float, float]:
        """Euler to degrees.

        Returns:
            Returns Euler as degrees.
        """
        return (
            math.degrees(self.pitch),
            math.degrees(self.yaw),
            math.degrees(self.roll),
        )

    def to_quaternion(self) -> "Quaternion":
        """Builds a Quaternion using pitch(X) -> yaw(Y) -> roll(Z).

        Returns:
            Returns a Quaternion using pitch(X) -> yaw(Y) -> roll(Z).
        """
        from .quaternion import Quaternion

        cp = math.cos(self.pitch * 0.5)
        sp = math.sin(self.pitch * 0.5)
        cy = math.cos(self.yaw * 0.5)
        sy = math.sin(self.yaw * 0.5)
        cr = math.cos(self.roll * 0.5)
        sr = math.sin(self.roll * 0.5)

        return Quaternion(
            w=cr * cp * cy + sr * sp * sy,
            x=cr * sp * cy - sr * cp * sy,
            y=cr * cp * sy + sr * sp * cy,
            z=sr * cp * cy - cr * sp * sy,
        )

    @classmethod
    def zero(cls) -> "Euler":
        """Euler at 0, 0, 0.

        Returns:
            Returns Eular at 0, 0, 0.
        """
        return cls(0.0, 0.0, 0.0)
