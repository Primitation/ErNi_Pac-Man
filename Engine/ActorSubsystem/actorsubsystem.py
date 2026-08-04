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
        """Initialize an event."""
        self._listeners: List[Callable[..., None]] = []

    def subscribe(self, callback: Callable[..., None]) -> None:
        """Subscribe a callback to an event.

        Args:
            callback: a callable function.
        """
        self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[..., None]) -> None:
        """Unsubscribe a callback to an event.

        Args:
            callback: a callable function.
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        """Emit to each callback.

        Args:
            args: args for the callback functions.
            kwargs: kwargs for the callback functions.
        """
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
        """Initialize an abstarct actor.

        Args:
            position: the position.
            scale: the scale.
            static: the actor is static or not.
        """
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
        """Adds a component to the actor.

        Args:
            component: a component.

        Returns:
            Returns the component.
        """
        self.components.append(component)
        component.on_added(self)
        return component

    def remove_component(self, component: Any) -> None:
        """Removes a component from the actor.

        Args:
            component: a component.
        """
        if component in self.components:
            self.components.remove(component)
        component.destroy()

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """Gets a component from the actor with specific type.

        Args:
            component_type: a component type.

        Returns:
            Returns the first component found with the component_type.
        """
        for component in self.components:
            if isinstance(component, component_type):
                return component
        return None

    def get_components(self, component_type: Type[T]) -> List[T]:
        """Gets every components from the actor with specific type.

        Args:
            component_type: a component type.

        Returns:
            Returns every components found with the component_type.
        """
        result: List[T] = []
        for component in self.components:
            if isinstance(component, component_type):
                result.append(component)
        return result

    @property
    def rotation(self) -> float:
        """Actor rotation."""
        return getattr(self, '_rotation', 0.0)

    @rotation.setter
    def rotation(self, value: float) -> None:
        """Set actor rotation."""
        self._rotation = float(value)

    @property
    def pivot(self) -> Tuple[float, float]:
        """Actor pivot."""
        return getattr(self, '_pivot', (0.5, 0.5))

    @pivot.setter
    def pivot(self, value: Tuple[float, float]) -> None:
        """Set actor pivot."""
        self._pivot = value

    def _tick(self, dt: float) -> None:
        """Apply a tick.

        Args:
            dt: time for the tick.
        """
        for component in list(self.components):
            if component.enabled and component.alive:
                component.update(dt)
        self.update(dt)

    def update(self, dt: float) -> None:
        """Update the actor.

        Args:
            dt: time for the update.
        """
        pass

    def destroy(self) -> None:
        """Destroy the actor and it's components."""
        for component in list(self.components):
            component.destroy()
        self.components.clear()
        self.alive = False


class ActorSubsystem:
    """Ticks every registered actor once per frame."""

    def __init__(self) -> None:
        """Initialize an actor subsystem."""
        self._actors: List[AActor] = []
        self._lock = threading.Lock()
        self.tick = Event()
        self.paused: bool = False
        self.remaining_time: float = 0.0
        self.time_stop: bool = False
        self._logger = Log.get("actors")

    def init(self) -> None:
        """Initialyze. Call once, at startup."""
        pass

    def add(self, actor: AActor) -> None:
        """Adds an actor to the subsystem.

        Args:
            actor: an actor.
        """
        with self._lock:
            self._actors.append(actor)
        self.tick.subscribe(actor._tick)

    def clear(self) -> None:
        """Clear the subsystem by destroying every actors."""
        with self._lock:
            for actor in self._actors:
                actor.destroy()

    def remove(self, actor: AActor) -> None:
        """Removes an actor from the subsystem.

        Args:
            actor: an actor.
        """
        with self._lock:
            if actor in self._actors:
                self._actors.remove(actor)
                World.remove(actor)
        self.tick.unsubscribe(actor._tick)

    def pause(self) -> None:
        """Pause the subsystem."""
        self.paused = True
        self._logger.info("Actors paused")

    def resume(self) -> None:
        """Resume the subsystem."""
        self.paused = False
        self._logger.info("Actors resumed")

    def toggle_pause(self) -> bool:
        """Pause or resume the subsystem."""
        if self.paused:
            self.resume()
        else:
            self.pause()
        return self.paused

    def update(self, dt: float) -> None:
        """Update the subsystem.

        Args:
            dt: time for the update.
        """
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
        """Close the subsystem."""
        pass

    def spawn(
        self, actor_class: Type[TActor], *args: Any, **kwargs: Any
    ) -> TActor:
        """Spawns an actor to the subsystem.

        Args:
            actor_class: the actor class.
            args: the args for the actor class.
            kwargs: the kwargs for the actor class.

        Returns:
            Returns the actor spwaned.
        """
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
        """Find the spawn position.

        Args:
            width: the width.
            height: the height.
            existing: existing.
            max_attempts: max attempts.

        Returns:
            Returns the spawn position.
        """
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
        """Compute if overlap.

        Args:
            r1: actor 1 hitbox
            r2: actor 2 hitbox

        Returns:
            Returns True if hitboxes overlap, False otherwise.
        """
        return not (
            r1[0] + r1[2] <= r2[0]
            or r2[0] + r2[2] <= r1[0]
            or r1[1] + r1[3] <= r2[1]
            or r2[1] + r2[3] <= r1[1]
        )

    def set_level_time(self, level_time: float) -> None:
        """Set the level time limit.

        Args:
            level_time: the level time limit.
        """
        self.remaining_time = level_time


def on_end_of_anim(callback: Callable[..., None]) -> Callable[..., Any]:
    """Decorator for animation completion callbacks."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator for callable.

        Args:
            func: callable function.

        Returns:
            Returns a callable with this decorator.
        """
        @wraps(func)
        def wrapper(self: Any, component: Any, *args: Any,
                    **kwargs: Any) -> Any:
            """Wrapper.

            Args:
                component: a component.
                args: component args.
                kwargs: component kwargs.

            Returns:
                Returns the result.
            """
            logger = Log.get(self.__class__.__name__)
            original_set_animation = component.set_animation

            if hasattr(callback, "__self__"):
                cb = callback
            else:
                def cb() -> None:
                    callback(self)

            def intercepted_set_animation(*args: Any, **kwargs: Any) -> Any:
                """Intercept set animation.

                Args:
                    args: callable args.
                    kwargs: callable kwargs.

                Returns:
                    Returns the result
                """
                logger.debug("Intercepted set_animation "
                             f"for {self.__class__.__name__}")
                existing = kwargs.get("on_complete")

                def chained_callback() -> None:
                    """Chained callable."""
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
