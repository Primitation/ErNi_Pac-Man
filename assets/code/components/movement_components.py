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
        Called only when arriving on a cell.

        Priority:
        1. Buffered input
        2. Continue current direction
        """

        if (
            self.target_direction.x != 0 or
            self.target_direction.y != 0
        ):

            if self._start_moving(
                self.target_direction
            ):
                return


        if (
            self.direction.x != 0 or
            self.direction.y != 0
        ):

            self._start_moving(
                self.direction
            )


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


class ChasePlayerGridComponent(Component):
    """AI component for grid-based chasing behavior using cell references."""

    def __init__(self, speed_multiplier=1.0):
        super().__init__()
        self.speed_multiplier = speed_multiplier

    def on_added(self, actor):
        super().on_added(actor)
        # Optionally adjust speed
        movement = actor.get_component(GridMovementComponent)
        if movement:
            movement.speed *= self.speed_multiplier

    def update(self, dt):
        from assets.code.actors.player import Player

        movement = self.actor.get_component(GridMovementComponent)
        if not movement or not movement.current_cell:
            return

        player = World.find(Player)
        if not player:
            return

        # Get player's grid movement component
        player_movement = player.get_component(GridMovementComponent)
        if not player_movement or not player_movement.current_cell:
            return

        # Calculate direction based on cell positions
        current_cell = movement.current_cell
        target_cell = player_movement.current_cell

        # Find path direction (simple chase - choose dominant axis)
        dx = target_cell.position.x - current_cell.position.x
        dy = target_cell.position.y - current_cell.position.y

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
