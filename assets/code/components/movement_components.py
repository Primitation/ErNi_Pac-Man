import random
from typing import Any, Callable, Optional, TYPE_CHECKING

from Engine import Vector2, Input, Component, World

if TYPE_CHECKING:
    from assets.code.actors.cell import Cell


class MovementComponent(Component):
    """Generic movement component."""

    def __init__(self, speed: float = 200.0, enabled: bool = True) -> None:
        """Initialize movement component.

        Args:
            speed: speed
            enabled: enabled
        """
        super().__init__(enabled)

        self.speed = speed
        self.direction = Vector2(0, 0)

    def set_direction(self, direction: Vector2) -> None:
        """Set direction.

        Args:
            direction: direction
        """
        """Set movement direction."""
        self.direction = direction

    def stop(self) -> None:
        """Stop movement."""
        self.direction = Vector2(0, 0)

    def update(self, dt: float) -> None:
        """Update movement.

        Args:
            dt: dt
        """
        if not self.actor:
            return

        direction = self.direction

        length = (direction.x ** 2 + direction.y ** 2) ** 0.5

        if length > 0:
            direction = Vector2(
                direction.x / length,
                direction.y / length
            )

            self.actor.velocity = Vector2(
                direction.x * self.speed,
                direction.y * self.speed
            )

        else:
            self.actor.velocity = Vector2(0, 0)


class PlayerMovementInput(Component):
    """Player input for movement."""

    def __init__(self) -> None:
        """Initialize player movement."""
        super().__init__()

        self.movement: MovementComponent | None = None

    def on_added(self, actor: Any) -> None:
        """On added to actor.

        Args:
            actor: actor
        """
        super().on_added(actor)

        self.movement = actor.get_component(
            MovementComponent
        )

    def update(self, dt: float) -> None:
        """Update input.

        Args:
            dt: dt time.
        """
        direction = Vector2(0, 0)

        if Input.is_action_held("left"):
            direction.x -= 1
            direction.y = 0

        if Input.is_action_held("right"):
            direction.x += 1
            direction.y = 0

        if Input.is_action_held("up"):
            direction.y -= 1
            direction.x = 0

        if Input.is_action_held("down"):
            direction.y += 1
            direction.x = 0

        if self.movement:
            self.movement.set_direction(direction)


class ChasePlayerComponent(Component):
    """Chase the player."""

    def update(self, dt: float) -> None:
        """Update chase.

        Args:
            dt: dt time.
        """
        from assets.code.actors.player import Player

        if not self.actor:
            return

        movement = self.actor.get_component(
            MovementComponent
        )

        player = World.find(Player)

        if player and movement:
            direction = Vector2(
                player.position.x - self.actor.position.x,
                player.position.y - self.actor.position.y
            )

            movement.set_direction(direction)


