from __future__ import annotations

from abc import ABC
from typing import Any, Dict, List, Tuple, Type

from Engine import World, Actors, Vector2
from ..code.actors.player import Player


class Level(ABC):
    """Base class for level definitions."""

    def __init__(self) -> None:
        """Initialize level."""
        self.actors: List[Tuple[Type[Any], Dict[str, Any]]] = []

    def load(self) -> None:
        """Load level."""
        World.clear()
        Actors.clear()
        self._spawn_actors()

    def _spawn_actors(self) -> None:
        """Spawn all actors from the actors list"""
        for actor_class, kwargs in self.actors:
            Actors.spawn(actor_class, **kwargs)

    def add_actor(self, actor_class: Type[Any],
                  **kwargs: Any) -> None:
        """Helper method to add an actor to be spawned

        Args:
            actor_class: actor class
            **kwargs: **kwargs
        """
        self.actors.append((actor_class, kwargs))


class Level1(Level):
    """First level."""

    def __init__(self) -> None:
        """Initialize level 1"""
        super().__init__()
        self.add_actor(Player, position=Vector2(0, 0),
                       velocity=Vector2(0, 0), scale=Vector2(0.25, 0.25))
