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


class FaceDirectionComponent(Component):

    def update(self, dt):

        velocity = self.actor.velocity

        if velocity.x > 0:
            self.actor.rotation = 0
        elif velocity.x < 0:
            self.actor.rotation = 180
        elif velocity.y < 0:
            self.actor.rotation = 270
        elif velocity.y > 0:
            self.actor.rotation = 90


class GhostFaceDirectionComponent(Component):

    def update(self, dt):

        velocity = self.actor.velocity

        if velocity.x > 0:
            self.actor.rotation = 0
        elif velocity.x < 0:
            self.actor.rotation = 0
        elif velocity.y < 0:
            self.actor.rotation = 270
        elif velocity.y > 0:
            self.actor.rotation = 90