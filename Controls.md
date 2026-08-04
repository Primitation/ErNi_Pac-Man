# Pac-Man — How to Play

## Launching
- **From the itch.io app:** click "Play" (uses `run.sh` automatically via `itch.toml`).
- **Manually:** `make run` from the project root, or after packaging:
  ```
  cd pacman-42-linux
  ./run.sh
  ```
- **Requirements:** a Linux desktop with X11 (this build uses MiniLibX, which is
  X11-based and does not run under Wayland-only sessions or on Windows/macOS).

## Rules
- **Win** — eat all pacgums.
- **Lose** — no more lives, or time reaches 0.
- **Lose a life** — a non-edible ghost touches Pac-Man.
- **Edible ghosts** — ghosts become edible for a short duration after eating a super-pacgum.
- **Score** — earned by eating pacgums, super-pacgums, and edible ghosts.

## Controls

### Movement & menus
| Key                          | Action                |
|-------------------------------|------------------------|
| `W` / `A` / `S` / `D`         | Move up/left/down/right |
| Arrow keys                    | Move (alternative to WASD) |
| `Enter` / `Space`             | Confirm (menus)        |
| `Escape`                      | Cancel / quit           |
| `P`                           | Pause                  |
| `M`                           | Quit to menu             |

### Cheats (development/testing)
| Key | Action              |
|-----|---------------------|
| `E` | Extra life          |
| `I` | Invincibility        |
| `U` | Speed up             |
| `Y` | Speed down           |
| `G` | Freeze ghosts        |
| `L` | Win level            |
| `T` | Stop time            |

## Configuration
- `config.json` (next to `pacman.py`) controls lives, pacgum count, level
  time limit, scoring, and the size of each generated level. See the
  Configuration section of the main [README](README.md) for the full
  reference.

## Known limitations
- Linux-only build (MiniLibX has no Windows/macOS port).
- Requires an X11-capable display server.
