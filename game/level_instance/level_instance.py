"""Level instance"""

import time

from Engine import Assets
from Engine import Collision
from Engine import Input
from Engine import Log
from Engine import Renderer
from Engine import World
from game.game_instance.player import PlayerInformation
from game.levelgen import LevelGenerator
from game.levelgen import LevelOptions
from Engine import Vector2
from assets.code.player import Player
from Engine import Actors


class LevelInstance:
    """Level instance.

    TODO
    """
    def __init__(self,
                 level_options: LevelOptions,
                 player_information: PlayerInformation) -> None:
        """Initializes a level instance.

        Args:
            level_options: options for the current level
        """
        self._level_options = level_options
        self._player_information = player_information
        self._level_structure = None

    def load(self) -> None:
        """Load the world structure.

        Load before start
        """
        Log.get("level").info("Level instance start load structure")
        self._level_structure = LevelGenerator.generate(self._level_options)
        Log.get("level").info("Level instance load ready")
        # TODO: set the world

    def _scaling(self, vector: Vector2) -> Vector2:
        return vector  # TODO rescaling rule ?

    def start(self) -> None:
        """Start the level.
        """
        Log.get("level").info("Level instance start init")
        if self._level_structure is None:
            Log.get("info").info("LevelInstance: Need to load or no level")
            return
        World.clear()
        Actors.clear()

        # TODO: set world map: f(self._level_structure.maze)
        Collision.init(self._level_structure.width,
                       self._level_structure.height)
        def tmp_put_wall_collision(): # TODO DELETE / OPTIMIZE
            tmp_maze = self._level_structure.maze
            for w in range(self._level_structure.width):
                for h in range(self._level_structure.height):
                    if self._level_structure.maze[h][w] & 8:  # West
                        #TODO: Collision: add a wall w-1 h
                        pass
                    if self._level_structure.maze[h][w] & 1:  # West
                        #TODO: Collision: add a wall w h+1
                        pass
        tmp_put_wall_collision()
        Log.get("level").info("Level instance walls ready")

        pacman_actor = Actors.spawn(
            Player,
            position=self._level_structure.pacman,  # TODO ?
            velocity=Vector2(0, 0),
            scale=self._scaling(Vector2(0.25, 0.25))  # TODO size
        )

        ghosts_actor = [
            Actors.spawn(
                Player,  # TODO: ghost
                position=ghost_position,  # TODO ?
                velocity=Vector2(0, 0),
                scale=self._scaling(Vector2(0.25, 0.25))  # TODO size
            )
            for ghost_position in self._level_structure.ghosts
        ]

        pacgum_actors = [
            Actors.spawn(
                Player,  # TODO: pacgum
                position=pacgum_position,  # TODO ?
                velocity=Vector2(0, 0),
                scale=self._scaling(Vector2(0.10, 0.10))  # TODO size
            )
            for pacgum_position in self._level_structure.pacgums
        ]

        super_pacgum_actors = [
            Actors.spawn(
                Player,  # TODO: super pacgum
                position=super_pacgum_position,  # TODO ?
                velocity=Vector2(0, 0),
                scale=self._scaling(Vector2(0.2, 0.2))  # TODO size
            )
            for super_pacgum_position in self._level_structure.super_pacgums
        ]
        Log.get("level").info("Level instance actors ready")
        # TODO: set the interactions on each Actors
        """
        collisions non blocking:
            pacman_actor: ghosts_actor pacgum_actors super_pacgum_actors
            ghosts_actor, pacgum_actors, super_pacgum_actors: pacman_actor
        """
        """
        On collision (X collides Y, what X does):
            pacman_actor:
                ghosts_actor:
                    if super_pacman then + score
                    else pacman delete + lives-1
                pacgum_actors:
                    score
                super_pacgum_actors:
                    super pacman + score
            pacgum_actors, super_pacgum_actors:
                pacman_actor:
                    delete pacgum / super pacgum
            ghosts_actor:
                pacman_actor:
                    if super_pacman then delete
        """

        # TODO: AI ghosts

        # TODO start the game
        Log.get("level").info("Level instance start")
        # TODO: this is an example temporary example:
        if 1:
            log = Log.get("main")
            log.info("Booting smoke test...")

            log.info(
                f"World has {len(World)} actor(s)."
            )

            last_time = time.perf_counter()
            fps_timer = 0.0
            fps_frames = 0
            fps = 0
            Renderer.bake(World)

            def frame(_param):

                nonlocal last_time
                nonlocal fps_timer
                nonlocal fps_frames
                nonlocal fps

                now = time.perf_counter()

                dt = (now - last_time) * 1000
                last_time = now

                fps_timer += dt
                fps_frames += 1

                if fps_timer >= 1000:
                    fps = fps_frames

                    # Update once per second
                    Renderer._logger.info(
                        f"Engine smoke test | FPS: {fps} | Actors: {len(World)}"
                    )

                    fps_frames = 0
                    fps_timer -= 1000

                Input.process_events()

                Input.process_actions()

                Assets.update()

                Actors.update(dt)
                if not Actors.paused:
                    Collision.update()
                Renderer.render(World)

                # Runs last: downgrades PRESSED -> HELD and RELEASED -> IDLE only
                # after everything this frame (process_actions, actor updates,
                # collision, render) has had a chance to see the fresh state.
                Input.update()

            Renderer.hook_loop(frame)

            log.info("Entering mlx loop.")

            Renderer.loop()
        # TODO: end example
        Log.get("level").info("Level instance end")
