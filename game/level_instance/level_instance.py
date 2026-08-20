"""Level instance."""

import time
from typing import Any, Dict, List, Optional

from Engine import (Assets, Collision, Input, Log,
                    Renderer, World, Vector2, Actors)
from Engine.ParticlesSubsystem.particlessubsystem import Particles

from assets.code.actors.ghost import (
    RedGhost,
    BlueGhost,
    YellowGhost,
    PinkGhost,
)
from assets.code.actors.pacgum import Pacgum, SuperPacgum
from assets.code.actors.cell import Cell
from assets.code.actors.player import Player

from assets.code.ui.pause_hud import PauseHUD
from assets.code.ui.gameplay_hud import GameplayHUD
from assets.code.ui.screen_transition import PacmanTransition as Transition

from game.game_instance.player_information import PlayerInformation
from game.levelgen import LevelGenerator, LevelOptions, LevelStructure


class LevelInstance:
    """A level instance."""

    TILE_SIZE = 42

    def __init__(self, level_options: LevelOptions, name: int) -> None:
        """Initialize a level instance.

        Args:
            level_options: the options for this level.
            name: level name
        """
        self._level_options = level_options
        self._level_structure: Optional[LevelStructure] = None
        self._name = name
        self.cells: List[List[Cell]] = []

    def load(self) -> None:
        """Load level structure."""
        if self._level_structure is not None:
            Log.get("level").info("Level instance already loaded")
            return

        Log.get("level").info(
            "Level instance start load structure"
        )

        self._level_structure = LevelGenerator.generate(
            self._level_options
        )

        Log.get("level").info("Level instance load ready")

    def _world_position(self, position: Vector2) -> Vector2:
        """Returns the world position for this level instance.

        Returns:
            Returns the world position for this level instance.
        """
        return Vector2(
            position.x * self.TILE_SIZE,
            position.y * self.TILE_SIZE,
        )

    def start(
        self,
        player_information: PlayerInformation,
        level_name: str,
    ) -> None:
        """Initialize and start level.

        Args:
            player_information: the level information.
            level_name: the name of the level.
        """

        self._prepare_level(
            player_information,
            level_name,
        )

        self._spawn_level()
        self._setup_camera()

        Renderer.bake(list(World))
        Actors.paused = False
        self._run_game_loop()

        World.clear()
        Actors.clear()

    def _prepare_level(
        self,
        player_information: PlayerInformation,
        level_name: str,
    ) -> None:
        """Prepare the level.

        Args:
            player_information: the level information.
            level_name: the name of the level.
        """
        if self._level_structure is None:
            self.load()

        World.clear()
        Actors.clear()

        Player.set_player_information(
            player_information
        )

        Player.current_level = level_name

        Actors.set_level_time(
            self._level_options.level_time
        )

        assert self._level_structure is not None

        width = (
            self._level_structure.width
            * self.TILE_SIZE
        )

        height = (
            self._level_structure.height
            * self.TILE_SIZE
        )

        Collision.init(width, height)

    def _spawn_level(self) -> None:
        """Spawns the actors in the level."""
        self._spawn_cells()
        self._spawn_player()
        self._spawn_ghosts()
        self._spawn_pacgums()

        Log.get("level").info(
            "Level instance actors ready"
        )

    def _spawn_cells(self) -> None:
        """Spawns the cells in the level."""
        assert self._level_structure is not None
        maze = self._level_structure.maze

        cells: List[List[Cell]] = []

        for y, row in enumerate(maze):
            cell_row: List[Cell] = []
            for x, value in enumerate(row):
                cell = Actors.spawn(
                    Cell,
                    position=self._world_position(
                        Vector2(x, y)
                    ),
                    N=not (value & 1),
                    E=not (value & 2),
                    S=not (value & 4),
                    W=not (value & 8),
                )
                cell_row.append(cell)
            cells.append(cell_row)

        self._link_cells(cells)

        self.cells = cells

        for cell_row_built in cells:
            for cell in cell_row_built:
                cell.build_geometry()

        Log.get("level").info(
            "Level instance cells ready"
        )

    def _link_cells(self, cells: List[List[Cell]]) -> None:
        """Links the cells to each others.

        Args:
            cells: the cells to link."""
        height = len(cells)
        width = len(cells[0])

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

    def _spawn_player(self) -> None:
        """Spawns the player."""
        assert self._level_structure is not None
        Actors.spawn(
            Player,
            position=self._world_position(
                self._level_structure.pacman
            ),
            velocity=Vector2(0, 0),
            scale=Vector2(1, 1),
        )

    def _spawn_ghosts(self) -> None:
        """Spawns the ghosts."""
        assert self._level_structure is not None
        ghosts = [
            RedGhost,
            BlueGhost,
            YellowGhost,
            PinkGhost,
        ]

        for ghost, position in zip(
            ghosts,
            self._level_structure.ghosts,
        ):
            Actors.spawn(
                ghost,
                position=self._world_position(position),
                velocity=Vector2(0, 0),
                scale=Vector2(1, 1),
            )

    def _spawn_pacgums(self) -> None:
        """Spawns the pacgums."""
        assert self._level_structure is not None
        for position in self._level_structure.pacgums:
            Actors.spawn(
                Pacgum,
                position=self._world_position(position),
                velocity=Vector2(0, 0),
                scale=Vector2(1, 1),
            )

        for position in self._level_structure.super_pacgums:
            Actors.spawn(
                SuperPacgum,
                position=self._world_position(position),
                velocity=Vector2(0, 0),
                scale=Vector2(1.5, 1.5),
            )

    def _setup_camera(self) -> None:
        """Setup the camera."""
        assert self._level_structure is not None
        width = (
            self._level_structure.width
            * self.TILE_SIZE
        )

        height = (
            self._level_structure.height
            * self.TILE_SIZE
        )

        half_cell = self.TILE_SIZE * 0.5

        Renderer.set_camera(
            Vector2(
                width * 0.5 - half_cell,
                height * 0.5 - half_cell,
            )
        )

        zoom = min(
            (Renderer.width - 100) / width,
            (Renderer.height - 100) / height,
        ) * 0.95

        Renderer.set_zoom(zoom)

    def _run_game_loop(self) -> None:
        """Run main game loop."""

        log = Log.get("main")

        hud = GameplayHUD(self._name)
        pause_hud = PauseHUD()

        state = {
            "fade_in": Transition(650),
            "fade_out": None,
            "last_time": time.perf_counter(),
        }

        self._register_callbacks(log)

        try:
            Renderer.hook_loop(
                lambda param: self._frame(
                    param,
                    hud,
                    pause_hud,
                    state,
                )
            )

            log.info("Entering mlx loop.")
            Renderer.loop()

        except Exception:
            log.exception(
                "Error level loop."
            )

        finally:
            self._remove_callbacks()

        log.info(
            "Level instance end"
        )

    def _register_callbacks(self, log: Any) -> None:
        """Register input callbacks."""

        def on_pause() -> None:
            paused = Actors.toggle_pause()
            log.info(
                f"Game {'paused' if paused else 'resumed'}."
            )

        def on_quit_to_menu() -> None:
            if Actors.paused:
                Player.quit = True

        self._pause_callback = on_pause
        self._quit_callback = on_quit_to_menu

        Input.register_action_callback(
            "pause",
            on_pause,
        )

        Input.register_action_callback(
            "quit to menu",
            on_quit_to_menu,
        )

    def _remove_callbacks(self) -> None:
        """Remove input callbacks."""

        Input.remove_action_callback(
            "pause",
            self._pause_callback,
        )

        Input.remove_action_callback(
            "quit to menu",
            self._quit_callback,
        )

    def _frame(
        self,
        _param: Any,
        hud: GameplayHUD,
        pause_hud: PauseHUD,
        state: Dict[str, Any],
    ) -> None:
        """Process one frame.

        Args:
            _param: parameters (ignored)
            hud: gameplay hud.
            pause_hud: pause hud.
            state: state in the level.
        """

        self._update_transition(state)

        now = time.perf_counter()

        dt = (
            now - state["last_time"]
        ) * 1000

        state["last_time"] = now

        Assets.update()

        Input.process_events()

        if state["fade_out"] is None:
            self._update_game(dt)

        self._render(
            hud,
            pause_hud,
            state,
        )

        Input.update()

    def _update_transition(self, state: Dict[str, Any]) -> None:
        """Update fade transitions.

        Args:
            state: state in the level.
        """

        if (
            Player.game_ended()
            and state["fade_out"] is None
        ):
            state["fade_out"] = Transition(650)

    def _update_game(self, dt: float) -> None:
        """Update gameplay.

        Args:
            dt: difference time from the previous update.
        """

        Input.process_actions()

        Actors.update(dt)

        if not Actors.paused:
            Collision.update()
            Particles.update(dt)

    def _render(
        self,
        hud: GameplayHUD,
        pause_hud: PauseHUD,
        state: Dict[str, Any],
    ) -> None:
        """Render current frame.

        Args:
            hud: gameplay hud.
            pause_hud: pause hud.
            state: state in the level.
        """

        Renderer.render_draw(list(World))

        Particles.render(Renderer)

        hud.render(Renderer)

        if Actors.paused:
            pause_hud.render(Renderer)

        self._render_fade(state)

        Renderer.render_present()

    def _render_fade(self, state: Dict[str, Any]) -> None:
        """Render fade effects.

        Args:
            state: state in the level.
        """

        fade_in = state["fade_in"]
        fade_out = state["fade_out"]

        if fade_in:
            fade_in.draw_fade_in(Renderer)

            if fade_in.done:
                state["fade_in"] = None

        if fade_out:
            fade_out.draw_fade_out(Renderer)

            if fade_out.done:
                Renderer.close_request()
