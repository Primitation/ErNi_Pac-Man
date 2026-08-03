class WorldClass:
    """Contains actors belonging to the current scene."""

    def __init__(self):
        self._actors = []

    def add(self, actor) -> None:
        if actor not in self._actors:
            self._actors.append(actor)

    def remove(self, actor) -> None:
        if actor in self._actors:
            self._actors.remove(actor)

    def clear(self) -> None:
        self._actors.clear()

    def find(self, actor_class):
        """Find the first actor matching the given class."""
        for actor in self._actors:
            if isinstance(actor, actor_class):
                return actor
        return None

    def find_all(self, actor_class):
        """Find all actors matching the given class."""
        return [
            actor for actor in self._actors
            if isinstance(actor, actor_class)
        ]

    def __iter__(self):
        return iter(self._actors)

    def __len__(self) -> int:
        return len(self._actors)


World = WorldClass()