class GridMovementComponent(Component):
    """Pac-Man style grid movement."""

    def __init__(self, speed: float = 200.0, enabled: bool = True) -> None:
        """Init grid movement component

        Args:
            speed: speed
            enabled: enabled
        """
        super().__init__(enabled)

        self.speed = speed / 1000

        self.direction = Vector2(0, 0)
        self.target_direction = Vector2(0, 0)

        self.current_cell: Optional["Cell"] = None
        self.target_cell: Optional["Cell"] = None

        self.is_moving = False

        self.direction_strategy: Optional[Callable[..., Any]] = None

    def set_direction(self, direction: Vector2) -> None:
        """Store the wanted direction.

        Args:
            direction: direction
        """
        if direction.x > 0:
            self.target_direction = Vector2(1, 0)

        elif direction.x < 0:
            self.target_direction = Vector2(-1, 0)

        elif direction.y > 0:
            self.target_direction = Vector2(0, 1)

        elif direction.y < 0:
            self.target_direction = Vector2(0, -1)

    def stop(self) -> None:
        """Stop movement."""
        self.direction = Vector2(0, 0)
        self.target_direction = Vector2(0, 0)
        self.target_cell = None
        self.is_moving = False

    def _get_neighbor_cell(
        self, cell: Optional["Cell"], direction: Vector2
    ) -> Optional["Cell"]:
        """Get neighbor cell.

        Args:
            cell: cell
            direction: direction

        Returns:
            Returns neighbor cell.
        """
        if not cell:
            return None

        if direction.x > 0:
            return cell.east

        if direction.x < 0:
            return cell.west

        if direction.y > 0:
            return cell.south

        if direction.y < 0:
            return cell.north

        return None

    def _can_move_from_cell(
        self, cell: Optional["Cell"], direction: Vector2
    ) -> bool:
        """Returns can move from cell.

        Args:
            cell: cell
            direction: direction

        Returns:
            Returns can move from cell.
        """

        if not cell:
            return False

        if direction.x > 0:
            return cell.open_east

        if direction.x < 0:
            return cell.open_west

        if direction.y > 0:
            return cell.open_south

        if direction.y < 0:
            return cell.open_north

        return False

    def set_cell(self, cell: Optional["Cell"] = None) -> None:
        """Set current cell position.

        Args:
            cell: cell
        """

        if not self.actor:
            return

        if not cell:
            from assets.code.actors.cell import Cell

            closest = None
            distance = float("inf")

            for c in World.find_all(Cell):

                dx = c.position.x - self.actor.position.x
                dy = c.position.y - self.actor.position.y

                d = dx * dx + dy * dy

                if d < distance:
                    distance = d
                    closest = c

            cell = closest

        if not cell:
            return

        self.current_cell = cell
        self.actor.position = cell.position

    def _start_moving(self, direction: Vector2) -> bool:
        """Start movement if possible.

        Args:
            direction: direction
        """

        if not self.current_cell:
            return False

        if not self._can_move_from_cell(
            self.current_cell,
            direction
        ):
            return False

        next_cell = self._get_neighbor_cell(
            self.current_cell,
            direction
        )

        if not next_cell:
            return False

        self.direction = direction
        self.target_cell = next_cell
        self.is_moving = True

        return True

    def _choose_next_direction(self) -> None:
        """Choose next direction on arrival."""
        if self.direction_strategy:
            direction = self.direction_strategy(self)
            if direction and self._start_moving(direction):
                return

        if (
            self.target_direction.x != 0
            or self.target_direction.y != 0
        ):
            if self._start_moving(self.target_direction):
                return

        if (
            self.direction.x != 0
            or self.direction.y != 0
        ):
            if self._start_moving(self.direction):
                return

        self.direction = Vector2(0, 0)
        self.is_moving = False

    def update(self, dt: float) -> None:
        """Update grid movement.

        Args:
            dt: dt time.
        """
        if not self.actor:
            return

        if not self.current_cell:
            self.set_cell()

            if not self.current_cell:
                return

        if not self.is_moving:

            self._choose_next_direction()
            return

        if not self.target_cell:
            self.is_moving = False
            return

        target = self.target_cell.position
        current = self.actor.position

        dx = target.x - current.x
        dy = target.y - current.y

        distance = (
            dx * dx
            + dy * dy
        ) ** 0.5

        move = self.speed * dt

        if move >= distance:

            self.actor.position = target

            self.current_cell = self.target_cell
            self.target_cell = None

            self.is_moving = False

            self._choose_next_direction()

            return

        self.actor.position = Vector2(
            current.x + (dx / distance) * move,
            current.y + (dy / distance) * move
        )


class PlayerGridInput(Component):
    """Player input handler for grid-based movement."""

    def __init__(self) -> None:
        """Initialize player grid input."""
        super().__init__()
        self.movement: GridMovementComponent | None = None

    def on_added(self, actor: Any) -> None:
        """On added to actor.

        Args:
            actor: actor
        """
        super().on_added(actor)
        self.movement = actor.get_component(GridMovementComponent)

    def update(self, dt: float) -> None:
        """Update input.

        Args:
            dt: dt time.
        """
        if not self.movement:
            return

        direction = Vector2(0, 0)

        if Input.is_action_held("left"):
            direction.x -= 1
            direction.y = 0

        if Input.is_action_held("right"):
            direction.x += 1
            direction.y = 0

        if Input.is_action_held("up"):
            direction.y -= 1
            direction.x = 0

        if Input.is_action_held("down"):
            direction.y += 1
            direction.x = 0

        if direction.x != 0 or direction.y != 0:
            self.movement.set_direction(direction)


