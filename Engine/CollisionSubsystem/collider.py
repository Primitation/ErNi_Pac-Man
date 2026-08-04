# collider.py
from typing import Optional, List, Dict, Callable, Any, Tuple, Set
from .. import Log
from .. import Vector2

Rect = Tuple[float, float, float, float]


def rect_collide_rect(rect1: Rect, rect2: Rect) -> bool:
    """Check if two rects overlap.

    Args:
        rect1: first rect
        rect2: second rect

    Returns:
        Returns if overlap.
    """
    return not (rect1[0] + rect1[2] <= rect2[0]
                or rect2[0] + rect2[2] <= rect1[0]
                or rect1[1] + rect1[3] <= rect2[1]
                or rect2[1] + rect2[3] <= rect1[1])


def rect_overlap_amount(rect1: Rect, rect2: Rect) -> Tuple[float, float]:
    """Return (overlap_x, overlap_y) between two rects.

    Args:
        rect1: first rect
        rect2: second rect

    Returns:
        Returns the overlap amount.
    """
    overlap_x = min(rect1[0] + rect1[2], rect2[0] + rect2[2]) \
        - max(rect1[0], rect2[0])
    overlap_y = min(rect1[1] + rect1[3], rect2[1] + rect2[3]) \
        - max(rect1[1], rect2[1])
    return overlap_x, overlap_y


def rect_center(rect: Rect) -> Tuple[float, float]:
    """Return center (x, y) of a rect.

    Args:
        rect: the rect.

    Returns:
        Returns the center.
    """
    return (rect[0] + rect[2] / 2, rect[1] + rect[3] / 2)


