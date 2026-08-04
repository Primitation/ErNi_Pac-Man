*This activity has been created as part of the 42 curriculum by nbreton, erxia.*


```
██████╗  █████╗  ██████╗      ███╗   ███╗ █████╗ ███╗   ██╗
██╔══██╗██╔══██╗██╔════╝      ████╗ ████║██╔══██╗████╗  ██║
██████╔╝███████║██║     █████╗██╔████╔██║███████║██╔██╗ ██║
██╔═══╝ ██╔══██║██║     ╚════╝██║╚██╔╝██║██╔══██║██║╚██╗██║
██║     ██║  ██║╚██████╗      ██║ ╚═╝ ██║██║  ██║██║ ╚████║
╚═╝     ╚═╝  ╚═╝ ╚═════╝      ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
```


## Description

- **`pacman`** — a pacman game using MiniLibX-based (`mlx`) visualizer that
  uses a configuration file for the higscore saving filename, lives per game,
  pacgums for the levels, time limit for the levels, points per eating,
  seed for the first maze, levels with each the width and height.

The goal of the project is to practice game like design, project management,
file-format design, and low-level pixel rendering with MiniLibX,
while making a game.

## Instructions

### Prerequisites

- Python 3.10+ and `python3-venv`.
- `make` and a C compiler/`git` (for building MiniLibX from source).
- A Linux (or WSL) environment — MiniLibX targets Linux/X11.

### Setup and build

```sh
make            # equivalent to `make install`: creates the venv,
                # installs mazegen + MiniLibX, and builds everything
make install    # same as above, explicit target
make build      # (re)build the package for game release
```

### Running

```sh
make run        # runs `pacman.py config.json` inside the venv
make debug       # same, but under `python3 -m pdb`
python3 pacman.py <config.json>
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

Select instructions in the menu for more gameplay information.

### Housekeeping

```sh
make lint       # flake8 + mypy over the project
make clean      # removes caches, build artifacts, and the generated maze.txt
make fclean     # clean + removes the venv, MiniLibX, and built packages
make re         # fclean, then install from scratch
```

## Configuration

`pacman` configuration use json text file (default: `config.json`).
Lines starting with `#` are treated as comments and ignored.

```
# Default
highscore_filename=save_scores.json
lives=3
pacgum=42
level_max_time=90
points_per_pacgum=10
points_per_super_pacgum=50
points_per_ghost=200
seed=42
level=10 length
width=15
height=15
```

| Key                       | Type        | Meaning                                                           |
|---------------------------|-------------|-------------------------------------------------------------------|
| `highscore_filename`      | string      | File for the scores storage the maze.                             |
| `lives`                   | int         | Starting lives for the pacman.                                    |
| `pacgum`                  | int         | Number of pacgums in a level.                                     |
| `level_max_time`          | int         | Time limit in seconds for every levels                            |
| `points_per_pacgum`       | int         | Points per pacgum eaten.                                          |
| `points_per_super_pacgum` | int         | Points per super-pacgum eaten.                                    |
| `points_per_ghost`        | int         | Points per ghost eaten.                                           |
| `seed`                    | int         | Seed for the first maze generation.                               |
| `level`                   | list[dict[width | height, int]] | List of width and height dict for each level. |
| `width`                   | int         | Width for the current level.                                      |
| `height`                  | int         | Height for the current level.                                     |

## Highscore

`pacman` highscore use json text file (default: `save_scores.json`).
It is saved as a list of list of size two with the name and the score.
The highscore uses the json module to read and write in the file.
Using json to save the score is easier implementing.


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

The game was implemented in python.

The game's core logic is straightforward, consisting of the game, levels, and generation.

The engine and assets controls the UI and the game logic (collisions, images, movements, etc).
The engine is composed of multiple subsystem. Each subsystem controls a specific system (actor, collision, world, etc).

The ghosts use different algorithms, such as chasing the player, trying to get in the player's path, unpredictably chasing the player, and staying close to the player.

Data validation with the Pydantic module. JSON reading with the JSON module.
UI rendering and control with MiniLibX.

### Technical Summary

- language: python
- architecture: game - engine - assets
- data validation: Pydantic module
- JSON: JSON module
- UI: MinilibX module and numpy module for optimization

