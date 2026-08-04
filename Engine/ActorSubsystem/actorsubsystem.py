# actorsubsystem.py
import threading
from functools import wraps
from typing import TypeVar, Type, Callable, List, Optional, Tuple, Any

from .. import Log
from .. import Vector2
from ..World.world import World
from .Components.component import Component


class Event:
    """Simple pub/sub event."""

    def __init__(self) -> None:
        self._listeners: List[Callable[..., None]] = []

    def subscribe(self, callback: Callable[..., None]) -> None:
        self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[..., None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for callback in list(self._listeners):
            callback(*args, **kwargs)


T = TypeVar("T", bound="Component")
TActor = TypeVar("TActor", bound="AActor")


class AActor:
    """Base class for anything the ActorSubsystem manages."""

    def __init__(
        self,
        position: Optional[Vector2] = None,
        scale: Optional[Vector2] = None,
        static: bool = False,
    ) -> None:
        self.alive: bool = True
        self.static: bool = static

        self.position: Vector2 = position \
            if position is not None else Vector2.zero()
        self.scale: Vector2 = scale if scale is not None else Vector2(1, 1)

        self.components: List[Any] = []
        self.logger = Log.get(self.__class__.__name__)

        self._rotation: float = 0.0
        self._pivot: Tuple[float, float] = (0.5, 0.5)

        Actors.add(self)

    def add_component(self, component: Any) -> Any:
        self.components.append(component)
        component.on_added(self)
        return component

    def remove_component(self, component: Any) -> None:
        if component in self.components:
            self.components.remove(component)
        component.destroy()

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        for component in self.components:
            if isinstance(component, component_type):
                return component
        return None

    def get_components(self, component_type: Type[T]) -> List[T]:
        result: List[T] = []
        for component in self.components:
            if isinstance(component, component_type):
                result.append(component)
        return result

    @property
    def rotation(self) -> float:
        return getattr(self, '_rotation', 0.0)

    @rotation.setter
    def rotation(self, value: float) -> None:
        self._rotation = float(value)

    @property
    def pivot(self) -> Tuple[float, float]:
        return getattr(self, '_pivot', (0.5, 0.5))

    @pivot.setter
    def pivot(self, value: Tuple[float, float]) -> None:
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


class ActorSubsystem:
    """Ticks every registered actor once per frame."""

    def __init__(self) -> None:
        self._actors: List[AActor] = []
        self._lock = threading.Lock()
        self.tick = Event()
        self.paused: bool = False
        self.remaining_time: float = 0.0
        self.time_stop: bool = False
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

    def spawn(
        self, actor_class: Type[TActor], *args: Any, **kwargs: Any
    ) -> TActor:
        random_spawn = kwargs.pop("random_spawn", False)
        actor = actor_class(*args, **kwargs)

        if random_spawn and hasattr(actor, "get_rect"):
            rect = actor.get_rect()
            if isinstance(rect, tuple) and len(rect) == 4:
                x, y, width, height = rect
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

    def find_spawn_position(
        self,
        width: float,
        height: float,
        existing: List[Any],
        max_attempts: int = 30
    ) -> Tuple[float, float]:
        import random
        from Engine import Renderer

        x, y = 0.0, 0.0
        for _ in range(max_attempts):
            x = random.uniform(0, Renderer.width - width)
            y = random.uniform(0, Renderer.height - height)
            candidate = (x, y, width, height)
            if not any(self.rects_overlap(candidate, r) for r in existing):
                return x, y
        return x, y

    @staticmethod
    def rects_overlap(r1: Tuple[float, float, float, float],
                      r2: Tuple[float, float, float, float]) -> bool:
        return not (
            r1[0] + r1[2] <= r2[0]
            or r2[0] + r2[2] <= r1[0]
            or r1[1] + r1[3] <= r2[1]
            or r2[1] + r2[3] <= r1[1]
        )

    def set_level_time(self, level_time: float) -> None:
        self.remaining_time = level_time


def on_end_of_anim(callback: Callable[..., None]) -> Callable[..., Any]:
    """Decorator for animation completion callbacks."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: Any, component: Any, *args: Any,
                    **kwargs: Any) -> Any:
            logger = Log.get(self.__class__.__name__)
            original_set_animation = component.set_animation

            if hasattr(callback, "__self__"):
                cb = callback
            else:
                def cb() -> None:
                    callback(self)

            def intercepted_set_animation(*args: Any, **kwargs: Any) -> Any:
                logger.debug("Intercepted set_animation "
                             f"for {self.__class__.__name__}")
                existing = kwargs.get("on_complete")

                def chained_callback() -> None:
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
