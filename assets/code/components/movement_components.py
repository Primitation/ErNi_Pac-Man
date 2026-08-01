from Engine import Vector2, Input, Component, World


class MovementComponent(Component):
    """
    Generic movement component.

    Does not care where the direction comes from.
    A player, AI, or other component can call set_direction().
    """

    def __init__(self, speed: float = 200.0, enabled=True):
        super().__init__(enabled)

        self.speed = speed
        self.direction = Vector2(0, 0)

    def set_direction(self, direction: Vector2):
        """
        Set movement direction.

        Example:
            movement.set_direction(Vector2(1, 0))
        """
        self.direction = direction

    def stop(self):
        self.direction = Vector2(0, 0)

    def update(self, dt):
        if not self.actor:
            return

        direction = self.direction

        # Normalize diagonal movement
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

    def __init__(self):
        super().__init__()

        self.movement = None

    def on_added(self, actor):
        super().on_added(actor)

        self.movement = actor.get_component(
            MovementComponent
        )

    def update(self, dt):

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

        self.movement.set_direction(direction)


class ChasePlayerComponent(Component):

    def update(self, dt):
        from assets.code.actors.player import Player

        movement = self.actor.get_component(
            MovementComponent
        )

        player = World.find(Player)

        direction = Vector2(
            player.position.x - self.actor.position.x,
            player.position.y - self.actor.position.y
        )

        movement.set_direction(direction)