class ChaseTargetGridComponent(Component):
    """Generic grid-based chase behavior."""

    _DIRECTION_PRIORITY = (
        Vector2(0, -1),
        Vector2(-1, 0),
        Vector2(0, 1),
        Vector2(1, 0),
    )

    FLEE_RANDOMNESS = 0.2

    def __init__(
        self,
        target: Optional[Any] = None,
        speed_multiplier: float = 1.0
    ) -> None:
        """Chase target grid component.

        Args:
            target: target
            speed_multiplier: speed multiplier
        """
        super().__init__()
        self.target = target
        self.speed_multiplier = speed_multiplier

        self.fleeing = False

    def on_added(self, actor: Any) -> None:
        """On added to actor.

        Args:
            actor: actor
        """
        super().on_added(actor)

        movement = actor.get_component(GridMovementComponent)
        if movement:
            if self.speed_multiplier != 1.0:
                movement.speed *= self.speed_multiplier

            movement.direction_strategy = self._decide_direction

        if self.target is None:
            self._auto_target_player()

    def set_target(self, target: Any) -> None:
        """Retarget this component to chase a different Actor.

        Args:
            target: target
        """
        self.target = target

    def set_fleeing(self, fleeing: bool) -> None:
        """Toggle flee mode.

        Args:
            fleeing: fleeing
        """
        self.fleeing = fleeing

    def _auto_target_player(self) -> None:
        """Fall back to chasing the Player."""
        try:
            from assets.code.actors.player import Player
        except ImportError:
            return

        self.target = World.find(Player)

    def get_target_cell(self) -> Optional["Cell"]:
        """Returns the Cell currently being aimed at.

        Returns:
            Returns the Cell currently being aimed at."""
        if not self.target:
            return None

        target_movement: Optional[GridMovementComponent] = \
            self.target.get_component(GridMovementComponent)
        if not target_movement:
            return None

        return target_movement.current_cell

    def _decide_direction(
        self, movement: "GridMovementComponent"
    ) -> Optional[Vector2]:
        """Decide direction.

        Args:
            movement: movement

        Returns:
            Returns direction decided.
        """
        """Called by GridMovementComponent on arrival."""
        if self.target is None:
            self._auto_target_player()

        target_cell = self.get_target_cell()
        if not target_cell:
            return None

        return self._choose_direction(movement, target_cell)

    def update(self, dt: float) -> None:
        """No-op: decisions happen in _decide_direction.

        Args:
            dt: dt time.
        """
        pass

    def _choose_direction(
        self, movement: "GridMovementComponent", target_cell: "Cell"
    ) -> Optional[Vector2]:
        """Choose direction.

        Args:
            movement: movement
            target_cell: target cell

        Returns:
            Returns direction.
        """
        current_cell = movement.current_cell

        came_from = movement.direction

        best_direction: Optional[Vector2] = None
        best_score = float("inf")
        fallback_direction: Optional[Vector2] = None
        fallback_score = float("inf")
        valid_choices: list[Vector2] = []

        for direction in self._DIRECTION_PRIORITY:
            if not movement._can_move_from_cell(current_cell, direction):
                continue

            neighbor = movement._get_neighbor_cell(current_cell, direction)
            if not neighbor:
                continue

            dx = target_cell.position.x - neighbor.position.x
            dy = target_cell.position.y - neighbor.position.y
            distance = dx * dx + dy * dy

            score = -distance if self.fleeing else distance

            is_reverse = (
                (came_from.x != 0 or came_from.y != 0)
                and direction.x == -came_from.x
                and direction.y == -came_from.y
            )

            if score < fallback_score:
                fallback_score = score
                fallback_direction = direction

            if is_reverse and not self.fleeing:
                continue

            valid_choices.append(direction)

            if score < best_score:
                best_score = score
                best_direction = direction

        if (
            self.fleeing
            and len(valid_choices) > 1
            and random.random() < self.FLEE_RANDOMNESS
        ):
            return random.choice(valid_choices)

        return best_direction or fallback_direction


class ChasePlayerGridComponent(ChaseTargetGridComponent):
    """Direct chase (Blinky's classic behavior)."""
    pass


class PinkyChaseComponent(ChaseTargetGridComponent):
    """Ambush behavior: aims a few cells ahead."""

    AMBUSH_DISTANCE = 4

    def get_target_cell(self) -> Optional["Cell"]:
        """Get target cell.

        Returns:
            Returns target cell.
        """
        if not self.target:
            return None

        target_movement: Optional[GridMovementComponent] = \
            self.target.get_component(GridMovementComponent)
        if not target_movement or not target_movement.current_cell:
            return None

        facing = target_movement.direction
        if facing.x == 0 and facing.y == 0:
            facing = target_movement.target_direction

        cell = target_movement.current_cell

        for _ in range(self.AMBUSH_DISTANCE):
            next_cell = self._neighbor_in_direction(cell, facing)
            if not next_cell:
                break
            cell = next_cell

        return cell

    @staticmethod
    def _neighbor_in_direction(
        cell: "Cell", direction: Vector2
    ) -> Optional["Cell"]:
        """Returns neighbor in direction.

        Args:
            cell: cell
            direction: direction

        Returns:
            Returns neighbor in direction.
        """
        if direction.x > 0:
            return cell.east
        if direction.x < 0:
            return cell.west
        if direction.y > 0:
            return cell.south
        if direction.y < 0:
            return cell.north
        return None


