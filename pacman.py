"""
Pacman Game Python Launcher
"""
import os
import sys

from Engine import Renderer, Input, Log
from game.game_instance.game_config import GameConfigParser
from game.game_instance.game_instance import GameInstance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


WIDTH, HEIGHT = 1600, 900


def main() -> None:
    """The main."""
    Renderer.init(WIDTH, HEIGHT, "Pacman - MLX")
    Input.init()

    game_config = GameConfigParser.parse(sys.argv[1])
    game_instance = GameInstance(game_config)
    game_instance.page_menu()
    Input.close()
    Renderer.close()
    Log.close()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        try:
            main()
        except Exception:
            pass
    else:
        print("Correct usage: python3 pacman.py <config.json>")