class GridMovementComponent(Component):
    """
    Pac-Man style grid movement.

    The actor moves cell by cell.
    Input is buffered and applied when reaching the next cell.
    """

    def __init__(self, speed: float = 200.0, enabled=True):
        super().__init__(enabled)

        self.speed = speed/1000

        # Current movement direction
        self.direction = Vector2(0, 0)

        # Last player input direction
        self.target_direction = Vector2(0, 0)

        self.current_cell = None
        self.target_cell = None

        self.is_moving = False

        # Optional callable: (movement) -> Vector2 | None.
        # If set, called exactly when a new direction is needed (on
        # arrival at a cell), with current_cell already pointing at
        # the cell just arrived at. Lets AI-driven movement (chase
        # components) make a fresh, precise decision instead of
        # relying on a buffered compass direction like player input.
        self.direction_strategy = None



    def set_direction(self, direction: Vector2):
        """
        Store the wanted direction.
        Only cardinal directions are allowed.
        """

        if direction.x > 0:
            self.target_direction = Vector2(1, 0)

        elif direction.x < 0:
            self.target_direction = Vector2(-1, 0)

        elif direction.y > 0:
            self.target_direction = Vector2(0, 1)

        elif direction.y < 0:
            self.target_direction = Vector2(0, -1)


    def stop(self):
        self.direction = Vector2(0, 0)
        self.target_direction = Vector2(0, 0)
        self.target_cell = None
        self.is_moving = False


    def _get_neighbor_cell(self, cell, direction):
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


    def _can_move_from_cell(self, cell, direction):
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


    def set_cell(self, cell=None):

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


    def _start_moving(self, direction):
        """
        Start movement if the direction is possible
        from the current cell.
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


    def _choose_next_direction(self):
        """
        Called when arriving at a cell.
        Try an AI direction_strategy first (fresh, computed from
        this exact cell), then buffered input, then continue direction.
        """

        if self.direction_strategy:
            direction = self.direction_strategy(self)
            if direction and self._start_moving(direction):
                return

        # Try player buffered input
        if (
            self.target_direction.x != 0 or
            self.target_direction.y != 0
        ):
            if self._start_moving(self.target_direction):
                return


        # Try continuing current direction
        if (
            self.direction.x != 0 or
            self.direction.y != 0
        ):
            if self._start_moving(self.direction):
                return


        # Nothing possible
        self.direction = Vector2(0, 0)
        self.is_moving = False


    def update(self, dt):

        if not self.actor:
            return


        if not self.current_cell:
            self.set_cell()

            if not self.current_cell:
                return


        if not self.is_moving:

            self._choose_next_direction()
            return



        target = self.target_cell.position
        current = self.actor.position


        dx = target.x - current.x
        dy = target.y - current.y

        distance = (
            dx * dx +
            dy * dy
        ) ** 0.5


        move = self.speed * dt


        if move >= distance:

            # Arrive exactly on cell
            self.actor.position = target

            self.current_cell = self.target_cell
            self.target_cell = None

            self.is_moving = False

            # Decide next move
            self._choose_next_direction()

            return



        # Move toward target
        self.actor.position = Vector2(
            current.x + (dx / distance) * move,
            current.y + (dy / distance) * move
        )


class PlayerGridInput(Component):
    """Player input handler for grid-based movement."""

    def __init__(self):
        super().__init__()
        self.movement = None

    def on_added(self, actor):
        super().on_added(actor)
        self.movement = actor.get_component(GridMovementComponent)

    def update(self, dt):
        if not self.movement:
            return

        # Get input direction
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
    """
    Generic grid-based chase behavior.

    Unlike a component hardcoded to chase the Player, this one chases
    whatever Actor is set as `target` — the Player, another ghost,
    anything with a GridMovementComponent. The target can be swapped
    at runtime with set_target(), which is what lets a "tag" style
    mode hand the chase off from one ghost to another.

    Movement decisions use the same core idea as the original Pac-Man
    ghosts: at every intersection, look at each open direction (other
    than the one just arrived from) and pick whichever one lands on
    the cell closest to the current target tile. Reversing direction
    is only allowed when there is no other option (dead end).

    Subclasses only need to override get_target_cell() to reproduce
    the different ghost personalities (see PinkyChaseComponent,
    InkyChaseComponent, ClydeChaseComponent below); the movement /
    intersection logic here stays the same for all of them.
    """

    # Priority order used to break ties when two directions are
    # equally close to the target tile.
    _DIRECTION_PRIORITY = (
        Vector2(0, -1),  # up
        Vector2(-1, 0),  # left
        Vector2(0, 1),   # down
        Vector2(1, 0),   # right
    )

    def __init__(self, target=None, speed_multiplier: float = 1.0):
        super().__init__()
        self.target = target
        self.speed_multiplier = speed_multiplier

    def on_added(self, actor):
        super().on_added(actor)

        movement = actor.get_component(GridMovementComponent)
        if movement:
            if self.speed_multiplier != 1.0:
                movement.speed *= self.speed_multiplier

            # Decide direction exactly when the ghost needs one
            # (on arrival at a cell) instead of continuously — see
            # _decide_direction for why that matters.
            movement.direction_strategy = self._decide_direction

        if self.target is None:
            self._auto_target_player()

    def set_target(self, target) -> None:
        """Retarget this component to chase a different Actor."""
        self.target = target

    def _auto_target_player(self) -> None:
        """
        Fall back to chasing the Player when nobody explicitly set a
        target. Kept lazy/best-effort: if the Player doesn't exist
        yet (spawn order), _decide_direction retries this on every
        arrival until it succeeds, or until set_target() is called
        explicitly.
        """
        try:
            from assets.code.actors.player import Player
        except ImportError:
            return

        self.target = World.find(Player)

    def get_target_cell(self):
        """
        Return the Cell currently being aimed at.

        Default behavior is a direct chase (Blinky-style): the
        target's own current cell. Override for ambush-style or
        other targeting behavior.
        """
        if not self.target:
            return None

        target_movement = self.target.get_component(GridMovementComponent)
        if not target_movement:
            return None

        return target_movement.current_cell

    def _decide_direction(self, movement):
        """
        Called by GridMovementComponent's direction_strategy hook —
        exactly once, right as the ghost arrives at a cell, with
        movement.current_cell already pointing at that cell.

        This matters: computing the direction on every frame instead
        (from whatever cell the ghost was last AT, mid-move) means
        the choice is always one cell stale by the time it's used —
        a turn that's correct for the cell just left, applied at the
        cell just entered. Straight corridors hide that; the sharper
        turns needed to reach an ambush-style target (Pinky, Inky)
        don't, which is why they drift far off course while a direct
        chase (Blinky) mostly looks fine.
        """
        if self.target is None:
            self._auto_target_player()

        target_cell = self.get_target_cell()
        if not target_cell:
            return None

        return self._choose_direction(movement, target_cell)

    def update(self, dt):
        # No-op: direction decisions happen in _decide_direction via
        # movement.direction_strategy, called exactly once on arrival
        # at each cell rather than every frame.
        pass

    def _choose_direction(self, movement, target_cell):
        current_cell = movement.current_cell

        # movement.direction is the direction we're currently moving
        # in (or just arrived from) — used to forbid reversing.
        came_from = movement.direction

        best_direction = None
        best_distance = float("inf")
        fallback_direction = None
        fallback_distance = float("inf")

        for direction in self._DIRECTION_PRIORITY:
            if not movement._can_move_from_cell(current_cell, direction):
                continue

            neighbor = movement._get_neighbor_cell(current_cell, direction)
            if not neighbor:
                continue

            dx = target_cell.position.x - neighbor.position.x
            dy = target_cell.position.y - neighbor.position.y
            distance = dx * dx + dy * dy

            is_reverse = (
                (came_from.x != 0 or came_from.y != 0)
                and direction.x == -came_from.x
                and direction.y == -came_from.y
            )

            if distance < fallback_distance:
                fallback_distance = distance
                fallback_direction = direction

            if is_reverse:
                continue

            if distance < best_distance:
                best_distance = distance
                best_direction = direction

        # Only reverse into a dead end if there was truly no other option.
        return best_direction or fallback_direction


class ChasePlayerGridComponent(ChaseTargetGridComponent):
    """
    Backward-compatible name: direct chase (Blinky's classic
    behavior), auto-targeting the Player. Functionally identical to
    ChaseTargetGridComponent used with no target — kept as an alias
    so existing code/readability isn't disrupted.
    """
    pass


class PinkyChaseComponent(ChaseTargetGridComponent):
    """
    Ambush behavior: aims a few cells ahead of the target's current
    facing direction instead of the target's own cell, so it tries
    to cut the target off rather than tail it.
    """

    AMBUSH_DISTANCE = 4

    def get_target_cell(self):
        if not self.target:
            return None

        target_movement = self.target.get_component(GridMovementComponent)
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
    def _neighbor_in_direction(cell, direction):
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
    """
    Unpredictable chase: draws a line from a `pivot` Actor
    (traditionally another ghost, e.g. Blinky) through a point a
    couple of cells ahead of the target, then doubles that line to
    get the final target tile. Erratic when the pivot is far from
    the target, aggressive when it's close.
    """

    LOOKAHEAD = 2

    def __init__(self, pivot=None, target=None, speed_multiplier=1.0):
        super().__init__(target=target, speed_multiplier=speed_multiplier)
        self.pivot = pivot

    def set_pivot(self, pivot) -> None:
        self.pivot = pivot

    def get_target_cell(self):
        if not self.target:
            return None

        target_movement = self.target.get_component(GridMovementComponent)
        if not target_movement or not target_movement.current_cell:
            return None

        # No pivot wired up (e.g. Blinky hasn't been assigned yet) —
        # fall back to a direct chase rather than freezing in place.
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
            next_cell = PinkyChaseComponent._neighbor_in_direction(cell, facing)
            if not next_cell:
                break
            cell = next_cell

        pivot_pos = pivot_movement.current_cell.position

        aim_x = cell.position.x + (cell.position.x - pivot_pos.x)
        aim_y = cell.position.y + (cell.position.y - pivot_pos.y)

        return self._closest_cell_to(aim_x, aim_y)

    @staticmethod
    def _closest_cell_to(x, y):
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
    """
    Chases directly while far from the target, but flees toward
    `home_cell` once within `flee_distance` *cells* — classic Clyde:
    aggressive at range, shy up close.
    """

    def __init__(
        self,
        flee_distance: float = 8,
        home_cell=None,
        target=None,
        speed_multiplier=1.0,
    ):
        super().__init__(target=target, speed_multiplier=speed_multiplier)
        self.flee_distance = flee_distance
        self.home_cell = home_cell
        self._cell_size = None

    def set_home_cell(self, cell) -> None:
        self.home_cell = cell

    def get_target_cell(self):
        if not self.target:
            return None

        target_movement = self.target.get_component(GridMovementComponent)
        movement = self.actor.get_component(GridMovementComponent)

        if not target_movement or not target_movement.current_cell:
            return None
        if not movement or not movement.current_cell:
            return None

        dx = target_movement.current_cell.position.x - movement.current_cell.position.x
        dy = target_movement.current_cell.position.y - movement.current_cell.position.y
        distance = (dx * dx + dy * dy) ** 0.5

        # flee_distance is expressed in cells, but cell positions are
        # in world units — scale the threshold by the actual spacing
        # between cells instead of comparing raw pixels to a "8".
        threshold = self.flee_distance * self._get_cell_size(movement.current_cell)

        if distance > threshold:
            return target_movement.current_cell

        return self.home_cell or self._find_home_cell(target_movement.current_cell)

    def _get_cell_size(self, cell) -> float:
        if self._cell_size is not None:
            return self._cell_size

        for neighbor in (cell.east, cell.west, cell.north, cell.south):
            if neighbor:
                dx = neighbor.position.x - cell.position.x
                dy = neighbor.position.y - cell.position.y
                self._cell_size = (dx * dx + dy * dy) ** 0.5
                break

        return self._cell_size or 1.0

    def _find_home_cell(self, target_cell):
        """
        No explicit home_cell was set — pick (and cache) whichever
        maze cell is farthest from the target as a stand-in "corner"
        to retreat to, so Clyde actually moves away instead of
        targeting the cell it's already standing on.
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

    def __init__(self, corner_cell=None):
        super().__init__()
        self.corner_cell = corner_cell

    def update(self, dt):
        movement = self.actor.get_component(GridMovementComponent)
        if not movement or not movement.current_cell:
            return

        # If no corner cell is set, try to find a corner cell
        if not self.corner_cell:
            self._find_corner_cell()
            if not self.corner_cell:
                return

        current_cell = movement.current_cell

        # Calculate direction to corner cell
        dx = self.corner_cell.position.x - current_cell.position.x
        dy = self.corner_cell.position.y - current_cell.position.y

        # Choose the dominant direction
        if abs(dx) > abs(dy):
            direction = Vector2(1 if dx > 0 else -1, 0)
        else:
            direction = Vector2(0, 1 if dy > 0 else -1)

        # Check if we can move in that direction
        if movement._can_move_from_cell(current_cell, direction):
            movement.set_direction(direction)
        else:
            # Try the other direction if blocked
            other_direction = Vector2(0, 1 if dy > 0 else -1) if abs(dx) > abs(dy) else Vector2(1 if dx > 0 else -1, 0)
            if movement._can_move_from_cell(current_cell, other_direction):
                movement.set_direction(other_direction)

    def _find_corner_cell(self):
        """Find a corner cell in the maze."""
        from assets.code.actors.cell import Cell

        cells = World.find_all(Cell)

        # Find cells at corners (where multiple walls meet)
        for cell in cells:
            # Check if this is a corner cell
            # A corner cell should have walls in two adjacent directions
            corner_count = 0
            if not cell.open_north: corner_count += 1
            if not cell.open_east: corner_count += 1
            if not cell.open_south: corner_count += 1
            if not cell.open_west: corner_count += 1

            # Check if it's a corner (2 or more walls)
            if corner_count >= 2:
                # Check if it's an outer corner
                is_outer = False
                if not cell.open_north and not cell.open_west:
                    # NW corner - check if it's at the edge
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

    def update(self, dt):
        if not self.actor:
            return

        movement = self.actor.get_component(GridMovementComponent)
        if not movement:
            return

        # Face based on current direction
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

    def update(self, dt):
        if not self.actor:
            return

        movement = self.actor.get_component(GridMovementComponent)
        if not movement:
            return

        if movement.is_moving:
            direction = movement.direction
        else:
            direction = movement.target_direction

        # Ghosts always face forward regardless of horizontal direction
        if direction.x != 0:
            self.actor.rotation = 0
        elif direction.y < 0:
            self.actor.rotation = 270
        elif direction.y > 0:
            self.actor.rotation = 90
