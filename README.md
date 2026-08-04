*This activity has been created as part of the 42 curriculum by nbreton, erxia.*

```
██████╗  █████╗  ██████╗       ███╗   ███╗ █████╗ ███╗   ██╗
██╔══██╗██╔══██╗██╔════╝       ████╗ ████║██╔══██╗████╗  ██║
██████╔╝███████║██║      █████╗██╔████╔██║███████║██╔██╗ ██║
██╔═══╝ ██╔══██║██║      ╚════╝██║╚██╔╝██║██╔══██║██║╚██╗██║
██║     ██║  ██║╚██████╗       ██║ ╚═╝ ██║██║  ██║██║ ╚████║
╚═╝     ╚═╝  ╚═╝ ╚═════╝       ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

This document is for anyone who wants to understand, build, or run the
Pac-Man project — a Pac-Man clone whose mazes are procedurally generated
by the `mazegenerator` package (the assigned *A-Maze-ing* project), rendered
through a small custom 2D engine built on MiniLibX. For the full engine
reference, see [`Engine/README.md`](Engine/README.md); this file is the
entry point for everything else.

## Description

Pac-Man is a from-scratch recreation of the classic arcade game, built for
the 42 curriculum. Its two defining constraints are that the maze isn't
hand-authored — it's generated at runtime by our own `mazegenerator`
package — and that all rendering, input, collision, and game-object logic
run on top of a homemade Actor/Component engine (`PacEngine`, in
[`Engine/`](Engine)), rather than an off-the-shelf game framework.

The goal was to practice: integrating a previously-built package
(`mazegenerator`) into a new, larger project; designing a small but real
engine architecture (subsystems, actors, components) on top of a low-level
pixel library (MiniLibX); and implementing classic arcade-game systems —
grid movement, ghost AI, collision, scoring, lives, levels, and highscores
— on top of that engine.

## Instructions

### Prerequisites

- Python 3.10+ and `python3-venv`.
- `make` and a C compiler/`git` (for building MiniLibX from source).
- A Linux (or WSL) environment with X11 — MiniLibX targets Linux/X11.

### Setup and build

```sh
make            # equivalent to `make install`: creates the venv,
                # installs the project + MiniLibX, and builds everything
make install    # same as above, explicit target
```

Under the hood, `make install`:

1. Creates a Python virtual environment in `.venv` (using `--copies`, so
   it stays relocatable) if it doesn't already exist.
2. Installs the project in editable mode (`pip install -e .`), pulling in
   `numpy` and `pydantic`.
3. Installs `flake8`, `mypy`, and `build` for linting/packaging.
4. Clones and builds `minilibx-linux` (the 42 MiniLibX fork,
   `42school/mlx_CLXV`) if it isn't already present, then installs the
   built `mlx` wheel into the venv.
5. Installs the `mazegenerator` wheel from `libs/` into the venv.

### Running

```sh
make run        # runs `pacman.py` inside the venv
make debug      # same, but under `python3 -m pdb`
```

Once the window opens, use the keys below (also listed in
[`Controls.md`](Controls.md)):

| Key                | Action                     |
|--------------------|----------------------------|
| `W`/`A`/`S`/`D` or Arrow Keys | Move Pac-Man    |
| `P`                | Pause                      |
| `M`                | Quit to menu                |
| `Enter` / `Space`  | Confirm (menus)            |
| `Escape`           | Cancel / quit               |

Cheat keys used for development/testing (invincibility, extra life,
speed up/down, freeze ghosts, win level, stop time) are also listed in
[`Controls.md`](Controls.md).

### Housekeeping

```sh
make lint       # flake8 + mypy over the project
make clean      # removes caches, build artifacts
make fclean     # clean + removes the venv, MiniLibX, and built packages
make re         # fclean, then install from scratch
```

## Configuration file

The game is driven by `config.json` at the project root:

```json
{
    "highscore_filename": "save_scores.json",
    "lives": 4,
    "pacgum": "100",
    "level_max_time": "90",
    "points_per_pacgum": "5",
    "points_per_super_pacgum": "10",
    "points_per_ghost": "200",
    "seed": "42",
    "level": [
        { "width": "20", "height": "20" }
    ]
}
```

| Key                       | Type            | Meaning                                                                 |
|----------------------------|-----------------|--------------------------------------------------------------------------|
| `highscore_filename`       | path            | File the highscore table is saved to and loaded from. Default: `save_scores.json`. |
| `lives`                    | int             | Starting lives for the player. Must be > 0.                              |
| `pacgum`                   | int             | Maximum number of pacgums placed per level.                              |
| `level_max_time`           | int (seconds)   | Time limit for a level before it's lost. Minimum 30.                     |
| `points_per_pacgum`        | int             | Points awarded per pacgum eaten.                                         |
| `points_per_super_pacgum`  | int             | Points awarded per super-pacgum eaten.                                   |
| `points_per_ghost`         | int             | Points awarded per (edible) ghost eaten.                                 |
| `seed`                     | int             | Seed for the first level's maze, for reproducible runs.                  |
| `level`                    | list of objects | One `{width, height}` entry per level; each maze is generated at that size (minimum 5x5). |

Every field is validated on load (via a `pydantic` model): invalid or
missing values fall back to safe defaults and are logged as errors rather
than crashing the game, so a malformed `config.json` degrades gracefully
instead of preventing launch.

## Highscore

Highscores are handled by `Score` (the live, in-run point counter — points
per pacgum/super-pacgum/ghost eaten, as configured) and `Scores` (the
persisted leaderboard).

`Scores` stores a simple list of `(name, score)` pairs and is loaded from
and saved to the JSON file named by `highscore_filename` in the config.
On save, the list is sorted descending by score and truncated to the top
10 entries (`MAX_SAVE_SCORES`) before being written — so the file only
ever holds a fixed-size leaderboard rather than growing unbounded across
every run.

We chose a flat JSON file over anything heavier (SQLite, a server, etc.)
because the requirement is a small, local, single-player leaderboard: a
list of ten `(name, score)` pairs needs no query language or migrations,
and a plain JSON file keeps it trivially inspectable, portable across
machines, and dependency-free — consistent with the project's config file
also being plain JSON.

## Maze Generation

Each level's maze is produced by the assigned `mazegenerator` package
(the *A-Maze-ing* project), used here as a pure, decoupled dependency —
`Pac-Man` never touches its internals, only its public `MazeGenerator`
class:

```python
from mazegenerator import MazeGenerator

