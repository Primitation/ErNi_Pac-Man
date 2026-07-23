class WorldClass:
    """Contains actors belonging to the current scene.

    ActorSubsystem handles lifetime/ticking.
    World handles scene visibility/rendering.
    """

    def __init__(self):
        self._actors = []

    def add(self, actor):
        if actor not in self._actors:
            self._actors.append(actor)

    def remove(self, actor):
        if actor in self._actors:
            self._actors.remove(actor)

    def clear(self):
        self._actors.clear()

    def __iter__(self):
        return iter(self._actors)

    def __len__(self):
        return len(self._actors)


World = WorldClass()
