import threading
from functools import wraps
from typing import TypeVar, Type, Callable

from .. import Log
from .. import Assets
from .. import Vector2
from .. import World
from .. import SpriteSheetKey, Animation


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


class AActor:
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
        scale: Vector2 = None,
        static=False,
    ):

        self.alive = True
        self.static = static

        self.position = (
            position
            if position is not None
            else Vector2.zero()
        )

        self.scale = (
            scale
            if scale is not None
            else Vector2(1, 1)
        )

        self._sprite_path = None

        # Sprite-sheet animation state — see set_animation()
        self._animation_key = None
        self._animation = None
        self._animation_fps = 10.0
        self._animation_loop = True
        self._animation_time = 0.0
        self._animation_on_complete = None
        self._animation_complete_fired = False

        self.logger = Log.get(self.__class__.__name__)

        Actors.add(self)

    @property
    def sprite(self):
        if self._animation_key is not None:
            if self._animation is None:
                frames = Assets.get(self._animation_key)
                if frames is None:
                    return None
                self._animation = Animation(
                    frames,
                    fps=self._animation_fps,
                    loop=self._animation_loop,
                )
            return self._animation.frame_at(self._animation_time)

        if self._sprite_path is None:
            return None
        return Assets.get(self._sprite_path)

    def set_sprite(self, path: str):
        self._animation_key = None
        self._animation = None
        self._sprite_path = path
        Assets.queue(path)

    def set_animation(
        self,
        path: str,
        frame_width: int,
        frame_height: int,
        frame_count: int = None,
        columns: int = None,
        start_frame: int = 0,
        fps: float = 10.0,
        loop: bool = True,
        on_complete=None,
    ):
        """Switch this actor to a sprite-sheet animation — walking,
        spawning, dying, whatever. Frames are sliced once per unique
        (path, frame_width, frame_height, frame_count, columns,
        start_frame) combo and shared across every actor using the
        same sheet + slicing, same caching model as set_sprite().

        start_frame lets several animations (e.g. walk vs. death) or
        several characters (e.g. each ghost color) share one sheet —
        it's the row-major index of the first frame to slice, so a
        death animation starting right after 4 walk frames would use
        start_frame=4.

        loop=False plays through once and holds on the last frame —
        use on_complete for a one-shot spawn/death animation to fire
        a callback (e.g. switch to the walk animation, or
        self.destroy()) the moment it finishes.
        """
        self._sprite_path = None

        self._animation_key = SpriteSheetKey(
            path, frame_width, frame_height, frame_count, columns, start_frame
        )
        self._animation = None
        self._animation_fps = fps
        self._animation_loop = loop
        self._animation_time = 0.0
        self._animation_on_complete = on_complete
        self._animation_complete_fired = False

        Assets.queue(self._animation_key)

    @property
    def rotation(self):
        """Rotation in degrees around the sprite's center."""
        return getattr(self, '_rotation', 0.0)

    @rotation.setter
    def rotation(self, value):
        self._rotation = float(value)

    # Also add a pivot point if you want off-center rotation
    @property
    def pivot(self):
        """Pivot point for rotation (as fraction of sprite size).
        Default: (0.5, 0.5) = center."""
        return getattr(self, '_pivot', (0.5, 0.5))

    @pivot.setter
    def pivot(self, value):
        self._pivot = value

    def _tick(self, dt):
        if self._animation_key is not None:
            self._animation_time += dt

            if (
                self._animation is not None
                and not self._animation_complete_fired
                and self._animation.finished(self._animation_time)
            ):
                self._animation_complete_fired = True

                self.logger.info(
                    f"Animation complete on {self.__class__.__name__}"
                )

                if self._animation_on_complete:
                    self.logger.info(
                        "Calling animation on_complete callback"
                    )
                    self._animation_on_complete()

        self.update(dt)

    def update(self, dt):
        pass

    def destroy(self):
        self.alive = False


