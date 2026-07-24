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
from game.level_instance.level_instance import LevelInstance
from game.levelgen.level_options import LevelOptions


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


WIDTH, HEIGHT = 300, 200


def main():

    Renderer.init(WIDTH*1, HEIGHT*1, "Engine smoke test")
    Input.init(Renderer)

    pacgums = 5
    seed = 42
    level_options = LevelOptions(WIDTH, HEIGHT, pacgums, seed)
    level_instance = LevelInstance(level_options)
    level_instance.load()
    level_instance.start()

    pacgums = 15
    seed = 53
    level_options = LevelOptions(200, 100, pacgums, seed)
    level_instance = LevelInstance(level_options)
    level_instance.load()
    level_instance.start()

    Input.close()
    Renderer.close()


if __name__ == "__main__":
    main()
