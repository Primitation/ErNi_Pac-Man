from enum import Enum, auto


class GameState(Enum):
    """Game state enumeration."""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    LEVEL_COMPLETE = auto()


class CollisionLayer(Enum):
    """Collision layers."""
    DEFAULT = 0
    PLAYER = 1
    WALL = 2
    ENEMY = 3
    TRIGGER = 4
    FLOOR = 5


class AssetType(Enum):
    """Asset types."""
    TEXTURE = auto()
    SPRITE_SHEET = auto()
    SOUND = auto()
    FONT = auto()
