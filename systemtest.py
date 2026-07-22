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

    for _ in range(NUM_BOUNCERS):
        speed = random.uniform(80, 220)
        angle = random.uniform(0, 2 * 3.141592653589793)

        Actors.spawn(
            Bouncer,
            position=Vector2(
                random.uniform(0, WIDTH - 64),
                random.uniform(0, HEIGHT - 64),
            ),
            velocity=Vector2(
                speed * __import__("math").cos(angle),
                speed * __import__("math").sin(angle),
            ),
            scale=Vector2(0.1, 0.1),
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
