from __future__ import annotations

from typing import Optional, Type, Any
from threading import Timer

from Engine.ActorSubsystem.Components.animated_sprite_component import (
    AnimatedSpriteComponent)
from assets.code.components.cheat_components import CheatComponent
from .actor import Actor
import random
from Engine import Vector2
from ..components.movement_components import (
    ChasePlayerGridComponent,
    ChaseTargetGridComponent,
    GridMovementComponent,
    InkyChaseComponent,
    ClydeChaseComponent,
    PinkyChaseComponent)


EDIBLEGHOST_INDEX = 32
DEADGHOST_INDEX = 28

FRIGHTENED_SPEED_MULTIPLIER = 0.5


class BasicGhost(Actor):
    """A basic ghost Actor."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 100.0,
        color_index: int = 0,
        chase_component: Type[ChaseTargetGridComponent] = (
            ChasePlayerGridComponent),
        chase_kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            collision=["Player"]
        )

        self.movement: GridMovementComponent = self.add_component(
            GridMovementComponent(speed=speed))
        self.chase: ChaseTargetGridComponent = self.add_component(
            chase_component(**(chase_kwargs or {}))
        )
        facevalue = random.randrange(8)
        self.face: AnimatedSpriteComponent = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=16,
                frame_height=16,
                frame_count=1,
                fps=1,
                loop=False,
                start_frame=160 + facevalue,
                center=True,
                render_layer=2
            )
        )

        self.color_index: int = color_index

        self._edible: bool = False
        self._dead: bool = False
        self._base_speed: float = self.movement.speed
        self.add_component(CheatComponent())
        self._dead_timer: Timer | None = None

        self.animation: AnimatedSpriteComponent = self.add_component(
            AnimatedSpriteComponent(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=32,
                frame_height=32,
                frame_count=4,
                fps=4,
                loop=True,
                start_frame=color_index,
                center=True,
                render_layer=1
            )
        )

    @property
    def dead(self) -> bool:
        return self._dead

    @dead.setter
    def dead(self, value: bool) -> None:
        if self._dead == value:
            return
        if self._dead_timer:
            self._dead_timer.cancel()
            self._dead_timer = None

        self._dead = value
        if value:
            self._dead_timer = Timer(
                5,
                lambda: setattr(self, "dead", False)
            )
            self._dead_timer.start()

        self.update_ghost_mode()

    @property
    def edible(self) -> bool:
        return self._edible

    @edible.setter
    def edible(self, value: bool) -> None:
        if self._edible == value:
            return

        self._edible = value

        self.update_ghost_mode()

    def update_ghost_mode(self) -> None:
        """Update ghost appearance and behavior."""
        if self.edible and not self.dead:
            self.animation.set_animation(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=32,
                frame_height=32,
                frame_count=8,
                fps=4,
                loop=True,
                start_frame=EDIBLEGHOST_INDEX
            )
            self.face.enabled = False
        else:
            self.animation.set_animation(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=32,
                frame_height=32,
                frame_count=4,
                fps=4,
                loop=True,
                start_frame=self.color_index
            )
            self.face.enabled = True
        if self.dead:
            self.animation.set_animation(
                "assets/texture/spritesheets"
                "/pacman_hd/PacManAssets-Ghosts.png",
                frame_width=32,
                frame_height=32,
                frame_count=8,
                fps=4,
                loop=True,
                start_frame=DEADGHOST_INDEX
            )
            self.movement.enabled = False
            self.face.enabled = False
        else:
            self.movement.enabled = True
            self.face.enabled = True

        if hasattr(self.chase, "set_fleeing"):
            self.chase.set_fleeing(self.edible)

        if self.movement.speed != 0:
            self.movement.speed = self._current_speed()

    def _current_speed(self) -> float:
        if self.edible:
            return self._base_speed * FRIGHTENED_SPEED_MULTIPLIER
        return self._base_speed

    def update(self, dt: float) -> None:
        """Update ghost."""
        super().update(dt)

    def destroy(self) -> None:
        """Destroy ghost."""
        self.logger.debug("destroy")
        super().destroy()

    def freeze_input(self) -> None:
        """Toggle freeze state."""
        if self.movement.speed == 0:
            self.movement.speed = self._current_speed()
        else:
            self.movement.speed = 0

    def set_chase_target(self, target: Any) -> None:
        """Retarget who this ghost is chasing."""
        self.chase.set_target(target)


class RedGhost(BasicGhost):
    """Red ghost (Blinky)."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 100.0,
    ) -> None:
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            color_index=0
        )


class BlueGhost(BasicGhost):
    """Blue ghost (Inky)."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 100.0,
        pivot: Optional[Any] = None,
    ) -> None:
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            color_index=4,
            chase_component=InkyChaseComponent,
            chase_kwargs={"pivot": pivot},
        )

    def set_pivot(self, pivot: Any) -> None:
        """Wire up the pivot ghost."""
        self.chase.set_pivot(pivot)  # type: ignore


class YellowGhost(BasicGhost):
    """Yellow ghost (Clyde)."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 100.0,
    ) -> None:
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            color_index=20,
            chase_component=ClydeChaseComponent
        )


class PinkGhost(BasicGhost):
    """Pink ghost (Pinky)."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        tag: str = "Actor",
        speed: float = 100.0,
    ) -> None:
        super().__init__(
            position=position,
            scale=scale,
            velocity=velocity,
            tag=tag,
            color_index=8,
            chase_component=PinkyChaseComponent
        )
