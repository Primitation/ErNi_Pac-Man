from .collider import CollisionManager, Collider
from .. import log_timing, Log


class CollisionSubsystem:
    """Global collision system."""

    def __init__(self, cell_size: int = 128,
                 max_correction_per_frame: float = 64.0):
        self._manager = CollisionManager(cell_size, max_correction_per_frame)
        self._logger = Log.get("collision")

    def init(self, width: int, height: int) -> None:
        self._manager.init(width, height)

    def register(
        self,
        owner,
        get_rect,
        tag: str = "default",
        collides_with=None,
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

    def draw_debug(self, renderer, color_map=None) -> None:
        """Draw all registered colliders for debug visualization."""
        self._manager.draw_debug(renderer, color_map)


Collision = CollisionSubsystem()
