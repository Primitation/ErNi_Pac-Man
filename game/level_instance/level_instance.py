"""Level instance"""

from Engine.World.world import World
from levelgen.level_gen import LevelGenerator
from levelgen.level_options import LevelOptions
from Engine import Vector2
from assets.code.actor import Player
from Engine import Actors


class LevelInstance:
    """Level instance.

    TODO
    """
    def __init__(self, level_options: LevelOptions) -> None:
        """Initializes a level instance.

        Args:
            level_options: options for the current level
        """
        self._level_options = level_options

    def load(self) -> None:
        self._level_structure = LevelGenerator.generate(self._level_options)
        # TODO: set the world

    def _scaling(self, vector: Vector2) -> Vector2:
        return vector  # TODO rescaling rule ?

    def start(self) -> None:
        """Start the level.
        """
        World.clear()

        # TODO: set world map: f(self._level_structure.maze)

        Actors.spawn(
            Player,
            position=self._level_structure.pacman,  # TODO ?
            velocity=Vector2(0, 0),
            scale=self._scaling(Vector2(0.25, 0.25)),  # TODO size
            sprite_path="assets/texture/pacman.png",  # TODO image
        )

        for ghost_position in self._level_structure.ghosts:
            Actors.spawn(
                Player,  # TODO: ghost
                position=ghost_position,  # TODO ?
                velocity=Vector2(0, 0),
                scale=self._scaling(Vector2(0.25, 0.25)),  # TODO size
                sprite_path="assets/texture/pacman.png",
            )

        for pacgum_position in self._level_structure.pacgums:
            Actors.spawn(
                Player,  # TODO: pacgum
                position=pacgum_position,  # TODO ?
                velocity=Vector2(0, 0),
                scale=self._scaling(Vector2(0.25, 0.25)),  # TODO size
                sprite_path="assets/texture/pacman.png",  # TODO image
            )

        for super_pacgum_position in self._level_structure.super_pacgums:
            Actors.spawn(
                Player,  # TODO: super pacgum
                position=super_pacgum_position,  # TODO ?
                velocity=Vector2(0, 0),
                scale=self._scaling(Vector2(0.25, 0.25)),  # TODO size
                sprite_path="assets/texture/pacman.png",  # TODO image
            )

        # TODO: set the interactions on each Actors
        # TODO start the game
