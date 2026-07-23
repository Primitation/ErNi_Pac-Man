from .component import Component
from ... import Assets, SpriteSheetKey, Animation


class AnimatedSpriteComponent(Component):
    """Sprite-sheet animation — walking, spawning, dying, whatever.

    Frames are sliced once per unique (path, frame_width,
    frame_height, frame_count, columns, start_frame) combo and
    shared across every actor using the same sheet + slicing, same
    caching model as SpriteComponent.

    start_frame lets several animations (e.g. walk vs. death) or
    several characters (e.g. each ghost color) share one sheet —
    it's the row-major index of the first frame to slice, so a death
    animation starting right after 4 walk frames would use
    start_frame=4.

    loop=False plays through once and holds on the last frame — use
    on_complete for a one-shot spawn/death animation to fire a
    callback (e.g. switch to a walk animation, or actor.destroy())
    the moment it finishes.
    """

    def __init__(
        self,
        path: str,
        frame_width: int,
        frame_height: int,
        frame_count: int = None,
        columns: int = None,
        start_frame: int = 0,
        fps: float = 10.0,
        loop: bool = True,
        on_complete=None,
        enabled: bool = True,
    ):
        super().__init__(enabled)

        self._key = None
        self._animation = None
        self._time = 0.0
        self._fps = fps
        self._loop = loop
        self._on_complete = on_complete
        self._complete_fired = False

        self.set_animation(
            path, frame_width, frame_height, frame_count, columns,
            start_frame, fps, loop, on_complete,
        )

    def set_animation(
        self,
        path: str,
        frame_width: int,
        frame_height: int,
        frame_count: int = None,
        columns: int = None,
        start_frame: int = 0,
        fps: float = 10.0,
        loop: bool = True,
        on_complete=None,
    ):
        """Switch to a different sheet/slicing/clip. Resets playback
        to frame 0 and clears the completed flag."""
        self._key = SpriteSheetKey(
            path, frame_width, frame_height, frame_count, columns, start_frame
        )
        self._animation = None
        self._time = 0.0
        self._fps = fps
        self._loop = loop
        self._on_complete = on_complete
        self._complete_fired = False

        Assets.queue(self._key)

    @property
    def sprite(self):
        if self._animation is None:
            frames = Assets.get(self._key)
            if frames is None:
                return None
            self._animation = Animation(frames, fps=self._fps, loop=self._loop)
        return self._animation.frame_at(self._time)

    @property
    def width(self):
        sprite = self.sprite
        return sprite.width if sprite is not None else 0

    @property
    def height(self):
        sprite = self.sprite
        return sprite.height if sprite is not None else 0

    def get_rect(self):
        """Rect (x, y, width, height) from the actor's position and
        scale — same convenience as SpriteComponent.get_rect()."""
        actor = self.actor
        width = self.width * actor.scale.x
        height = self.height * actor.scale.y
        return (actor.position.x, actor.position.y, width, height)

    def update(self, dt):
        self._time += dt

        if (
            self._animation is not None
            and not self._complete_fired
            and self._animation.finished(self._time)
        ):
            self._complete_fired = True

            if self.actor is not None:
                self.actor.logger.info(
                    f"Animation complete on {self.actor.__class__.__name__}"
                )

            if self._on_complete:
                self._on_complete()