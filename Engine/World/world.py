# world.py
from typing import List, Optional, Type, TypeVar, Iterator, Any

T = TypeVar('T')


class WorldClass:
    """Contains actors belonging to the current scene."""

    def __init__(self) -> None:
        self._actors: List[Any] = []

    def add(self, actor: Any) -> None:
        if actor not in self._actors:
            self._actors.append(actor)

    def remove(self, actor: Any) -> None:
        if actor in self._actors:
            self._actors.remove(actor)

    def clear(self) -> None:
        self._actors.clear()

    def find(self, actor_class: Type[T]) -> Optional[T]:
        """Find the first actor matching the given class."""
        for actor in self._actors:
            if isinstance(actor, actor_class):
                return actor
        return None

    def find_all(self, actor_class: Type[T]) -> List[T]:
        """Find all actors matching the given class."""
        return [
            actor for actor in self._actors
            if isinstance(actor, actor_class)
        ]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._actors)

    def __len__(self) -> int:
        return len(self._actors)


World = WorldClass()
