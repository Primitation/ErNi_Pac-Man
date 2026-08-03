import threading
from functools import wraps
from typing import TypeVar, Type, Callable

from .. import Log
from .. import Vector2
from .. import World


class Event:
    """Simple pub/sub event."""

    def __init__(self):
        self._listeners = []

    def subscribe(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def unsubscribe(self, callback: Callable) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def emit(self, *args, **kwargs) -> None:
        for callback in list(self._listeners):
            callback(*args, **kwargs)


class AActor:
    """Base class for anything the ActorSubsystem manages."""

    def __init__(
        self,
        position: Vector2 | None = None,
        scale: Vector2 | None = None,
        static: bool = False,
    ):
        self.alive = True
        self.static = static

        self.position = position if position is not None else Vector2.zero()
        self.scale = scale if scale is not None else Vector2(1, 1)

        self.components = []
        self.logger = Log.get(self.__class__.__name__)

        Actors.add(self)

    def add_component(self, component):
        self.components.append(component)
        component.on_added(self)
        return component

    def remove_component(self, component) -> None:
        if component in self.components:
            self.components.remove(component)
        component.destroy()

    def get_component(self, component_type):
        for component in self.components:
            if isinstance(component, component_type):
                return component
        return None

    def get_components(self, component_type):
        return [
            component for component in self.components
            if isinstance(component, component_type)
        ]

    @property
    def rotation(self) -> float:
        return getattr(self, '_rotation', 0.0)

    @rotation.setter
    def rotation(self, value: float) -> None:
        self._rotation = float(value)

    @property
    def pivot(self) -> tuple[float, float]:
        return getattr(self, '_pivot', (0.5, 0.5))

    @pivot.setter
    def pivot(self, value: tuple[float, float]) -> None:
        self._pivot = value

    def _tick(self, dt: float) -> None:
        for component in list(self.components):
            if component.enabled and component.alive:
                component.update(dt)
        self.update(dt)

    def update(self, dt: float) -> None:
        pass

    def destroy(self) -> None:
        for component in list(self.components):
            component.destroy()
        self.components.clear()
        self.alive = False


T = TypeVar("T", bound=AActor)


class ActorSubsystem:
    """Ticks every registered actor once per frame."""

    def __init__(self):
        self._actors: list[AActor] = []
        self._lock = threading.Lock()
        self.tick = Event()
        self.paused = False
        self.remaining_time = 0.0
        self.time_stop = False
        self._logger = Log.get("actors")

    def init(self) -> None:
        """Call once, at startup."""
        pass

    def add(self, actor: AActor) -> None:
        with self._lock:
            self._actors.append(actor)
        self.tick.subscribe(actor._tick)

    def clear(self) -> None:
        with self._lock:
            for actor in self._actors:
                actor.destroy()

    def remove(self, actor: AActor) -> None:
        with self._lock:
            if actor in self._actors:
                self._actors.remove(actor)
                World.remove(actor)
        self.tick.unsubscribe(actor._tick)

    def pause(self) -> None:
        self.paused = True
        self._logger.info("Actors paused")

    def resume(self) -> None:
        self.paused = False
        self._logger.info("Actors resumed")

    def toggle_pause(self) -> bool:
        if self.paused:
            self.resume()
        else:
            self.pause()
        return self.paused

    def update(self, dt: float) -> None:
        from assets.code.actors.player import Player

        if not self.paused:
            self.tick.emit(dt)
            if not self.time_stop:
                self.remaining_time -= dt / 1000
            if self.remaining_time <= 0:
                Player.end_game = True

        with self._lock:
            dead = [actor for actor in self._actors if not actor.alive]

        for actor in dead:
            self.remove(actor)

    def close(self) -> None:
        pass

    def spawn(self, actor_class: Type[T], *args, **kwargs) -> T:
        random_spawn = kwargs.pop("random_spawn", False)
        actor = actor_class(*args, **kwargs)

        if random_spawn and hasattr(actor, "get_rect"):
            x, y, width, height = actor.get_rect()
            existing = [
                a.get_rect() for a in self._actors
                if hasattr(a, "get_rect") and a is not actor
            ]
            spawn_x, spawn_y = self.find_spawn_position(width, height,
                                                        existing)
            actor.position.x = spawn_x
            actor.position.y = spawn_y

        World.add(actor)
        return actor

    def find_spawn_position(self, width: float, height: float, existing: list,
                            max_attempts: int = 30) -> tuple[float, float]:
        import random
        from Engine import Renderer

        for _ in range(max_attempts):
            x = random.uniform(0, Renderer.width - width)
            y = random.uniform(0, Renderer.height - height)
            candidate = (x, y, width, height)
            if not any(self.rects_overlap(candidate, r) for r in existing):
                return x, y
        return x, y

    @staticmethod
    def rects_overlap(r1: tuple, r2: tuple) -> bool:
        return not (
            r1[0] + r1[2] <= r2[0] or
            r2[0] + r2[2] <= r1[0] or
            r1[1] + r1[3] <= r2[1] or
            r2[1] + r2[3] <= r1[1]
        )

    def set_level_time(self, level_time: float) -> None:
        self.remaining_time = level_time


def on_end_of_anim(callback: Callable) -> Callable:
    """Decorator for animation completion callbacks."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, component, *args, **kwargs):
            logger = Log.get(self.__class__.__name__)
            original_set_animation = component.set_animation

            if hasattr(callback, "__self__"):
                cb = callback
            else:
                def cb():
                    callback(self)

            def intercepted_set_animation(*args, **kwargs):
                logger.debug("Intercepted set_animation "
                             f"for {self.__class__.__name__}")
                existing = kwargs.get("on_complete")

                def chained_callback():
                    logger.info("Animation complete callback "
                                f"fired on {self.__class__.__name__}")
                    if existing:
                        logger.debug("Calling existing animation callback")
                        existing()
                    logger.debug("Calling decorator callback")
                    cb()

                kwargs["on_complete"] = chained_callback
                logger.debug("Injected on_complete callback into animation")
                return original_set_animation(*args, **kwargs)

            component.set_animation = intercepted_set_animation

            try:
                return func(self, component, *args, **kwargs)
            finally:
                component.set_animation = original_set_animation
                logger.debug("Restored original set_animation")

        return wrapper

    return decorator


Actors: ActorSubsystem = ActorSubsystem()
