from .actor import Actor
from Engine import Vector2


class Player(Actor):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        sprite_path: str,
        tag: str = "Actor"
    ):
        super().__init__(
                position=position,
                scale=scale,
                velocity=velocity,
                scale=scale,
                sprite_path=sprite_path,
                tag=tag
            )
    
