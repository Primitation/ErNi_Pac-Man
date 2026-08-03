from typing import Callable, Any

from .. import Log
from .. import Vector2


def rect_collide_rect(rect1: tuple, rect2: tuple) -> bool:
    """Check if two rects overlap."""
    return not (rect1[0] + rect1[2] <= rect2[0] or
                rect2[0] + rect2[2] <= rect1[0] or
                rect1[1] + rect1[3] <= rect2[1] or
                rect2[1] + rect2[3] <= rect1[1])


def rect_overlap_amount(rect1: tuple, rect2: tuple) -> tuple[float, float]:
    """Return (overlap_x, overlap_y) between two rects."""
    overlap_x = min(rect1[0] + rect1[2], rect2[0]
                    + rect2[2]) - max(rect1[0], rect2[0])
    overlap_y = min(rect1[1] + rect1[3], rect2[1]
                    + rect2[3]) - max(rect1[1], rect2[1])
    return overlap_x, overlap_y


def rect_center(rect: tuple) -> tuple[float, float]:
    """Return center (x, y) of a rect."""
    return (rect[0] + rect[2] / 2, rect[1] + rect[3] / 2)


class Signal:
    """Minimal multicast delegate."""

    def __init__(self):
        self._listeners = []
        self._logger = Log.get("collision")

    def bind(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def unbind(self, callback: Callable) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def broadcast(self, *args, **kwargs) -> None:
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
        get_rect: Callable,
        tag: str = "default",
        collides_with: list[str] | None = None,
        blocking: bool = False,
        bounce: float = 0.0,
        static: bool = False,
        enabled: bool = True
    ):
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

    def rect(self) -> tuple:
        """Returns the rect as (x, y, width, height)."""
        rect = self.get_rect()
        if isinstance(rect, (tuple, list)):
            return rect
        return (rect.x, rect.y, rect.width, rect.height)

    def can_collide_with(self, other: "Collider") -> bool:
        if self.collides_with is None:
            return True
        return other.tag in self.collides_with

    def draw_debug(self, renderer, color: int = 0xFFFF0000,
                   thickness: int = 1) -> None:
        if not self.enabled:
            return
        rect = self.rect()
        renderer.draw_rect_outline(rect[0], rect[1], rect[2], rect[3],
                                   color, thickness)


class SpatialGrid:
    """Uniform spatial hash used as a broad phase."""

    def __init__(self, cell_size: int = 128):
        self.cell_size = cell_size
        self._cells: dict[tuple[int, int], list] = {}

    def clear(self) -> None:
        self._cells.clear()

    def _cell_range(self, rect: tuple) -> tuple[int, int, int, int]:
        x, y, w, h = rect
        cs = self.cell_size
        cx0 = int(x // cs)
        cy0 = int(y // cs)
        cx1 = int((x + w) // cs)
        cy1 = int((y + h) // cs)
        return cx0, cy0, cx1, cy1

    def insert(self, collider: Collider, rect: tuple) -> None:
        cx0, cy0, cx1, cy1 = self._cell_range(rect)
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                self._cells.setdefault((cx, cy), []).append(collider)

    def candidate_pairs(self):
        seen = set()
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
                 max_correction_per_frame: float = 64.0):
        self._colliders: list[Collider] = []
        self._active_overlaps: set[tuple[Collider, Collider]] = set()
        self.width: int | None = None
        self.height: int | None = None
        self.max_correction_per_frame = max_correction_per_frame
        self._grid = SpatialGrid(cell_size)
        self._logger = Log.get("collision")
        self._warned_no_bounds = False

    def init(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def register(self, owner: Any, get_rect: Callable, tag: str = "default",
                 collides_with: list[str] | None = None,
                 blocking: bool = False, bounce: float = 0.0,
                 static: bool = False, enabled: bool = True) -> Collider:
        collider = Collider(owner, get_rect, tag, collides_with,
                            blocking, bounce, static, enabled)
        self._colliders.append(collider)
        return collider

    def unregister(self, collider: Collider) -> None:
        if collider in self._colliders:
            self._colliders.remove(collider)
        self._active_overlaps = {
            pair for pair in self._active_overlaps
            if collider not in pair
        }

    def update(self) -> None:
        active = [c for c in self._colliders if c.enabled]

        if len(active) < 1:
            return

        rects = {}
        for c in active:
            try:
                rects[c] = c.rect()
            except Exception:
                self._logger.exception(f"rect() failed for {c.owner!r}"
                                       " skipping")

        active = [c for c in active if c in rects]

        self._resolve_boundaries(active, rects)

        current_overlaps: set[tuple[Collider, Collider]] = set()

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
        velocity = getattr(collider.owner, "velocity", None)
        if velocity is None:
            return True
        return velocity.dot(normal) < 0

    @staticmethod
    def _bounce(collider: Collider, normal: Vector2) -> None:
        velocity = getattr(collider.owner, "velocity", None)
        if velocity is None:
            return
        into_surface = velocity.dot(normal)
        if into_surface < 0:
            velocity -= (1 + collider.bounce) * into_surface * normal

    def _resolve_boundaries(self, colliders: list[Collider],
                            rects: dict | None = None) -> None:
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

    def draw_debug(self, renderer, color_map: dict | None = None) -> None:
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