## General Software Architecture

### Game

The game core logic.

- Game instance - The main game core logic. Controls the menu, scores, and player,
  and uses the configuration to generate and start the game mode. Uses the engine and assets.
- Game config - Reads the configuration file and validates the data,
  applying default and limit values.
- Scores - Reads from and writes to the high score file and controls the current scores.
- Player information and Score - Stores and controls the player's
  lives and score as described in the configuration.
- Game mode - Controls multiple levels as described in the configuration and generates
  them using the level generator.
- Level instance - The main level core logic. Uses the level structure,
  the engine, and assets to control the frame and updates.
- Level gen - The level generator. Generates the maze information using the maze generator
  package, along with the positions of Pac-Man, ghosts, pac-gums, and super pac-gums.
  Uses the level options for generation and returns a level structure containing the generated information.
- Level options - Stores the level options, such as the width and height, the seed, the
  number of pac-gums, and the time limit.
- Level structure - Stores the level information, including the maze, Pac-Man, ghosts,
  pac-gums, and super pac-gums positions.

### Engine and assets

The game control and UI logic. Render each frame with update calls between each frame.

- Renderer - The main renderer using the MiniLibX module. Renders each frame,
  including the level and other UI elements.
- World - Contains the actors in the level.
- Actors - Controls the actors in the level. Can spawn actors, update them,
  pause and resume them, and control the level timer.
- Actor - Controls an actor with its position, rotation, pivot, whether it is static
  (no specific interaction), and updates. Uses and stores specific components for actions or information related to the actor.
  Uses and stores specific components for actions or information for the specific actor.
    1. player actor - The player actor with grid movement, player grid input, collider, animated sprite, facing direction, and cheat components. Stores the level and game state information, such as the end of the level when the player wins and the end of the game when the player loses or quits.
    1. ghost actor - Ghost actors (Blinky, Pinky, Inky, Clyde) with collider, animated sprite, chase behavior, grid movement, and cheat components.
    1. pacgum actor - A pac-gum in the world with collider and sprite components.
    1. super-pacgum actor - A super pac-gum in the world with collider and sprite components.
    1. cell actor - A static actor representing a cell image with walls based on the maze layout, using wall components.
- Components - Controls a specific action or information linked to an actor.
  A component update is mandatory.
    1. sprite component - Controls a static image with its information for an actor.
    1. animated sprite component - Controls an animated sprite with its information. Updates the animation for an actor.
    1. collider component - Stores collision information for the collision resolver of an actor.
    1. movement components - A set of components for movement:
        1. movement component - Controls the movement of an actor.
        1. grid movement component - Restricts movement to a grid.
        1. player grid input component - Controls player input for grid movement direction only.
        1. chase target grid components - Controls ghost chase logic,
           with basic player chase behaviors:
            1. chase player grid component - Blinky chase behavior, directly chasing the player.
            1. pinky chase component - Pinky chase behavior, chasing ahead of the player.
            1. inky chase component - Inky chase behavior, unpredictably chasing the player.
            1. clyde chase component - Clyde chase behavior, chasing when far from the player and fleeing when close to the player.
            1. scatter ghost component - Moves toward corners.
        1. face direction component - Controls the image rotation based on the movement direction of an actor.
    1. particle component - Controls specific particles for an actor.
    1. wall components - Specific components for wall textures.
    1. cheat component - Controls cheats for the player and ghosts.
- Collision - Resolves collisions. Stores and updates collision data, resolves positions after
  collisions, and uses signals to notify when a collision occurs.
- Assets - Controls the assets, mainly images. Handles loading and caching for
  asset optimization.
- Input - Controls player input. Maps keyboard input to actions and can check
  whether an action is active or register callbacks that map actions to functions.
- Particles - Controls the particle effects in the level. Stores,
  updates, and renders particles using the renderer.
- UI - Provides an easier way to create other UI elements
  (menu, high score, instructions, options, player name)
  and renders them using the renderer.
- Log - Controls the logs and prints.

## Project Management

The project was managed using Notion, which was used as a central platform to organize and track the development process. A dedicated Notion workspace was created to store project information, including tasks and progress tracking.

link:
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
