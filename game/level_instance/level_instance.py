"""Level instance"""

import time
from typing import Tuple
from Engine import (Assets, Collision, Input, Log, Renderer, World,
                    Vector2, Actors)
from Engine.ParticlesSubsystem.particlessubsystem import Particles
from assets.code.actors.ghost import (
    RedGhost, BlueGhost, YellowGhost, PinkGhost)
from assets.code.actors.pacgum import Pacgum, SuperPacgum
from assets.code.actors.wall import (Wall, WallEast, WallNorth,
                                     WallSouth, WallWest)
from game.game_instance.player_information import PlayerInformation
from game.levelgen import LevelGenerator, LevelOptions
from assets.code.actors.player import Player
from game.levelgen.maze_analyzer import MazeAnalyzer


class LevelInstance:
    """A level instance.

    Can start the level.
    """
    def __init__(self, level_options: LevelOptions) -> None:
        """Initializes a level instance.
    TILE_SIZE = 48

        Args:
            level_options: options for the current level.
        """
        self._level_options = level_options
        self._level_structure = None

    def load(self) -> None:
        """Load the world structure.

        Load before start.
        """
        if self._level_structure is not None:
            Log.get("level").info("Level instance already loaded")
            return
        Log.get("level").info("Level instance start load structure")
        self._level_structure = LevelGenerator.generate(self._level_options)
        Log.get("level").info("Level instance load ready")

    def _world_position(self, position: Vector2) -> Vector2:
        return Vector2(
            position.x * self.TILE_SIZE,
            position.y * self.TILE_SIZE,
        )


        if self._level_structure is None:
            self.load()

    def start(self, player_information: PlayerInformation) -> None:
        """Initialize and start the level.

        World.clear()
        Actors.clear()

        # TODO: SCORES + LIVES (player) to link !
        player_information.reset()  # TODO: DELETE !!!
        curr_pacman_data = self._world_position(
            self._level_structure.pacman
        )

        curr_ghosts_data = [
            self._world_position(pos)
            for pos in self._level_structure.ghosts
        ]

        curr_pacgums_data = [
            self._world_position(pos)
            for pos in self._level_structure.pacgums
        ]

        curr_super_pacgums_data = [
            self._world_position(pos)
            for pos in self._level_structure.super_pacgums
        ]

        maze_width = self._level_structure.width * self.TILE_SIZE
        maze_height = self._level_structure.height * self.TILE_SIZE

        Collision.init(maze_width, maze_height)

        def put_wall_texture() -> None:  # TODO DELETE / OPTIMIZE
            maze = self._level_structure.maze
            all_walls = MazeAnalyzer.extract_walls(maze)
            mapping: dict[float, Tuple[Wall, Vector2]] = {
                0: (WallNorth, Vector2(1, 0.5)),
                90: (WallEast, Vector2(0.5, 1)),
                180: (WallSouth, Vector2(1, 0.5)),
                270: (WallWest, Vector2(0.5, 1))
            }

            for wall_position, rotation in all_walls:
                wall_type, scale = mapping[rotation]

                Actors.spawn(
                    wall_type,
                    position=self._world_position(wall_position),
                    velocity=Vector2(0, 0),
                    scale=scale,
                )

        Wall.local_offset_scaling(1.0)
        put_wall_texture()

        Log.get("level").info("Level instance walls ready")

        pacman_actor = Actors.spawn(
            Player,
            position=curr_pacman_data,
            velocity=Vector2(0, 0),
            scale=Vector2(1, 1),
        )

        ghosts_actor = [
            Actors.spawn(
                ghost_class,
                position=ghost_position,
                velocity=Vector2(0, 0),
                scale=Vector2(1, 1),
            )
            for ghost_class, ghost_position in zip(
                [RedGhost, BlueGhost, YellowGhost, PinkGhost],
                curr_ghosts_data,
            )
        ]

        pacgum_actors = [
            Actors.spawn(
                Pacgum,
                position=position,
                velocity=Vector2(0, 0),
                scale=Vector2(1.5, 1.5),
            )
            for position in curr_pacgums_data
        ]

        super_pacgum_actors = [
            Actors.spawn(
                SuperPacgum,
                position=super_pacgum_position,
                velocity=Vector2(0, 0),
            )
            for position in curr_super_pacgums_data
        ]

        # ---------------- Camera ----------------

        half_cell = self.TILE_SIZE * 0.5

        camera_center = Vector2(
            maze_width * 0.5 - half_cell,
            maze_height * 0.5 - half_cell,
        )

        screen_width = Renderer.width
        screen_height = Renderer.height

        zoom = min(
            screen_width / maze_width,
            screen_height / maze_height,
        ) * 0.95

        Renderer.set_camera(camera_center)
        Renderer.set_zoom(zoom)

        # ----------------------------------------

        Renderer.bake(World)

        Log.get("level").info("Level instance actors ready")
        Log.get("level").info("Level instance start")

        try:
            log = Log.get("main")
            log.info("Booting smoke test...")
            log.info(f"World has {len(World)} actor(s).")

            last_time = time.perf_counter()
            fps_timer = 0.0
            fps_frames = 0
            fps = 0

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

                    Renderer._logger.info(
                        f"Engine smoke test | FPS: {fps} | Actors: {len(World)}"
                    )

                    fps_frames = 0
                    fps_timer -= 1000

                Assets.update()

                Input.process_events()
                Input.update()
                Input.process_actions()

                Actors.update(dt)

                if not Actors.paused:
                    Collision.update()

                Renderer.render_draw(World)
                Particles.update(dt)
                Particles.render(Renderer)
                Renderer.render_present()

            Renderer.hook_loop(frame)
            log.info("Entering mlx loop.")
            Renderer.loop()

        except Exception:
            log.error("Error level loop.")

        World.clear()
        Actors.clear()
        log.info("Level instance end")