T = TypeVar("T", bound=AActor)


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
        self.paused = False

        self._logger = Log.get("actors")

    def init(self):
        """Call once, at startup. Kept for API symmetry with the
        other subsystems — there's no thread to spin up anymore."""
        pass

    def add(self, actor: AActor):
        """Registers the actor and subscribes its update() to the
        tick event. Thread-safe on the registration itself, even
        though ticking happens on the main thread."""

        with self._lock:
            self._actors.append(actor)

        self.tick.subscribe(actor._tick)

    def clear(self):
        with self._lock:
            self._actors.clear()

    def remove(self, actor: AActor):
        with self._lock:
            if actor in self._actors:
                self._actors.remove(actor)
                World.remove(actor)

        self.tick.unsubscribe(actor._tick)

    def pause(self):
        """Freeze every actor's update() until resume()/toggle_pause()."""
        self.paused = True
        self._logger.info("Actors paused")

    def resume(self):
        """Resume ticking actors after pause()."""
        self.paused = False
        self._logger.info("Actors resumed")

    def toggle_pause(self) -> bool:
        """Flip paused state and return the new value."""
        if self.paused:
            self.resume()
        else:
            self.pause()
        return self.paused

    def update(self, dt):
        """Call once per frame from the main loop, passing the same
        dt (in ms) you got from your clock. Ticks every actor unless
        paused, then cleans up anything that marked itself not alive
        during this tick — cleanup still runs while paused so nothing
        piles up waiting for a resume()."""

        if not self.paused:
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

        random_spawn = kwargs.pop("random_spawn", False)

        actor = actor_class(
            *args,
            **kwargs
        )

        if random_spawn and hasattr(actor, "get_rect"):

            x, y, width, height = actor.get_rect()

            existing = [
                a.get_rect()
                for a in self._actors
                if hasattr(a, "get_rect") and a is not actor
            ]

            spawn_x, spawn_y = self.find_spawn_position(
                width,
                height,
                existing
            )

            actor.position.x = spawn_x
            actor.position.y = spawn_y

        World.add(actor)

        return actor

    def find_spawn_position(self, width, height, existing, max_attempts=30):
        import random
        from Engine import Renderer
        """Rejection-sample a position that doesn't overlap any
        already-spawned rect, so actors don't start on top of each
        other. Falls back to the last sampled position (still
        possibly overlapping) if it can't find a free spot in time —
        better than spinning forever once the screen gets crowded."""

        for _ in range(max_attempts):
            x = random.uniform(0, Renderer.width - width)
            y = random.uniform(0, Renderer.height - height)
            candidate = (x, y, width, height)

            if not any(self.rects_overlap(candidate, r) for r in existing):
                return x, y

        return x, y

    def rects_overlap(self, r1, r2):
        return not (
            r1[0] + r1[2] <= r2[0] or
            r2[0] + r2[2] <= r1[0] or
            r1[1] + r1[3] <= r2[1] or
            r2[1] + r2[3] <= r1[1]
        )


def on_end_of_anim(callback: Callable) -> Callable:
    """
    Decorator that automatically attaches a callback to the next
    set_animation() call made inside the decorated function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):

            logger = Log.get(self.__class__.__name__)

            original_set_animation = self.set_animation

            if hasattr(callback, "__self__"):
                cb = callback
            else:
                cb = lambda: callback(self)

            def intercepted_set_animation(*args, **kwargs):

                logger.debug(
                    f"Intercepted set_animation for {self.__class__.__name__}"
                )

                existing = kwargs.get("on_complete")

                def chained_callback():
                    logger.info(
                        f"Animation complete callback fired on "
                        f"{self.__class__.__name__}"
                    )

                    if existing:
                        logger.debug("Calling existing animation callback")
                        existing()

                    logger.debug("Calling decorator callback")
                    cb()

                kwargs["on_complete"] = chained_callback

                logger.debug(
                    "Injected on_complete callback into animation"
                )

                return original_set_animation(*args, **kwargs)

            self.set_animation = intercepted_set_animation

            try:
                return func(self, *args, **kwargs)

            finally:
                self.set_animation = original_set_animation
                logger.debug(
                    "Restored original set_animation"
                )

        return wrapper

    return decorator


# Global actor system
Actors = ActorSubsystem()
