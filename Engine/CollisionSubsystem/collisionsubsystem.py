# collisionsubsystem.py
from typing import Any, Optional, List, Dict, Callable
from .collider import CollisionManager, Collider, Rect
from .. import log_timing, Log


class CollisionSubsystem:
    """Global collision system."""

    def __init__(self, cell_size: int = 128,
                 max_correction_per_frame: float = 64.0) -> None:
        self._manager = CollisionManager(cell_size, max_correction_per_frame)
        self._logger = Log.get("collision")

    def init(self, width: int, height: int) -> None:
        self._manager.init(width, height)

    def register(
        self,
        owner: Any,
        get_rect: Callable[[], Rect],
        tag: str = "default",
        collides_with: Optional[List[str]] = None,
        blocking: bool = False,
        bounce: float = 0.0,
        static: bool = False,
        enabled: bool = True
    ) -> Collider:
        """Register a collider."""
        return self._manager.register(
            owner,
            get_rect,
            tag,
            collides_with,
            blocking,
            bounce,
            static,
            enabled
        )

    def unregister(self, collider: Collider) -> None:
        """Unregister a collider."""
        self._manager.unregister(collider)

    @log_timing()
    def update(self) -> None:
        """Call once per frame."""
        self._manager.update()

    def draw_debug(self, renderer: Any,
                   color_map: Optional[Dict[str, int]] = None) -> None:
        """Draw all registered colliders for debug visualization."""
        self._manager.draw_debug(renderer, color_map)


Collision = CollisionSubsystem()