class InkyChaseComponent(ChaseTargetGridComponent):
    """Unpredictable chase using a pivot."""

    LOOKAHEAD = 2

    def __init__(
        self,
        pivot: Optional[Any] = None,
        target: Optional[Any] = None,
        speed_multiplier: float = 1.0
    ) -> None:
        """Initialize inky chase component.

        Args:
            pivot: pivot
            target: target
            speed_multiplier: speed multiplier
        """
        super().__init__(target=target, speed_multiplier=speed_multiplier)
        self.pivot = pivot

    def set_pivot(self, pivot: Any) -> None:
        """Set the pivot actor.

        Args:
            pivot: pivot
        """
        self.pivot = pivot

    def get_target_cell(self) -> Optional["Cell"]:
        """Get target cell.

        Returns:
            Returns target cell.
        """
        if not self.target:
            return None

        target_movement: Optional[GridMovementComponent] = \
            self.target.get_component(GridMovementComponent)
        if not target_movement or not target_movement.current_cell:
            return None

        if not self.pivot:
            return target_movement.current_cell

        pivot_movement = self.pivot.get_component(GridMovementComponent)
        if not pivot_movement or not pivot_movement.current_cell:
            return target_movement.current_cell

        facing = target_movement.direction
        if facing.x == 0 and facing.y == 0:
            facing = target_movement.target_direction

        cell = target_movement.current_cell
        for _ in range(self.LOOKAHEAD):
            next_cell = PinkyChaseComponent._neighbor_in_direction(cell,
                                                                   facing)
            if not next_cell:
                break
            cell = next_cell

        pivot_pos = pivot_movement.current_cell.position

        aim_x = cell.position.x + (cell.position.x - pivot_pos.x)
        aim_y = cell.position.y + (cell.position.y - pivot_pos.y)

        return self._closest_cell_to(aim_x, aim_y)

    @staticmethod
    def _closest_cell_to(x: float, y: float) -> Optional["Cell"]:
        """Returns closest cell to.

        Args:
            x: x
            y: y

        Returns:
            Returns closest cell to.
        """
        from assets.code.actors.cell import Cell

        closest = None
        distance = float("inf")

        for c in World.find_all(Cell):
            dx = c.position.x - x
            dy = c.position.y - y
            d = dx * dx + dy * dy

            if d < distance:
                distance = d
                closest = c

        return closest


class ClydeChaseComponent(ChaseTargetGridComponent):
    """Chases directly while far, flees when close."""

    def __init__(
        self,
        flee_distance: float = 8,
        home_cell: Optional["Cell"] = None,
        target: Optional[Any] = None,
        speed_multiplier: float = 1.0
    ) -> None:
        """Initialize clyde chase component.

        Args:
            flee_distance: flee distance
            home_cell: home cell
            target: target
            speed_multiplier: speed multiplier
        """
        super().__init__(target=target, speed_multiplier=speed_multiplier)
        self.flee_distance = flee_distance
        self.home_cell = home_cell
        self._cell_size = 0.0

    def set_home_cell(self, cell: "Cell") -> None:
        """Set the home cell.

        Args:
            cell: cell
        """
        self.home_cell = cell

    def get_target_cell(self) -> Optional["Cell"]:
        """Get target cell.

        Returns:
            Returns target cell.
        """
        if not self.target or not self.actor:
            return None

        target_movement: Optional[GridMovementComponent] = \
            self.target.get_component(GridMovementComponent)
        movement = self.actor.get_component(GridMovementComponent)

        if not target_movement or not target_movement.current_cell:
            return None
        if not movement or not movement.current_cell:
            return None

        dx = (
            target_movement.current_cell.position.x
            - movement.current_cell.position.x
        )
        dy = (
            target_movement.current_cell.position.y
            - movement.current_cell.position.y
        )
        distance = (dx * dx + dy * dy) ** 0.5

        threshold = self.flee_distance * self._get_cell_size(
            movement.current_cell
        )

        if distance > threshold:
            return target_movement.current_cell

        return self.home_cell or self._find_home_cell(
            target_movement.current_cell
        )

    def _get_cell_size(self, cell: "Cell") -> float:
        """Get cell size.

        Args:
            cell: cell

        Returns:
            Returns cell size.
        """
        if self._cell_size != 0.0:
            return self._cell_size

        for neighbor in (cell.east, cell.west, cell.north, cell.south):
            if neighbor:
                dx = neighbor.position.x - cell.position.x
                dy = neighbor.position.y - cell.position.y
                self._cell_size = (dx * dx + dy * dy) ** 0.5
                break

        return self._cell_size or 1.0

    def _find_home_cell(self, target_cell: "Cell") -> Optional["Cell"]:
        """Find home cell.

        Args:
            target_cell: target cell

        Returns:
            Returns home cell.
        """
        from assets.code.actors.cell import Cell

        farthest = None
        farthest_distance = -1.0

        for c in World.find_all(Cell):
            dx = c.position.x - target_cell.position.x
            dy = c.position.y - target_cell.position.y
            d = dx * dx + dy * dy

            if d > farthest_distance:
                farthest_distance = d
                farthest = c

        self.home_cell = farthest
        return farthest


