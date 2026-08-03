class Color:
    """r, g, b, a as ints 0-255."""

    __slots__ = ("r", "g", "b", "a")

    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Color)
            and self.r == other.r
            and self.g == other.g
            and self.b == other.b
            and self.a == other.a
        )

    def to_argb(self) -> int:
        """Packs to the 0xAARRGGBB int mlx_pixel_put() expects."""
        return (self.a << 24) | (self.r << 16) | (self.g << 8) | self.b

    def to_bytes(self) -> bytes:
        """4 little-endian bytes."""
        return self.to_argb().to_bytes(4, "little")

    @classmethod
    def from_argb(cls, value: int) -> "Color":
        return cls(
            r=(value >> 16) & 0xFF,
            g=(value >> 8) & 0xFF,
            b=value & 0xFF,
            a=(value >> 24) & 0xFF,
        )

    def to_floats(self) -> tuple[float, float, float, float]:
        return (self.r / 255, self.g / 255, self.b / 255, self.a / 255)

    @classmethod
    def white(cls) -> "Color":
        return cls(255, 255, 255, 255)

    @classmethod
    def black(cls) -> "Color":
        return cls(0, 0, 0, 255)

    @classmethod
    def transparent(cls) -> "Color":
        return cls(0, 0, 0, 0)

    @classmethod
    def magenta(cls) -> "Color":
        return cls(255, 0, 255, 255)
