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


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


WIDTH, HEIGHT = 1600, 900


def main():

    log = Log.get("main")
    log.info("Booting smoke test...")

    Renderer.init(WIDTH, HEIGHT, "Engine smoke test")
    Collision.init(WIDTH, HEIGHT)

    print("[DEBUG] Initializing Input...")
    Input.init(Renderer)

    Actors.spawn(
        Player,
        position=Vector2(0, 0),      # overwritten by find_spawn_position() if get_rect() works
        velocity=Vector2(0, 0),
        scale=Vector2(0.25, 0.25),
        sprite_path="assets/texture/pacman.png",
    )

    def on_pause():
        paused = Actors.toggle_pause()
        log.info(f"Game {'paused' if paused else 'resumed'}.")

    Input.register_action_callback("pause", on_pause)

    log.info(
        f"World has {len(World)} actor(s)."
    )

    last_time = time.perf_counter()
    fps_timer = 0.0
    fps_frames = 0
    fps = 0
    Renderer.bake(World)

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

            # Update once per second
            Renderer._logger.info(
                f"Engine smoke test | FPS: {fps} | Actors: {len(World)}"
            )

            fps_frames = 0
            fps_timer -= 1000

        Assets.update()

        Input.process_actions()
        Input.update()

        Actors.update(dt)
        if not Actors.paused:
            Collision.update()
        Renderer.render(World)

    Renderer.hook_loop(frame)

    log.info("Entering mlx loop.")

    Renderer.loop()

    log.info("Window closed.")

    Input.close()
    Renderer.close()


if __name__ == "__main__":
    main()
