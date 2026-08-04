# collisionsubsystem.py
from typing import Any, Optional, List, Dict, Callable
from .collider import CollisionManager, Collider, Rect
from .. import log_timing, Log


class CollisionSubsystem:
    """Global collision system."""

    def __init__(self, cell_size: int = 128,
                 max_correction_per_frame: float = 64.0) -> None:
        """Initialize collision subsystem.

        Args:
            cell_size: the cell size.
            max_correction_per_frame: max correction per frame
        """
        self._manager = CollisionManager(cell_size, max_correction_per_frame)
        self._logger = Log.get("collision")

    def init(self, width: int, height: int) -> None:
        """Init with width and height.

        Args:
            width: the width.
            height: the height.
        """
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
        """Register a collider.

        Args:
            owner: the owner.
            get_rect: callable to get the rect.
            tag: tag.
            collides_with: collide with type.
            blocking: block the path.
            bounce: bounce distance.
            static: static collider.
            enabled: enable the component.
        """
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
        """Unregister a collider.

        Args:
            collider: the collider to unregister.
        """
        self._manager.unregister(collider)

    @log_timing()
    def update(self) -> None:
        """Update the collider."""
        self._manager.update()

    def draw_debug(self, renderer: Any,
                   color_map: Optional[Dict[str, int]] = None) -> None:
        """Draw all registered colliders for debug visualization.

        Args:
            renderer: the renderer.
            color_map: the color for collision owner.
        """
        self._manager.draw_debug(renderer, color_map)


Collision = CollisionSubsystem()
