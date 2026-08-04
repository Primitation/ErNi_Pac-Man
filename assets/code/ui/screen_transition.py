"""Fade-to/from-black overlay."""

import time
from typing import Any, Protocol
from Engine import Assets


class _RendererLike(Protocol):
    """Structural type for the renderer object used by transitions."""

    width: int
    height: int

    def draw_rect_screen(
        self, x: int, y: int, w: int, h: int, color: int
    ) -> None:
        ...

    def draw_texture_region_screen(
        self,
        texture: Any,
        src_x: int,
        src_y: int,
        src_w: int,
        src_h: int,
        dst_x: int,
        dst_y: int,
        dst_w: int,
        dst_h: int,
    ) -> None:
        ...


class Transition:
    """One fade, either in or out."""

    def __init__(self, duration_ms: float = 300.0, color: int = 0x000000):
        self._duration = max(1.0, duration_ms)
        self._rgb = color & 0x00FFFFFF
        self._start_ms: float | None = None
        self.done = False

    def _elapsed_ms(self) -> float:
        if self._start_ms is None:
            self._start_ms = time.perf_counter() * 1000.0
        return (time.perf_counter() * 1000.0) - self._start_ms

    def _draw(self, renderer: _RendererLike, alpha: int) -> None:
        alpha = max(0, min(255, alpha))
        color = (alpha << 24) | self._rgb
        renderer.draw_rect_screen(
            0, 0, renderer.width, renderer.height, color
        )

    def draw_fade_in(self, renderer: _RendererLike) -> None:
        t = min(1.0, self._elapsed_ms() / self._duration)
        self._draw(renderer, int(255 * (1.0 - t)))
        if t >= 1.0:
            self.done = True

    def draw_fade_out(self, renderer: _RendererLike) -> None:
        t = min(1.0, self._elapsed_ms() / self._duration)
        self._draw(renderer, int(255 * t))
        if t >= 1.0:
            self.done = True


class PacmanTransition:
    """Pac-Man slides across the screen."""

    TEXTURE_PATH = "assets/texture/spritesheets/pacman_hd/" \
        "PacManAssets-PacMan.png"
    FRAME_WIDTH = 32
    FRAME_HEIGHT = 32
    FRAME_COUNT = 4
    FPS = 16

    def __init__(
        self,
        duration_ms: float = 700.0,
        size: int | None = None,
        color: int = 0x000000
    ):
        self._duration = max(1.0, duration_ms * 4)
        self._size = size
        self._rgb = color & 0x00FFFFFF
        self._start_ms: float | None = None
        self.done = False
        self._texture = Assets.load(self.TEXTURE_PATH)

    def _elapsed_ms(self) -> float:
        if self._start_ms is None:
            self._start_ms = time.perf_counter() * 1000.0
        return (time.perf_counter() * 1000.0) - self._start_ms

    def _pacman_size(self, renderer: _RendererLike) -> int:
        if self._size is None:
            return int(max(120, renderer.height))
        return self._size

    def _pacman_x(
        self, renderer: _RendererLike, t: float, size: int
    ) -> float:
        start_x = -size
        end_x = renderer.width + size
        return start_x + (end_x - start_x) * t

    def _draw_black(
        self, renderer: _RendererLike, x0: float, x1: float
    ) -> None:
        x0 = max(0, int(x0))
        x1 = min(renderer.width, int(x1))
        if x1 > x0:
            renderer.draw_rect_screen(
                x0, 0, x1 - x0, renderer.height, 0xFF000000 | self._rgb
            )

    def _draw_pacman(
        self, renderer: _RendererLike, x: float, size: int
    ) -> None:
        frame = int(self._elapsed_ms() / 1000.0 * self.FPS) % self.FRAME_COUNT
        y = (renderer.height - size) // 2
        renderer.draw_texture_region_screen(
            self._texture,
            frame * self.FRAME_WIDTH,
            0,
            self.FRAME_WIDTH,
            self.FRAME_HEIGHT,
            int(x - size / 2),
            y,
            size,
            size,
        )

    def draw_fade_out(self, renderer: _RendererLike) -> None:
        t = min(1.0, self._elapsed_ms() / self._duration)
        size = self._pacman_size(renderer)
        x = self._pacman_x(renderer, t, size)
        self._draw_black(renderer, 0, x)
        if t < 1.0:
            self._draw_pacman(renderer, x, size)
        if t >= 1.0:
            self.done = True

    def draw_fade_in(self, renderer: _RendererLike) -> None:
        t = min(1.0, self._elapsed_ms() / self._duration)
        size = self._pacman_size(renderer)
        x = self._pacman_x(renderer, t, size)
        self._draw_black(renderer, x, renderer.width)
        if t < 1.0:
            self._draw_pacman(renderer, x, size)
        if t >= 1.0:
            self.done = True
