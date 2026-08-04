# world.py
from typing import List, Optional, Type, TypeVar, Iterator, Any

T = TypeVar('T')


class WorldClass:
    """Contains actors belonging to the current scene."""

    def __init__(self) -> None:
        """Initialize the world."""
        self._actors: List[Any] = []

    def add(self, actor: Any) -> None:
        """Adds an actor in the world.

        Args:
            actor: an actor.
        """
        if actor not in self._actors:
            self._actors.append(actor)

    def remove(self, actor: Any) -> None:
        """Removes an actor in the world.

        Args:
            actor: an actor.
        """
        if actor in self._actors:
            self._actors.remove(actor)

    def clear(self) -> None:
        """Removes all actors.
        """
        self._actors.clear()

    def find(self, actor_class: Type[T]) -> Optional[T]:
        """Find the first actor matching the given class.

        Args:
            actor_class: actor class

        Returns:
            Returns the first actor with the class actor_class.
        """
        for actor in self._actors:
            if isinstance(actor, actor_class):
                return actor
        return None

    def find_all(self, actor_class: Type[T]) -> List[T]:
        """Find all actors matching the given class.

        Args:
            actor_class: actor class

        Returns:
            Returns every actors with the class actor_class.
        """
        return [
            actor for actor in self._actors
            if isinstance(actor, actor_class)
        ]

    def __iter__(self) -> Iterator[Any]:
        """Iterates over the actors.

        Returns:
            Returns iterator.
        """
        return iter(self._actors)

    def __len__(self) -> int:
        """Number of actors in the world.

        Returns:
            Returns the number of actors in the world.
        """
        return len(self._actors)


World = WorldClass()
