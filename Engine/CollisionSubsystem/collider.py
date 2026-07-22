import itertools

from .. import Log
from .. import Vector2


def rect_collide_rect(rect1, rect2):
    """Check if two rects (x, y, w, h) overlap."""
    return not (rect1[0] + rect1[2] <= rect2[0] or
                rect2[0] + rect2[2] <= rect1[0] or
                rect1[1] + rect1[3] <= rect2[1] or
                rect2[1] + rect2[3] <= rect1[1])


def rect_overlap_amount(rect1, rect2):
    """Return (overlap_x, overlap_y) between two rects."""
    overlap_x = min(rect1[0] + rect1[2], rect2[0] + rect2[2]) - max(rect1[0], rect2[0])
    overlap_y = min(rect1[1] + rect1[3], rect2[1] + rect2[3]) - max(rect1[1], rect2[1])
    return overlap_x, overlap_y


def rect_center(rect):
    """Return center (x, y) of a rect."""
    return (rect[0] + rect[2] / 2, rect[1] + rect[3] / 2)


class Signal:
    """Minimal multicast delegate — the same idea as Unreal's
    dynamic multicast delegates (OnComponentBeginOverlap, etc).
    Bind any number of callables, broadcast() calls them all. A
    handler that raises is logged and skipped, it won't stop the
    other handlers from running."""

    def __init__(self):

        self._listeners = []
        self._logger = Log.get("collision")

    def bind(self, callback):

        self._listeners.append(callback)

    def unbind(self, callback):

        if callback in self._listeners:
            self._listeners.remove(callback)

    def broadcast(self, *args, **kwargs):

        for callback in list(self._listeners):

            try:
                callback(*args, **kwargs)
            except Exception:
                self._logger.exception(
                    f"Collision event handler {callback!r} raised"
                )


class Collider:
    """A collidable region tied to an owner. get_rect is a callable
    returning the current rect as (x, y, width, height) — pass e.g.
    a lambda that returns a tuple, so the collider always reflects
    the sprite's live position/size with no manual syncing.

    blocking: if True on BOTH colliders in a pair, overlap gets
    physically resolved each frame (pushed apart + bounced) instead
    of just firing overlap events. Needs owner.position (and
    owner.velocity, for bounce) to exist — a plain Vector2
    attribute, same as Player already has.

    bounce: restitution, 0..1. 0 = velocity into the surface is
    absorbed (stops dead on that axis), 1 = fully elastic bounce.

    static: this collider never moves when resolving a block, even
    if it has a position (e.g. walls, floors)."""

    def __init__(
        self,
        owner,
        get_rect,
        tag="default",
        collides_with=None,
        blocking=False,
        bounce=0.0,
        static=False,
        enabled=True
    ):

        self.owner = owner
        self.get_rect = get_rect
        self.tag = tag
        self.collides_with = collides_with  # None = collides with any tag
        self.blocking = blocking
        self.bounce = bounce
        self.static = static
        self.enabled = enabled

        self.on_begin_overlap = Signal()
        self.on_end_overlap = Signal()

    def rect(self):
        """Returns the rect as (x, y, width, height)."""
        rect = self.get_rect()
        # If it's already a tuple/list, return it
        if isinstance(rect, (tuple, list)):
            return rect
        # If it's some other object with x, y, width, height attributes
        return (rect.x, rect.y, rect.width, rect.height)

    def can_collide_with(self, other):

        if self.collides_with is None:
            return True

        return other.tag in self.collides_with