maze_generated = MazeGenerator(
    size=(width, height),
    perfect=False,
    entry_cell=start,
    exit_cell=end,
    seed=seed,
)
maze = maze_generated.maze  # 2D array of wall bitmasks
```

This happens in `LevelGenerator.generate()`
([`game/levelgen/level_gen.py`](game/levelgen/level_gen.py)), which:

1. Calls `MazeGenerator` with the level's configured width/height and a
   seed (fixed for level 1, from `config.json`; random-ish thereafter),
   with `perfect=False` so the maze includes a few loops rather than
   being a strict spanning tree — closer to a real Pac-Man maze than a
   perfect one.
2. Reads back `maze`, a 2D grid of wall bitmasks (`W S E N` packed into
   one hex digit per cell), and hands it to `MazeAnalyzer` to extract the
   open (non-fully-walled) cells.
3. Places Pac-Man at the center, one ghost and one super-pacgum at each
   of the four corners, and scatters regular pacgums across a random
   sample of the remaining open cells (up to `pacgum` from the config).
4. Packages all of this into a `LevelStructure`, which is what the
   rendering/actor side of the game actually consumes.

The generator's own maze-drawing rules (perfect vs. imperfect mazes,
loop punching, dead-end reduction, the hidden "42" pattern) are entirely
its own concern — see its own documentation for the algorithm details;
from `Pac-Man`'s side it is only ever used as an imported library
(`libs/mazegenerator-2.1.0-py3-none-any.whl`, installed like any other
dependency), which is exactly the "reusable, decoupled package" contract
it was built to satisfy.

## Implementation

- **Language/runtime:** Python 3.10+, typed throughout (`mypy --strict`-ish
  settings in `pyproject.toml`) and linted with `flake8`.
- **Rendering:** MiniLibX (`mlx_CLXV`, the 42 fork) for the window and
  pixel buffer, with `numpy` used for fast buffer manipulation in the
  engine's renderer.
- **Config/validation:** `pydantic` models validate `config.json` on load,
  falling back to sane defaults on any invalid field instead of crashing.
- **Grid-based gameplay:** Pac-Man, ghosts, and pacgums live on the maze's
  cell grid; movement, collision, and AI all reason in grid coordinates,
  translated to pixel positions only at render time.
- **Ghost AI:** each ghost uses one of several chase-behavior components
  (`ChasePlayerGridComponent`, `ChaseTargetGridComponent`,
  `PinkyChaseComponent`, `InkyChaseComponent`, `ClydeChaseComponent`),
  echoing the four original ghosts' distinct targeting personalities
  (direct chase, ambush-ahead, pincer, and flee/chase-toggle behavior)
  rather than having every ghost chase identically.
- **Levels:** `GameModeNormalLevels` pre-generates a fixed sequence of
  `LevelInstance`s from the config's `level` list, then plays through them
  in order via `GameInstance`, tracking lives/score across the whole run
  through a persistent `PlayerInformation`.
- **Cheats:** a `CheatComponent` exposes debug-only actions (invincibility,
  extra life, speed up/down, freeze ghosts, win level, stop time) behind
  dedicated key bindings, useful for testing specific game states without
  having to play through them.

## General Software Architecture

The codebase is split into three layers:

```
Engine/        PacEngine — a small, reusable 2D Actor/Component engine
                (not specific to Pac-Man at all; see Engine/README.md)
