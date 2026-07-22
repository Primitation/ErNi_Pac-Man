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
import random
import math
import os
import sys
import time

from Engine import Renderer, Assets, Actors, Actor, Log, Vector2, World, Collision


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


WIDTH, HEIGHT = 800, 600


class Bouncer(Actor):
    """A bouncing actor that can collide with other objects and
    bounce off them using the collision system's physical resolution."""

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        scale: Vector2,
        sprite_path: str,
    ):
        super().__init__(
            position=position,
            scale=scale,
        )

        self.velocity = velocity
        self.set_sprite(sprite_path)

        # Register with collision system
        self._collider = Collision.register(
            owner=self,
            get_rect=self.get_rect,
            tag="bouncer",
            collides_with=None,
            blocking=True,
            bounce=0.8,
            static=False,
            enabled=True
        )

        # Bind collision events for debugging
        self._collider.on_begin_overlap.bind(self._on_collision_begin)
        self._collider.on_end_overlap.bind(self._on_collision_end)

    def get_rect(self):
        """Return a rect as (x, y, width, height).
        Uses sprite dimensions multiplied by scale."""
        
        sprite = self.sprite
        if sprite is not None:
            width = sprite.width * self.scale.x
            height = sprite.height * self.scale.y
        else:
            # Fallback to scale if sprite not loaded yet
            width = self.scale.x
            height = self.scale.y
        
        return (
            self.position.x,
            self.position.y,
            width,
            height
        )

    def _on_collision_begin(self, self_collider, other_collider):
        """Called when this bouncer starts overlapping with another collider."""
        pass

    def _on_collision_end(self, self_collider, other_collider):
        """Called when this bouncer stops overlapping with another collider."""
        pass

    def update(self, dt):
        """Update bouncer position and handle wall bouncing."""
        
        # Move the bouncer
        self.position += (
            self.velocity * (dt / 1000)
        )

        # Handle wall bouncing with proper clamping
        self._handle_wall_bounce()

    def _handle_wall_bounce(self):
        """Handle bouncing off screen edges with proper clamping."""
        
        # Get the actual size for boundary checking (sprite dimensions * scale)
        sprite = self.sprite
        if sprite is not None:
            width = sprite.width * self.scale.x
            height = sprite.height * self.scale.y
        else:
            width = self.scale.x
            height = self.scale.y
        
        # Check X bounds
        if self.position.x <= 0:
            self.position.x = 0
            self.velocity.x = abs(self.velocity.x)
            
        elif self.position.x + width >= WIDTH:
            self.position.x = WIDTH - width
            self.velocity.x = -abs(self.velocity.x)
            
        # Check Y bounds
        if self.position.y <= 0:
            self.position.y = 0
            self.velocity.y = abs(self.velocity.y)
            
        elif self.position.y + height >= HEIGHT:
            self.position.y = HEIGHT - height
            self.velocity.y = -abs(self.velocity.y)

    def destroy(self):
        """Clean up this bouncer."""
        Collision.unregister(self._collider)
        self.alive = False



def main():

    log = Log.get("main")

    log.info("Booting smoke test...")

    Renderer.init(
        WIDTH,
        HEIGHT,
        "Engine smoke test"
    )

    Collision.init(WIDTH, HEIGHT)

    sprite = "assets/pacman.png"

    NUM_BOUNCERS = 250

    # Load once synchronously up front so we know the actual on-screen
    # size (sprite pixels * scale) to use for spawn placement below.
    scale = Vector2(0.1, 0.1)
    texture = Assets.load(sprite)
    sprite_w = texture.width * scale.x
    sprite_h = texture.height * scale.y

    spawned_rects = []

    def rects_overlap(r1, r2):
        return not (
            r1[0] + r1[2] <= r2[0] or
            r2[0] + r2[2] <= r1[0] or
            r1[1] + r1[3] <= r2[1] or
            r2[1] + r2[3] <= r1[1]
        )

    def find_spawn_position(width, height, existing, max_attempts=30):
        """Rejection-sample a position that doesn't overlap any
        already-spawned rect, so actors don't start on top of each
        other. Falls back to the last sampled position (still
        possibly overlapping) if it can't find a free spot in time —
        better than spinning forever once the screen gets crowded."""

        for _ in range(max_attempts):
            x = random.uniform(0, WIDTH - width)
            y = random.uniform(0, HEIGHT - height)
            candidate = (x, y, width, height)

            if not any(rects_overlap(candidate, r) for r in existing):
                return x, y

        return x, y

    for _ in range(NUM_BOUNCERS):
        speed = random.uniform(80, 220)
        angle = random.uniform(0, 2 * math.pi)

        x, y = find_spawn_position(sprite_w, sprite_h, spawned_rects)
        spawned_rects.append((x, y, sprite_w, sprite_h))

        Actors.spawn(
            Bouncer,
            position=Vector2(x, y),
            velocity=Vector2(
                speed * math.cos(angle),
                speed * math.sin(angle),
            ),
            scale=scale,
            sprite_path=sprite,
        )


    log.info(
        f"World has {len(World)} actor(s)."
    )


    last_time = time.perf_counter()
    fps_timer = 0.0
    fps_frames = 0
    fps = 0

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