class ScatterGhostComponent(Component):
    """Ghost scatter behavior - move toward a corner."""

    def __init__(self, corner_cell: Optional["Cell"] = None) -> None:
        """Initialize scatter ghoszt component.

        Args:
            corner_cell: corner cell
        """
        super().__init__()
        self.corner_cell = corner_cell

    def update(self, dt: float) -> None:
        """Update scatter behavior.

        Args:
            dt: dt time.
        """
        if not self.actor:
            return

        movement = self.actor.get_component(GridMovementComponent)
        if not movement or not movement.current_cell:
            return

        if not self.corner_cell:
            self._find_corner_cell()
            if not self.corner_cell:
                return

        current_cell = movement.current_cell

        dx = self.corner_cell.position.x - current_cell.position.x
        dy = self.corner_cell.position.y - current_cell.position.y

        if abs(dx) > abs(dy):
            direction = Vector2(1 if dx > 0 else -1, 0)
        else:
            direction = Vector2(0, 1 if dy > 0 else -1)

        if movement._can_move_from_cell(current_cell, direction):
            movement.set_direction(direction)
        else:
            if abs(dx) > abs(dy):
                other_direction = Vector2(0, 1 if dy > 0 else -1)
            else:
                other_direction = Vector2(1 if dx > 0 else -1, 0)
            if movement._can_move_from_cell(current_cell, other_direction):
                movement.set_direction(other_direction)

    def _find_corner_cell(self) -> None:
        """Find a corner cell in the maze."""
        from assets.code.actors.cell import Cell

        cells = World.find_all(Cell)

        for cell in cells:
            corner_count = 0
            if not cell.open_north:
                corner_count += 1
            if not cell.open_east:
                corner_count += 1
            if not cell.open_south:
                corner_count += 1
            if not cell.open_west:
                corner_count += 1

            if corner_count >= 2:
                is_outer = False
                if not cell.open_north and not cell.open_west:
                    if not cell.north or not cell.west:
                        is_outer = True
                elif not cell.open_north and not cell.open_east:
                    if not cell.north or not cell.east:
                        is_outer = True
                elif not cell.open_south and not cell.open_west:
                    if not cell.south or not cell.west:
                        is_outer = True
                elif not cell.open_south and not cell.open_east:
                    if not cell.south or not cell.east:
                        is_outer = True

                if is_outer:
                    self.corner_cell = cell
                    return


class FaceDirectionComponent(Component):
    """Face the direction of movement."""

    def update(self, dt: float) -> None:
        """Update facing direction.

        Args:
            dt: dt time.
        """
        if not self.actor:
            return

        movement = self.actor.get_component(GridMovementComponent)
        if not movement:
            return

        if movement.is_moving:
            direction = movement.direction
        else:
            direction = movement.target_direction

        if direction.x > 0:
            self.actor.rotation = 0
        elif direction.x < 0:
            self.actor.rotation = 180
        elif direction.y < 0:
            self.actor.rotation = 270
        elif direction.y > 0:
            self.actor.rotation = 90


class GhostFaceDirectionComponent(Component):
    """Ghost-specific facing behavior."""

    def update(self, dt: float) -> None:
        """Update ghost facing direction.

        Args:
            dt: dt time.
        """
        if not self.actor:
            return

        movement = self.actor.get_component(GridMovementComponent)
        if not movement:
            return

        if movement.is_moving:
            direction = movement.direction
        else:
            direction = movement.target_direction

        if direction.x != 0:
            self.actor.rotation = 0
        elif direction.y < 0:
            self.actor.rotation = 270
        elif direction.y > 0:
            self.actor.rotation = 90
