class World:
    """Holds every actor that belongs to a given scene, for the
    renderer to draw. Deliberately separate from ActorSubsystem:
    Actors ticks EVERY actor in the game regardless of scene; a
    World is "what's currently on screen", so you can build a new
    World per level without touching ticking at all.

    Actor already carries .sprite/.position/.size itself, so World
    just needs the actor — nothing else to pass in.
    """

    def __init__(self):
        self._actors = []

    def add(self, actor):
        self._actors.append(actor)

    def remove(self, actor):
        if actor in self._actors:
            self._actors.remove(actor)

    def __iter__(self):
        return iter(self._actors)

    def __len__(self):
        return len(self._actors)
