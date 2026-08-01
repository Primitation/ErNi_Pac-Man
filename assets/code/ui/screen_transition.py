"""Fade-to/from-black overlay, meant to be driven from inside a
screen's own frame() function.

MainMenu, LevelInstance and EndScreen each own a full mlx loop via
Renderer.hook_loop()/Renderer.loop() — there's no outer loop that
could take over rendering to insert a transition between them. So a
Transition doesn't run its own loop either: the screen keeps drawing
its normal content every frame, and just draws this overlay on top,
before Renderer.render_present().

Usage inside a screen:

    from assets.code.ui.screen_transition import Transition

    class MyScreen:
        def __init__(self):
            self._fade_in = Transition(300)
            self._fade_out = None   # created on demand, see below

        def show(self):
            def frame(_param):
                ... normal per-frame update/render ...
                Renderer.clear(...)
                ... draw normal content ...

                if self._fade_in is not None:
                    self._fade_in.draw_fade_in()
                    if self._fade_in.done:
                        self._fade_in = None

                if self._fade_out is not None:
                    self._fade_out.draw_fade_out()
                    if self._fade_out.done:
                        Renderer.close_request()

                Renderer.render_present()
                Input.update()

            Renderer.hook_loop(frame)
            Renderer.loop()

        def _on_quit(self):
            # instead of calling Renderer.close_request() directly,
            # start the fade — frame() above closes once it's done.
            self._fade_out = Transition(300)
"""

import time
from Engine import Assets


class Transition:
    """One fade, either in (opaque -> transparent) or out (transparent
    -> opaque). Call draw_fade_in()/draw_fade_out() once per frame;
    check .done to know when it's finished."""

    def __init__(self, duration_ms: float = 300.0, color: int = 0x000000):
        self._duration = max(1.0, duration_ms)
        self._rgb = color & 0x00FFFFFF
        self._start_ms = None
        self.done = False

    def _elapsed_ms(self) -> float:
        if self._start_ms is None:
            self._start_ms = time.perf_counter() * 1000.0
        return (time.perf_counter() * 1000.0) - self._start_ms

    def _draw(self, renderer, alpha: int) -> None:
        alpha = max(0, min(255, alpha))
        color = (alpha << 24) | self._rgb
        renderer.draw_rect_screen(0, 0, renderer.width, renderer.height, color)

    def draw_fade_in(self, renderer) -> None:
        """Overlay starts opaque, fades away. Call at the top of a
        screen's life; .done means the screen is fully visible."""
        t = min(1.0, self._elapsed_ms() / self._duration)
        self._draw(renderer, int(255 * (1.0 - t)))
        if t >= 1.0:
            self.done = True

    def draw_fade_out(self, renderer) -> None:
        """Overlay starts transparent, fades to opaque. Call once
        triggered (e.g. a button callback); .done means the screen is
        fully hidden — that's the cue to actually close/switch."""
        t = min(1.0, self._elapsed_ms() / self._duration)
        self._draw(renderer, int(255 * t))
        if t >= 1.0:
            self.done = True


class PacmanTransition:
    """Pac-Man slides across the screen, eating/revealing it as he
    goes. Same interface as Transition (draw_fade_in/draw_fade_out/
    .done) — drop-in swap wherever a Transition is used.

    fade_out (leaving a screen): black trails behind him, growing —
    screen ends up fully covered once he's crossed.
    fade_in (entering a screen): screen starts fully black; black
    stays ahead of him, shrinking — screen ends up fully revealed.

    Uses the same chomp spritesheet the Player actor animates
    (assets/code/actors/player.py's AnimatedSpriteComponent) — a
    horizontal strip of 4 frames, 32x32 each — just drawn much
    bigger and cycled by hand here instead of through that component,
    since this runs outside any Actor/World.
    """

    TEXTURE_PATH = "assets/texture/spritesheets/pacman_hd/PacManAssets-PacMan.png"
    FRAME_WIDTH = 32
    FRAME_HEIGHT = 32
    FRAME_COUNT = 4
    # Faster than the in-game 4fps: a 650ms crossing only has time for
    # a couple of loops at 4fps, so bump it up for a readable chomp.
    FPS = 16

    def __init__(self, duration_ms: float = 700.0, size: int = None,
                 color: int = 0x000000):
        self._duration = max(1.0, duration_ms*4)
        self._size = size  # None = auto-sized from screen height on first draw
        self._rgb = color & 0x00FFFFFF
        self._start_ms = None
        self.done = False
        self._texture = Assets.load(self.TEXTURE_PATH)

    def _elapsed_ms(self) -> float:
        if self._start_ms is None:
            self._start_ms = time.perf_counter() * 1000.0
        return (time.perf_counter() * 1000.0) - self._start_ms

    def _pacman_size(self, renderer) -> int:
        if self._size is None:
            return int(max(120, renderer.height))
        return self._size

    def _pacman_x(self, renderer, t: float, size: int) -> float:
        # Travels from fully off the left edge to fully off the right
        # edge, so he's never half-clipped at t=0 or t=1.
        start_x = -size
        end_x = renderer.width + size
        return start_x + (end_x - start_x) * t

    def _draw_black(self, renderer, x0: float, x1: float) -> None:
        x0 = max(0, int(x0))
        x1 = min(renderer.width, int(x1))
        if x1 > x0:
            renderer.draw_rect_screen(x0, 0, x1 - x0, renderer.height,
                                       0xFF000000 | self._rgb)

    def _draw_pacman(self, renderer, x: float, size: int) -> None:
        frame = int(self._elapsed_ms() / 1000.0 * self.FPS) % self.FRAME_COUNT
        y = (renderer.height - size) // 2
        renderer.draw_texture_region_screen(
            self._texture,
            frame * self.FRAME_WIDTH, 0, self.FRAME_WIDTH, self.FRAME_HEIGHT,
            int(x - size / 2), y, size, size,
        )

    def draw_fade_out(self, renderer) -> None:
        t = min(1.0, self._elapsed_ms() / self._duration)
        size = self._pacman_size(renderer)
        x = self._pacman_x(renderer, t, size)
        self._draw_black(renderer, 0, x)
        if t < 1.0:
            self._draw_pacman(renderer, x, size)
        if t >= 1.0:
            self.done = True

    def draw_fade_in(self, renderer) -> None:
        t = min(1.0, self._elapsed_ms() / self._duration)
        size = self._pacman_size(renderer)
        x = self._pacman_x(renderer, t, size)
        self._draw_black(renderer, x, renderer.width)
        if t < 1.0:
            self._draw_pacman(renderer, x, size)
        if t >= 1.0:
            self.done = True
