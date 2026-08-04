from Engine import Component
from Engine import Particles


class OriginMarkerComponent(Component):
    """Debug dot at actor position."""

    def __init__(self, color: int = 0xFFFF0000, size: float = 6.0,
                 enabled: bool = True):
        super().__init__(enabled)
        self.color = color
        self.size = size

    def update(self, dt: float) -> None:
        """Emit debug particle."""
        if self.actor is None:
            return
        Particles.emit(
            self.actor.position,
            count=1,
            color=self.color,
            speed=(0.0, 0.0),
            size=(self.size, self.size),
            life=(0.1, 0.1),
            spread=0.0,
            gravity=0.0,
            fade=False,
        )
