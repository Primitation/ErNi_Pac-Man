# component.py
from abc import ABC
import math
from typing import Optional, Tuple, Union, Any

from ... import Vector2


class Component(ABC):
    """Base class for everything an Actor can carry as a component."""

    def __init__(
        self,
        enabled: bool = True,
        local_scale: Union[Vector2, Tuple[float, float]] = Vector2(1.0, 1.0),
        render_layer: int = 0
    ) -> None:
        self.actor: Optional[Any] = None
        self.enabled = enabled
        self.alive = True
        self.local_position: Union[Vector2, Tuple[float, float]] = \
            Vector2(0.0, 0.0)
        self.local_rotation = 0.0
        self.offset_rotates = True
        self.local_scale = local_scale
        self.render_layer = render_layer

    def on_added(self, actor: Any) -> None:
        """Called once by AActor.add_component()."""
        self.actor = actor

    def update(self, dt: float) -> None:
        """Override for per-frame work."""
        pass

    def destroy(self) -> None:
        """Override to release anything external."""
        self.alive = False

    def get_world_position(self) -> Tuple[float, float]:
        """Get the world position of this component."""
        if self.actor is None:
            return (0.0, 0.0)

        pos_x = self.actor.position.x
        pos_y = self.actor.position.y

        offset = self.local_position
        if isinstance(offset, Vector2):
            offset_x, offset_y = offset.x, offset.y
        else:
            offset_x, offset_y = offset[0], offset[1]

        if offset_x != 0.0 or offset_y != 0.0:
            if self.offset_rotates:
                rotation = getattr(self.actor, "rotation", 0.0) \
                    + self.local_rotation
                angle = math.radians(rotation)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)

                rotated_x = offset_x * cos_a - offset_y * sin_a
                rotated_y = offset_x * sin_a + offset_y * cos_a
                offset_x, offset_y = rotated_x, rotated_y

            pos_x += offset_x
            pos_y += offset_y

        return (pos_x, pos_y)

    def get_world_scale(self) -> Vector2:
        """World-space scale = local_scale * actor.scale."""
        scale = self.local_scale
        if isinstance(scale, Vector2):
            scale_x, scale_y = scale.x, scale.y
        else:
            scale_x, scale_y = scale[0], scale[1]

        actor_scale = getattr(self.actor, "scale", None) if self.actor \
            is not None else None
        if actor_scale is not None:
            actor_scale_x, actor_scale_y = (
                (actor_scale.x, actor_scale.y)
                if hasattr(actor_scale, "x")
                else (actor_scale[0], actor_scale[1])
            )
            scale_x *= actor_scale_x
            scale_y *= actor_scale_y

        return Vector2(scale_x, scale_y)
