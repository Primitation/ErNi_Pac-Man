import threading
from typing import TypeVar, Type

from .. import Log
from .. import Assets
from .. import Vector2


class Event:
    """Simple pub/sub event — subscribe callables, emit() calls all
    of them with whatever arguments you pass. Not just for actors:
    any system can subscribe to Actors.tick."""

    def __init__(self):
        self._listeners = []

    def subscribe(self, callback):
        self._listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def emit(self, *args, **kwargs):
        for callback in list(self._listeners):
            callback(*args, **kwargs)


class Actor:
    """Base class for anything the ActorSubsystem manages.

    Every actor carries a position, a size, and a sprite right on
    itself — so Renderer (and anything else, e.g. Collision) can
    read them directly off the actor, without per-actor callables
    like Collision.register()'s get_rect still uses.

    `sprite` isn't set once and stored — it's a property that
    resolves from AssetSubsystem's cache on every access.
    set_sprite() only queues the load and remembers the name, so
    `actor.sprite` naturally reads back None until the background
    load finishes, then the loaded Texture from then on — the same
    (cached, shared) object every other actor using that path gets.

    Override update().
    """

    def __init__(
        self,
        position: Vector2 = None,
        size: Vector2 = None,
    ):

        self.alive = True
        self.position = position if position is not None else Vector2.zero()
        self.size = size if size is not None else Vector2.zero()

        self._sprite_name = None

        self.logger = Log.get(self.__class__.__name__)

        Actors.add(self)

    @property
    def sprite(self):
        if self._sprite_name is None:
            return None
        return Assets.get(self._sprite_name)

    def set_sprite(self, name: str, path: str):
        """Queues the texture to load (piggybacks on an existing
        load/cache entry if `path` — or `name` — is already
        known, same as Assets.queue() always does) and remembers
        `name` so `.sprite` can resolve it once it's ready."""

        self._sprite_name = name
        Assets.queue(name, path)

    def update(self, dt):
        pass


T = TypeVar("T", bound=Actor)


class ActorSubsystem:
    """Ticks every registered actor once per frame. Deliberately NOT
    thread-driven: actors touch renderer-derived state (position,
    sprite) that Render/Collision read straight after, so ticking
    has to happen on the main thread, in step with everything else
    that reads that state."""

    def __init__(self):

        self._actors = []
        self._lock = threading.Lock()

        self.tick = Event()

    def init(self):
        """Call once, at startup. Kept for API symmetry with the
        other subsystems — there's no thread to spin up anymore."""
        pass

    def add(self, actor: Actor):
        """Registers the actor and subscribes its update() to the
        tick event. Thread-safe on the registration itself, even
        though ticking happens on the main thread."""

        with self._lock:
            self._actors.append(actor)

        self.tick.subscribe(actor.update)

    def remove(self, actor: Actor):

        with self._lock:
            if actor in self._actors:
                self._actors.remove(actor)

        self.tick.unsubscribe(actor.update)

    def update(self, dt):
        """Call once per frame from the main loop, passing the same
        dt (in ms) you got from your clock. Ticks every actor, then
        cleans up anything that marked itself not alive during this
        tick."""

        self.tick.emit(dt)

        with self._lock:
            dead = [actor for actor in self._actors if not actor.alive]

        for actor in dead:
            self.remove(actor)

    def close(self):
        """Kept for API symmetry — nothing to shut down anymore."""
        pass

    def spawn(
        self,
        actor_class: Type[T],
        *args,
        **kwargs
    ) -> T:

        return actor_class(
            *args,
            **kwargs
        )


# Global actor system
Actors = ActorSubsystem()
