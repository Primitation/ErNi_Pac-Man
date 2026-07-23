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
                   World, Collision, Input


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


WIDTH, HEIGHT = 1600, 900


def main():

    log = Log.get("main")
    log.info("Booting smoke test...")

    Renderer.init(WIDTH, HEIGHT, "Engine smoke test")
    Collision.init(WIDTH, HEIGHT)

    print("[DEBUG] Initializing Input...")
    Input.init(Renderer)

    Input.enable_key_debug(True)

    # Method 2: Add a simple test callback
    def test_key_callback(keycode, state):
        key_name = Input.get_key_name(keycode)
        print(f"[TEST] Key event: {key_name} (code: {keycode}) - {state.name}")

    Input.on_any_key(test_key_callback)

    # Method 3: Print every frame what keys are held
    # This will show if any keys are being detected at all

    # Register a callback for movement actions
    def on_move_up():
        log.info("Moving UP!")

    Input.register_action_callback("up", on_move_up)

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

        Input.update()
        Input.process_actions()
        Assets.update()
        Actors.update(dt)
        Collision.update()
        Renderer.render(World)

    Renderer.hook_loop(frame)

    log.info("Entering mlx loop.")

    Renderer.loop()

    log.info("Window closed.")

    Renderer.close()


if __name__ == "__main__":
    main()
