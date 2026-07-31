"""Level instance"""

import time
from typing import Tuple
from Engine import (Assets, Collision, Input, Log, Renderer, World,
                    Vector2, Actors)
from Engine.ParticlesSubsystem.particlessubsystem import Particles
from assets.code.actors.ghost import (
    RedGhost, BlueGhost, YellowGhost, PinkGhost)
from assets.code.actors.pacgum import Pacgum, SuperPacgum
from assets.code.actors.cell import Cell
from game.game_instance.player_information import PlayerInformation
from game.levelgen import LevelGenerator, LevelOptions
from assets.code.actors.player import Player
from assets.code.ui.gameplay_hud import GameplayHUD
from game.levelgen.maze_analyzer import MazeAnalyzer


class LevelInstance:
    """A level instance.

    Can start the level.
    """
    TILE_SIZE = 42

    def __init__(self, level_options: LevelOptions) -> None:
        """Initializes a level instance.

        Args:
            level_options: options for the current level.
        """
        self._level_options = level_options
        self._level_structure = None
        self._name = None

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

    def start(self, player_information: PlayerInformation, level_name: str) -> None:
        """Initialize and start the level."""

        if self._level_structure is None:
            self.load()

        World.clear()
        Actors.clear()
        """
        Renderer._debug_draw_colliders = True

        # Custom color map for different collider tags
        color_map = {
            "player": 0xFF00FF00,  # Bright green
            "wall": 0xFFFF0000,    # Bright red
            "enemy": 0xFFFF00FF,   # Magenta
        }
        Renderer._debug_collider_color_map = color_map
        """

        Player.set_player_information(player_information)
        Player.current_level = level_name
        Actors.set_level_time(self._level_options.level_time)

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

        def put_cell() -> None:
            maze = self._level_structure.maze

            height = len(maze)
            width = len(maze[0])

            cells = [[None for _ in range(width)] for _ in range(height)]

            # First pass: create every cell
            for y in range(height):
                for x in range(width):
                    value = maze[y][x]

                    cell = Actors.spawn(
                        Cell,
                        position=self._world_position(Vector2(x, y)),
                        N=not (value & 1),
                        E=not (value & 2),
                        S=not (value & 4),
                        W=not (value & 8),
                    )

                    cells[y][x] = cell

            # Second pass: assign neighbors
            for y in range(height):
                for x in range(width):
                    cell = cells[y][x]

                    if y > 0:
                        cell.north = cells[y - 1][x]

                    if y < height - 1:
                        cell.south = cells[y + 1][x]

                    if x > 0:
                        cell.west = cells[y][x - 1]

                    if x < width - 1:
                        cell.east = cells[y][x + 1]

            self.cells = cells
            for row in self.cells:
                for cell in row:
                    cell.build_geometry()

            Log.get("level").info("Level instance cells ready")
        put_cell()

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
                scale=Vector2(1, 1),
            )
            for position in curr_pacgums_data
        ]

        super_pacgum_actors = [
            Actors.spawn(
                SuperPacgum,
                position=position,
                velocity=Vector2(0, 0),
                scale=Vector2(1.5, 1.5),
            )
            for position in curr_super_pacgums_data
        ]

        # ---------------- Camera ----------------

        half_cell = self.TILE_SIZE * 0.5

        camera_center = Vector2(
            maze_width * 0.5 - half_cell,
            maze_height * 0.5 - half_cell,
        )

        screen_width = Renderer.width - 100
        screen_height = Renderer.height - 100

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

            hud = GameplayHUD()

            last_time = time.perf_counter()
            fps_timer = 0.0
            fps_frames = 0
            fps = 0

            def frame(_param):

                nonlocal last_time
                nonlocal fps_timer
                nonlocal fps_frames
                nonlocal fps

                if Player.game_ended():
                    Renderer.close_request()

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
                Input.process_actions()

                Actors.update(dt)

                if not Actors.paused:
                    Collision.update()

                Renderer.render_draw(World)
                Particles.update(dt)
                if Renderer._debug_draw_colliders:
                    Collision.draw_debug(Renderer, Renderer._debug_collider_color_map)
                Particles.render(Renderer)
                hud.render(Renderer)
                Renderer.render_present()
                Input.update()

            Renderer.hook_loop(frame)
            log.info("Entering mlx loop.")
            Renderer.loop()

        except Exception:
            log.error("Error level loop.")

        World.clear()
        Actors.clear()
        log.info("Level instance end")
