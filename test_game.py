"""
Smoke test for the mlx engine:
- RendererSubsystem
- AssetSubsystem
- ActorSubsystem
- World
- Sprite loading
- Actor ticking
- Rendering
"""
import os
import sys
import time

from Engine import Renderer, Assets, Actors, Log, \
                   World, Collision, Input, Vector2
from assets.code.player import Player
from game.game_instance.game_config import GameConfig
from game.game_instance.game_instance import GameInstance
from game.game_instance.player import PlayerInformation
from game.level_instance.level_instance import LevelInstance
from game.levelgen.level_options import LevelOptions


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


WIDTH, HEIGHT = 300, 200


def main():

    Renderer.init(WIDTH*1, HEIGHT*1, "Engine smoke test")
    Input.init(Renderer)

    game_config = GameConfig()
    game_instance = GameInstance(game_config)
    game_instance.page_menu()
    # simulate input start game
    game_instance._start_normal_levels()

    Input.close()
    Renderer.close()


if __name__ == "__main__":
    main()
