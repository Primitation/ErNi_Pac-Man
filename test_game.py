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

from Engine import Renderer, Input, Log
from game.game_instance.game_config import GameConfig, GameConfigParser
from game.game_instance.game_instance import GameInstance
from game.game_instance.score import Scores


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


WIDTH, HEIGHT = 800, 600


def main():
    Renderer.init(WIDTH*1, HEIGHT*1, "Engine smoke test")
    Input.init(Renderer)

    game_config = GameConfigParser.parse("config.json")
    game_instance = GameInstance(game_config)
    game_instance.page_menu()
    # simulate input start game
    game_instance._start_normal_levels()

    Input.close()
    Renderer.close()
    Log.close()


def main_parser():
    game_config: GameConfig = GameConfigParser.parse("config.json")
    print(game_config)
    from time import sleep
    # TODO: wait others threads before quitting
    sleep(2)


def main_scores():
    game_config: GameConfig = GameConfigParser.parse("config.json")
    scores = Scores.load_scores(game_config)
    print(scores.get_top_scores())
    scores.add_score("AB", 42)
    print(scores.get_top_scores())
    scores.save_scores(game_config)


if __name__ == "__main__":
    # main_parser()
    main()
    # main_scores()