game/          Pac-Man-specific game logic and state (not rendering)
assets/code/   Pac-Man-specific actors, components, and UI screens
                (built on top of Engine's Actor/Component classes)
```

**`Engine/`** provides one global subsystem per concern — `Renderer`,
`Assets`, `Actors`, `Collision`, `Input`, `Particles`, `Log` — each a
singleton, plus the `AActor`/`Component` base classes that everything in
`assets/code/actors` and `assets/code/components` builds on. The main loop
(process input → update actors → resolve collisions → render → update
particles) lives here and is entirely game-agnostic; see
[`Engine/README.md`](Engine/README.md) and its `docs/` pages for the full
reference.

**`game/`** holds the Pac-Man-specific state machine and data, independent
of rendering:
- `game_instance/` — `GameInstance` (menu ↔ play ↔ scores flow),
  `GameConfig`/`GameConfigParser` (validated config loading),
  `GameModeNormalLevels` (the level sequence), `PlayerInformation` and
  `Score`/`Scores` (lives, points, the highscore table).
- `levelgen/` — `LevelGenerator`, `LevelOptions`, `LevelStructure`,
  `MazeAnalyzer`, `MazeParser`: turns a `mazegenerator` maze plus level
  options into the concrete layout (walls, pacman, ghosts, pacgums) a
  level starts with.
- `level_instance/` — `LevelInstance`: owns one level's lifecycle (load →
  start → play → win/lose), spawning the actual `Engine` actors for that
  level's layout.

**`assets/code/`** is the Pac-Man-specific content built on `Engine`'s
Actor/Component classes:
- `actors/` — `Player`, `BasicGhost`, `Pacgum`/`SuperPacgum`, `Wall`,
  `Cell`, plus shared `Actor`/`Entity` base classes.
- `components/` — grid movement (`GridMovementComponent` and its
  chase-behavior subclasses), collision-driven wall rendering
  (`wall_components.py`), the debug `CheatComponent`, particle effects.
- `ui/` — the main menu, pause/end screens, and the in-game HUD, all
  built on `Engine`'s `UISubsystem`.

The dependency direction is strictly one-way: `assets/code` depends on
`game` and `Engine`, `game` depends on `Engine` (and on the external
`mazegenerator` package), and `Engine` depends on nothing Pac-Man-specific
— which is what lets `Engine` ship with its own standalone documentation
and, in principle, back a different game entirely.

## Project Management

- [Notion](https://midnight-juniper-97d.notion.site/Pac-Man-40379e40a3a682e19463018f9709c540)

## Resources

- [MiniLibX prototypes reference (42 docs)](https://harm-smits.github.io/42docs/libs/minilibx/prototypes.html)
- [`mlx_CLXV` Python bindings source](https://github.com/42school/mlx_CLXV)
- [Pac-Man ghost AI — Pinky, Inky, Blinky, Clyde targeting logic (The Pac-Man Dossier)](https://www.gamedeveloper.com/design/the-pac-man-dossier)
- `pydantic` documentation (config validation)
- Classic references on Actor/Component game architecture (any
  introductory game-engine-design material covering the pattern, as used
  by engines like Unity/Unreal)

**AI usage.** AI assistance (Claude) was used for three specific:
Drafting the packaging script
Fast iteration of engine structure
Help in lint of project