class Signal:
    """Minimal multicast delegate."""

    def __init__(self) -> None:
        """Initialize the signal."""
        self._listeners: List[Callable[..., None]] = []
        self._logger = Log.get("collision")

    def bind(self, callback: Callable[..., None]) -> None:
        """Bind a callback to the signal.

        Args:
            callback: a callable function.
        """
        self._listeners.append(callback)

    def unbind(self, callback: Callable[..., None]) -> None:
        """Unbind a callback to the signal.

        Args:
            callback: a callable function.
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    def broadcast(self, *args: Any, **kwargs: Any) -> None:
        """Broadcast on every bind callable.

        Args:
            args: args for callable function.
            kwargs: kwargs for callable function.
        """
        for callback in list(self._listeners):
            try:
                callback(*args, **kwargs)
            except Exception:
                self._logger.exception(f"Collision event handler {callback!r} "
                                       "raised")


class Collider:
    """A collidable region tied to an owner."""

    def __init__(
        self,
        owner: Any,
        get_rect: Callable[[], Rect],
        tag: str = "default",
        collides_with: Optional[List[str]] = None,
        blocking: bool = False,
        bounce: float = 0.0,
        static: bool = False,
        enabled: bool = True
    ) -> None:
        """Initialize a collider.

        Args:
            owner: the owner of the collider.
            get_rect: callable get the rect.
            tag: tag.
            collides_with: collides with type.
            blocking: block on collision.
            bounce: bounce distance on collision.
            static: static collider.
            enabled: enable the component.
        """
        self.owner = owner
        self.get_rect = get_rect
        self.tag = tag
        self.collides_with = collides_with
        self.blocking = blocking
        self.bounce = bounce
        self.static = static
        self.enabled = enabled

        self.on_begin_overlap = Signal()
        self.on_end_overlap = Signal()

    def rect(self) -> Rect:
        """Returns the rect as (x, y, width, height).

        Returns:
            Returns the rect."""
        return self.get_rect()

    def can_collide_with(self, other: "Collider") -> bool:
        """Check if can collide with other.

        Args:
            other: other collider.

        Returns:
            Returns True if the collision tag matches.
        """
        if self.collides_with is None:
            return True
        return other.tag in self.collides_with

    def draw_debug(self, renderer: Any, color: int = 0xFFFF0000,
                   thickness: int = 1) -> None:
        """Draw debug collision hitbox.

        Args:
            renderer: the renderer.
            color: the hitbox color.
            thickness: the thickness of the hitbox.
        """
        if not self.enabled:
            return
        rect = self.rect()
        renderer.draw_rect_outline(rect[0], rect[1], rect[2], rect[3],
                                   color, thickness)


class SpatialGrid:
    """Uniform spatial hash used as a broad phase."""

    def __init__(self, cell_size: int = 128) -> None:
        """Initialize a spacial grid.

        Args:
            cell_size: the cell size for each cell.
        """
        self.cell_size = cell_size
        self._cells: Dict[Tuple[int, int], List[Collider]] = {}

    def clear(self) -> None:
        """Clear the cells."""
        self._cells.clear()

    def _cell_range(self, rect: Rect) -> Tuple[int, int, int, int]:
        """Get the cell for the rect.

        Args:
            rect: a rectangle.

        Returns:
            Returns a cell position.
        """
        x, y, w, h = rect
        cs = self.cell_size
        cx0 = int(x // cs)
        cy0 = int(y // cs)
        cx1 = int((x + w) // cs)
        cy1 = int((y + h) // cs)
        return cx0, cy0, cx1, cy1

    def insert(self, collider: Collider, rect: Rect) -> None:
        """Insert a collider in the cell.

        Args:
            collider: the collider for the cell.
            rect: a rect for search the cell.
        """
        cx0, cy0, cx1, cy1 = self._cell_range(rect)
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                self._cells.setdefault((cx, cy), []).append(collider)

    def candidate_pairs(self) -> Any:
        """Generator for candidate pairs."""
        seen: Set[Tuple[Collider, Collider]] = set()
        for bucket in self._cells.values():
            n = len(bucket)
            if n < 2:
                continue
            for i in range(n):
                a = bucket[i]
                for j in range(i + 1, n):
                    b = bucket[j]
                    key = (a, b) if id(a) < id(b) else (b, a)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield key


class CollisionManager:
    """Manages collision detection and resolution."""

    def __init__(self, cell_size: int = 128,
                 max_correction_per_frame: float = 64.0) -> None:
        """Initialize collision manager.

        Args:
            cell_size: cell size.
            max_correction_per_frame: max correction per frame.
        """
        self._colliders: List[Collider] = []
        self._active_overlaps: Set[Tuple[Collider, Collider]] = set()
        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self.max_correction_per_frame = max_correction_per_frame
        self._grid = SpatialGrid(cell_size)
        self._logger = Log.get("collision")
        self._warned_no_bounds = False

    def init(self, width: int, height: int) -> None:
        """Initialize with width and height.

        Args:
            width: the width.
            height: the height.
        """
        self.width = width
        self.height = height

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
        collider = Collider(owner, get_rect, tag, collides_with,
                            blocking, bounce, static, enabled)
        self._colliders.append(collider)
        return collider

    def unregister(self, collider: Collider) -> None:
        """Unregister a collider.

        Args:
            collider: the collider to unregister.
        """
        if collider in self._colliders:
            self._colliders.remove(collider)
        self._active_overlaps = {
            pair for pair in self._active_overlaps
            if collider not in pair
        }

    def update(self) -> None:
        """Update the colliders."""
        active = [c for c in self._colliders if c.enabled]

        if len(active) < 1:
            return

        rects: Dict[Collider, Rect] = {}
        for c in active:
            try:
                rects[c] = c.rect()
            except Exception:
                self._logger.exception(f"rect() failed for {c.owner!r} "
                                       "skipping")

        active = [c for c in active if c in rects]

        self._resolve_boundaries(active, rects)

        current_overlaps: Set[Tuple[Collider, Collider]] = set()

        if len(active) >= 2:
            self._grid.clear()
            for c in active:
                rect = c.rect()
                rects[c] = rect
                self._grid.insert(c, rect)

            for a, b in self._grid.candidate_pairs():
                if not (a.enabled and b.enabled):
                    continue
                if not (a.can_collide_with(b) and b.can_collide_with(a)):
                    continue

                try:
                    rect_a = a.rect()
                    rect_b = b.rect()
                    overlapping = rect_collide_rect(rect_a, rect_b)
                except Exception:
                    self._logger.exception("Collision check failed between "
                                           f"{a.owner!r} and {b.owner!r}")
                    continue

                if not overlapping:
                    continue

                pair = (a, b) if id(a) < id(b) else (b, a)
                current_overlaps.add(pair)

                if a.blocking and b.blocking:
                    self._resolve_block(a, b)

        self._resolve_boundaries(active)

        began = current_overlaps - self._active_overlaps
        ended = self._active_overlaps - current_overlaps

        for a, b in began:
            a.on_begin_overlap.broadcast(a, b)
            b.on_begin_overlap.broadcast(b, a)

        for a, b in ended:
            a.on_end_overlap.broadcast(a, b)
            b.on_end_overlap.broadcast(b, a)

        self._active_overlaps = current_overlaps

    def _resolve_block(self, a: Collider, b: Collider) -> None:
        """Resolve two collider overlapping.

        Args:
            a: first collider.
            b: second collider.
        """
        try:
            rect_a = a.rect()
            rect_b = b.rect()
        except Exception:
            self._logger.exception(f"Collision resolve failed between "
                                   f"{a.owner!r} and {b.owner!r}")
            return

        overlap_x, overlap_y = rect_overlap_amount(rect_a, rect_b)

        if overlap_x <= 0 or overlap_y <= 0:
            return

        center_a = rect_center(rect_a)
        center_b = rect_center(rect_b)

        dx = center_a[0] - center_b[0]
        dy = center_a[1] - center_b[1]

        if dx == 0 and dy == 0:
            dx = 1.0 if (id(a) ^ id(b)) & 1 else -1.0

        if overlap_x < overlap_y:
            normal = Vector2(1, 0) if dx > 0 else Vector2(-1, 0)
            penetration = overlap_x
        else:
            normal = Vector2(0, 1) if dy > 0 else Vector2(0, -1)
            penetration = overlap_y

        if self.max_correction_per_frame is not None:
            penetration = min(penetration, self.max_correction_per_frame)

        a_movable = not a.static and hasattr(a.owner, "position")
        b_movable = not b.static and hasattr(b.owner, "position")

        if a_movable and b_movable:
            a_share, b_share = 0.5, 0.5
        elif a_movable:
            a_share, b_share = 1.0, 0.0
        elif b_movable:
            a_share, b_share = 0.0, 1.0
        else:
            return

        if a_movable and self._should_resolve(a, normal):
            a.owner.position += normal * penetration * a_share
            self._bounce(a, normal)

        if b_movable and self._should_resolve(b, -normal):
            b.owner.position -= normal * penetration * b_share
            self._bounce(b, -normal)

    @staticmethod
    def _should_resolve(collider: Collider, normal: Vector2) -> bool:
        """Check if should resolve the collider.

        Args:
            collider: the collider.
            normal: normal position.

        Returns:
            Returns if it should resolve.
        """
        velocity = getattr(collider.owner, "velocity", None)
        if velocity is None:
            return True
        return bool(velocity.dot(normal) < 0)

    @staticmethod
    def _bounce(collider: Collider, normal: Vector2) -> None:
        """Bounce the collider.

        Args:
            collider: the collider.
            normal: normal position.
        """
        velocity = getattr(collider.owner, "velocity", None)
        if velocity is None:
            return
        into_surface = velocity.dot(normal)
        if into_surface < 0:
            velocity -= (1 + collider.bounce) * into_surface * normal

    def _resolve_boundaries(
        self,
        colliders: List[Collider],
        rects: Optional[Dict[Collider, Rect]] = None
    ) -> None:
        """Resolve boundaries.

        Args:
            colliders: the colliders.
            rects: the rectangles.
        """
        if self.width is None or self.height is None:
            if not self._warned_no_bounds:
                self._logger.warning(
                    "CollisionManager.update() "
                    "called before init(width, height) — "
                    "boundary resolution is disabled until init() is called."
                )
                self._warned_no_bounds = True
            return

        for collider in colliders:
            if not collider.enabled or collider.static:
                continue

            owner = collider.owner
            if not hasattr(owner, "position"):
                continue

    def draw_debug(self, renderer: Any,
                   color_map: Optional[Dict[str, int]] = None) -> None:
        """Draw debug colloders.

        Args:
            renderer: the renderer.
            color_map: the color for collision owner.
        """
        if color_map is None:
            color_map = {
                "default": 0xFFFF0000,
                "player": 0xFF00FF00,
                "wall": 0xFFFF8800,
                "floor": 0xFF8888FF,
                "trigger": 0xFF00FFFF,
                "enemy": 0xFFFF00FF,
            }

        for collider in self._colliders:
            if not collider.enabled:
                continue

            rect = collider.rect()
            color = color_map.get(collider.tag, 0xFFFFFF00)

            if not collider.blocking:
                color &= 0x88FFFFFF

            renderer.draw_rect_outline(rect[0], rect[1], rect[2], rect[3],
                                       color, thickness=1)
