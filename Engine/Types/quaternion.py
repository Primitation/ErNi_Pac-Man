import math

from .vector3 import Vector3


class Quaternion:
    """w + xi + yj + zk."""

    __slots__ = ("w", "x", "y", "z")

    def __init__(self, w: float = 1.0, x: float = 0.0, y: float = 0.0,
                 z: float = 0.0):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self) -> str:
        return f"Quaternion({self.w}, {self.x}, {self.y}, {self.z})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Quaternion)
            and self.w == other.w
            and self.x == other.x
            and self.y == other.y
            and self.z == other.z
        )

    def __mul__(self, other):
        """Quaternion * Quaternion = combined rotation."""
        if isinstance(other, Quaternion):
            return Quaternion(
                w=self.w * other.w - self.x * other.x
                - self.y * other.y - self.z * other.z,
                x=self.w * other.x + self.x * other.w
                + self.y * other.z - self.z * other.y,
                y=self.w * other.y - self.x * other.z
                + self.y * other.w + self.z * other.x,
                z=self.w * other.z + self.x * other.y
                - self.y * other.x + self.z * other.w,
            )

        if isinstance(other, Vector3):
            return self._rotate_vector(other)

        return NotImplemented

    def _rotate_vector(self, v: Vector3) -> Vector3:
        qv = Quaternion(0.0, v.x, v.y, v.z)
        result = self * qv * self.conjugate()
        return Vector3(result.x, result.y, result.z)

    def conjugate(self) -> "Quaternion":
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def length(self) -> float:
        return math.sqrt(
            self.w * self.w + self.x * self.x
            + self.y * self.y + self.z * self.z
        )

    def normalize(self) -> "Quaternion":
        length = self.length()
        if length == 0:
            return Quaternion()
        return Quaternion(
            self.w / length, self.x / length,
            self.y / length, self.z / length,
        )

    def to_euler(self):
        """Returns an Euler in radians."""
        from .euler import Euler

        sinr_cosp = 2 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1 - 2 * (self.x * self.x + self.y * self.y)
        pitch = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            yaw = math.copysign(math.pi / 2, sinp)
        else:
            yaw = math.asin(sinp)

        siny_cosp = 2 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1 - 2 * (self.y * self.y + self.z * self.z)
        roll = math.atan2(siny_cosp, cosy_cosp)

        return Euler(pitch, yaw, roll)

    @classmethod
    def from_axis_angle(cls, axis: Vector3, angle: float) -> "Quaternion":
        half = angle * 0.5
        s = math.sin(half)
        return cls(
            w=math.cos(half),
            x=axis.x * s,
            y=axis.y * s,
            z=axis.z * s,
        )

    @classmethod
    def identity(cls) -> "Quaternion":
        return cls(1.0, 0.0, 0.0, 0.0)