class CollisionManager:

    def __init__(self):

        self._colliders = []
        self._active_overlaps = set()  # set of (collider, collider) pairs

        self._logger = Log.get("collision")

    def register(
        self,
        owner,
        get_rect,
        tag="default",
        collides_with=None,
        blocking=False,
        bounce=0.0,
        static=False,
        enabled=True
    ) -> Collider:

        collider = Collider(
            owner,
            get_rect,
            tag,
            collides_with,
            blocking,
            bounce,
            static,
            enabled
        )

        self._colliders.append(collider)

        return collider

    def unregister(self, collider):

        if collider in self._colliders:
            self._colliders.remove(collider)

        self._active_overlaps = {
            pair for pair in self._active_overlaps
            if collider not in pair
        }

    def update(self):
        """Call once per frame."""
        
        # First, resolve boundaries for all colliders
        self._resolve_boundaries()
        
        current_overlaps = set()
        active = [collider for collider in self._colliders if collider.enabled]
        
        for a, b in itertools.combinations(active, 2):
            if not (a.can_collide_with(b) and b.can_collide_with(a)):
                continue
                
            try:
                rect_a = a.rect()
                rect_b = b.rect()
                overlapping = rect_collide_rect(rect_a, rect_b)
            except Exception:
                self._logger.exception(f"Collision check failed between {a.owner!r} and {b.owner!r}")
                continue
                
            if not overlapping:
                continue
                
            pair = (a, b) if id(a) < id(b) else (b, a)
            current_overlaps.add(pair)
            
            if a.blocking and b.blocking:
                self._resolve_block(a, b)
        
        # Resolve boundaries again after object-object collisions
        self._resolve_boundaries()
        
        began = current_overlaps - self._active_overlaps
        ended = self._active_overlaps - current_overlaps
        
        for a, b in began:
            a.on_begin_overlap.broadcast(a, b)
            b.on_begin_overlap.broadcast(b, a)
            
        for a, b in ended:
            a.on_end_overlap.broadcast(a, b)
            b.on_end_overlap.broadcast(b, a)
            
        self._active_overlaps = current_overlaps

    def _resolve_block(self, a, b):
        """Push a pair of blocking colliders apart along whichever
        axis (x or y) has the least overlap, then bounce each
        side's velocity off that axis. A collider only moves/bounces
        if it isn't static and its owner has a .position (and, for
        bounce, a .velocity) attribute."""

        try:
            rect_a = a.rect()
            rect_b = b.rect()
        except Exception:
            self._logger.exception(
                f"Collision resolve failed between "
                f"{a.owner!r} and {b.owner!r}"
            )
            return

        overlap_x, overlap_y = rect_overlap_amount(rect_a, rect_b)

        if overlap_x <= 0 or overlap_y <= 0:
            return

        center_a = rect_center(rect_a)
        center_b = rect_center(rect_b)

        if overlap_x < overlap_y:
            normal = Vector2(1, 0) if center_a[0] < center_b[0] else Vector2(-1, 0)
            penetration = overlap_x
        else:
            normal = Vector2(0, 1) if center_a[1] < center_b[1] else Vector2(0, -1)
            penetration = overlap_y

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

    def _should_resolve(self, collider, normal):
        """
        Returns True only if the collider is moving into the surface.

        normal points away from the collider it hit.
        """

        velocity = getattr(collider.owner, "velocity", None)

        if velocity is None:
            return True

        # Moving away from the surface
        if velocity.dot(normal) >= 0:
            return False

        return True

    def _bounce(self, collider, normal):
        """Reflect the owner's velocity off `normal` (which points
        away from the other collider), scaled by this collider's
        bounce. Only the velocity component heading into the
        surface is affected."""

        velocity = getattr(collider.owner, "velocity", None)

        if velocity is None:
            return

        into_surface = velocity.dot(normal)

        if into_surface < 0:
            velocity -= (1 + collider.bounce) * into_surface * normal

    def _resolve_boundaries(self):
        """Resolve all colliders against screen boundaries."""
        for collider in self._colliders:
            if not collider.enabled:
                continue
                
            rect = collider.rect()
            position = collider.owner.position
            velocity = getattr(collider.owner, "velocity", None)
            
            # X boundary
            if rect[0] < 0:
                position.x = 0
                if velocity is not None:
                    velocity.x = abs(velocity.x)
            elif rect[0] + rect[2] > WIDTH:
                position.x = WIDTH - rect[2]
                if velocity is not None:
                    velocity.x = -abs(velocity.x)
            
            # Y boundary
            if rect[1] < 0:
                position.y = 0
                if velocity is not None:
                    velocity.y = abs(velocity.y)
            elif rect[1] + rect[3] > HEIGHT:
                position.y = HEIGHT - rect[3]
                if velocity is not None:
                    velocity.y = -abs(velocity.y)
