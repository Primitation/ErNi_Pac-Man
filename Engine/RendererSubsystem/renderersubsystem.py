from mlx import Mlx

from .. import Assets
from .. import Log


class RendererSubsystem:
    """Owns mlx_init() and the window — this is the one place mlx_ptr
    gets created. Every other subsystem that needs mlx (right now,
    just AssetSubsystem) gets it wired in from here, so there's only
    ever one X11 connection for the whole app (see the earlier
    discussion on why two mlx_init() calls is a bad idea: images and
    windows have to share a context to be usable together)."""

    def __init__(self):
        self.mlx = None
        self.mlx_ptr = None
        self.win_ptr = None

        self._logger = Log.get("renderer")

    def init(self, width: int, height: int, title: str = "PrimiEngine"):
        """Call once, at startup, before anything else touches mlx
        (including Assets.load()/queue())."""

        self.mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()

        if self.mlx_ptr is None:
            raise RuntimeError(
                "mlx_init() failed — no display available (check your "
                "DISPLAY env var / that an X server is actually running)."
            )

        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, width, height, title
        )

        if self.win_ptr is None:
            raise RuntimeError("mlx_new_window() failed.")

        Assets.init(self.mlx, self.mlx_ptr)

        # Wired in automatically so the window's close (X) button
        # just works — no need for every caller to register their
        # own hook_close(). Call hook_close() yourself afterward if
        # you want different close behavior (e.g. a confirm prompt).
        self.mlx.mlx_hook(self.win_ptr, 33, 0, self._close_window, self)

        self._logger.info(f'Window created: {width}x{height} "{title}"')

    def render(self, world):
        """Call once per frame. Clears the window, then draws every
        actor in `world` at its own .position, in registration order
        (later adds draw on top of earlier ones). An actor whose
        sprite isn't ready yet (still loading via set_sprite() ->
        Assets.queue()) is just skipped for this frame rather than
        crashing.

        Note: this clears + redraws directly to the window each
        frame, which is the simplest thing that works but can
        flicker on some setups. If that becomes a problem, the fix
        is double buffering — draw into an off-screen image (built
        with mlx_new_image + manual pixel writes, the same technique
        TextureLoader.placeholder() uses) and mlx_put_image_to_window
        that single image once per frame instead. Ask if you want
        that version.
        """

        if self.win_ptr is None:
            raise RuntimeError(
                "RendererSubsystem.render() called before .init()."
            )

        self.mlx.mlx_clear_window(self.mlx_ptr, self.win_ptr)

        for actor in world:

            sprite = actor.sprite
            if sprite is None:
                continue

            try:
                self.mlx.mlx_put_image_to_window(
                    self.mlx_ptr, self.win_ptr, sprite.img,
                    int(actor.position.x), int(actor.position.y),
                )
            except Exception:
                self._logger.exception(f"Failed to draw actor {actor!r}")

    def hook_loop(self, callback, param=None):
        """Registers `callback` to run once per mlx event-loop tick
        (this is where your update/render frame goes). Must be
        called before .loop()."""

        self.mlx.mlx_loop_hook(self.mlx_ptr, callback, param)

    def hook_close(self, callback, param=None):
        """Registers `callback` for the window's close button (the X
        button), so you can call .close() / exit cleanly instead of
        the window just hanging."""

        self.mlx.mlx_hook(self.win_ptr, 33, 0, callback, param)

    def _close_window(self, param):
        """Default handler for the window's close (X) button (mlx
        event 33). Just stops the event loop — this runs as a
        ctypes callback, so raising here (sys.exit(), etc.) won't
        actually unwind anything; mlx_loop_exit() is the correct way
        to hand control back to whoever called .loop(). Do your real
        cleanup (Renderer.close(), sys.exit()) right after .loop()
        returns in your main loop instead."""

        self._logger.info("Window close requested.")
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def loop(self):
        """Hands control to mlx's own event loop. Blocks until the
        close button is hit (or something else calls mlx_loop_exit)
        — do cleanup right after this call returns, e.g.:

            Renderer.loop()
            Renderer.close()
            sys.exit(0)
        """

        self.mlx.mlx_loop(self.mlx_ptr)

    def close(self):
        if self.win_ptr is not None:
            self.mlx.mlx_destroy_window(self.mlx_ptr, self.win_ptr)
            self.win_ptr = None


# Global renderer system
Renderer = RendererSubsystem()