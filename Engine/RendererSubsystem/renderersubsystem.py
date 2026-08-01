import ctypes
import numpy as np
from typing import Any, Tuple
from mlx import Mlx
import math
from .. import Assets
from .. import Log, log_timing
from .. import Vector2


class RendererSubsystem:
    """Owns mlx_init(), the window and the render framebuffer."""

    def __init__(self):
        self.mlx = None
        self.mlx_ptr = None
        self.win_ptr = None

        self.framebuffer = None
        self.framebuffer_data = None
        self.framebuffer_ptr = None

        self.width = 0
        self.height = 0
        self.title = "PacEngine"

        self.bpp = 0
        self.line_size = 0
        self.pixel_size = 0
        self.format = 0

        self.buffer = None
        self.buffer_size = 0
        self.buffer_np = None        # numpy view over self.buffer, shape (height, line_size)
        self._buffer_cbuf = None     # cached ctypes buffer for memmove (built once, not per frame)
        self._clear_view = None      # buffer reinterpreted as whole pixels, for one-shot clear()

        self.bake_buffer = None      # baked static-actor background, same layout as self.buffer
        self.bake_np = None          # numpy view over bake_buffer
        self._baked = False
        self._last_bake_world = None            # world passed to the last bake() call, if any
        self._last_bake_background_color = 0xFF000000

        # Camera: camera_position is the WORLD point centered on screen.
        # zoom is a screen-pixels-per-world-unit multiplier (1.0 = no
        # zoom). See world_to_screen().
        self.camera_position = Vector2(0.0, 0.0)
        self.zoom = 1.0

        # Camera state as of the last bake() call. bake() pre-renders
        # static actors once, so if the camera moves/zooms after that,
        # the baked pixels no longer reflect the current view. clear()
        # and render_draw() check _camera_matches_bake() and fall back
        # to redrawing static actors fresh (still correctly
        # transformed) whenever the camera has since diverged.
        self._bake_camera_position = Vector2(0.0, 0.0)
        self._bake_zoom = 1.0

        self._scale_cache = {}       # (id(texture), scaled_w, scaled_h) -> resampled numpy array
        self._resize_listeners = []  # callbacks notified with (win_ptr, width, height) after resize()

        self._logger = Log.get("renderer")
        self._frame_count = 0

        self._debug_draw_colliders = False
        self._debug_collider_color_map = None
        # Off by default — assets/code/ui/gameplay_hud.py now draws the
        # real HUD (lives/score/time). Flip to True for a quick text
        # fallback if the HUD widgets ever need bypassing for debug.
        self._draw_debug_banner = False

    def init(self, width: int, height: int, title: str = "PacEngine"):
        """Call once, at startup, before anything else touches mlx."""

        self.width = width
        self.height = height
        self.title = title

        self.mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()

        if self.mlx_ptr is None:
            raise RuntimeError("mlx_init() failed — no display available.")

        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, width, height, title
        )

        if self.win_ptr is None:
            raise RuntimeError("mlx_new_window() failed.")

        self.framebuffer = self.mlx.mlx_new_image(
            self.mlx_ptr, width, height
        )

        if self.framebuffer is None:
            raise RuntimeError("mlx_new_image() failed.")

        (
            self.framebuffer_data,
            self.bpp,
            self.line_size,
            self.format
        ) = self.mlx.mlx_get_data_addr(self.framebuffer)

        self.pixel_size = self.bpp // 8
        self.framebuffer_ptr = ctypes.addressof(self.framebuffer_data.obj)
        self.buffer_size = self.height * self.line_size
        self.buffer = bytearray(self.buffer_size)

        # Zero-copy numpy view over self.buffer. Writes to buffer_np land
        # directly in self.buffer's memory — no extra copy anywhere.
        self.buffer_np = np.frombuffer(self.buffer, dtype=np.uint8).reshape(
            self.height, self.line_size
        )

        # Built once instead of re-wrapping self.buffer every render() call.
        self._buffer_cbuf = (ctypes.c_char * self.buffer_size).from_buffer(self.buffer)

        # Reinterpret the buffer as whole pixels (not individual bytes) so
        # clear() can assign a color to the entire framebuffer in one
        # vectorized call instead of building/tiling a row per clear.
        pixel_dtype = {1: np.uint8, 2: np.uint16, 4: np.uint32}.get(self.pixel_size)
        if pixel_dtype is not None and self.line_size % self.pixel_size == 0:
            self._clear_view = self.buffer_np.view(dtype=pixel_dtype)
        else:
            # Unusual pixel size (e.g. 3 bytes/pixel) — clear() falls back
            # to the tiled-row approach below.
            self._clear_view = None

        self._logger.debug(
            f"Framebuffer info: bpp={self.bpp}, line_size={self.line_size}, "
            f"format={self.format}, pixel_size={self.pixel_size}"
        )

        Assets.init(self.mlx, self.mlx_ptr)

        self.mlx.mlx_hook(
            self.win_ptr, 33, 0, self._close_window, self
        )

        self._logger.info(f'Window created: {width}x{height} "{title}"')

        # Clear with FULLY OPAQUE BLACK
        self.clear(0xFF000000)

    def set_camera(self, position: Vector2) -> None:
        """Move the camera. `position` is the world point that gets
        centered on screen."""
        self.camera_position = position

    def move_camera(self, dx: float, dy: float) -> None:
        """Pan the camera by (dx, dy) in world units."""
        self.camera_position = Vector2(
            self.camera_position.x + dx, self.camera_position.y + dy
        )

    def set_zoom(self, zoom: float) -> None:
        """Set the zoom level. 1.0 = no zoom, 2.0 = twice as large
        on screen, 0.5 = half size."""
        if zoom <= 0:
            raise ValueError("zoom must be > 0")
        self.zoom = zoom

    def zoom_by(self, factor: float) -> None:
        """Multiply the current zoom by `factor`."""
        self.set_zoom(self.zoom * factor)

    def _camera_matches_bake(self) -> bool:
        """Whether the live camera is still where it was when bake()
        last ran — i.e. whether the baked background pixels are still
        valid to use as-is."""
        return (
            abs(self.camera_position.x - self._bake_camera_position.x) < 1e-6
            and abs(self.camera_position.y - self._bake_camera_position.y) < 1e-6
            and abs(self.zoom - self._bake_zoom) < 1e-6
        )

    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Converts world-space coordinates to framebuffer pixel
        coordinates, applying the current camera_position and zoom.
        camera_position is the world point centered on screen."""
        screen_x = (x - self.camera_position.x) * self.zoom + self.width / 2.0
        screen_y = (y - self.camera_position.y) * self.zoom + self.height / 2.0
        return screen_x, screen_y

    def _get_component_position(self, component):
        """Get the world position of a component (actor position + local offset)."""
        if hasattr(component, 'get_world_position'):
            return component.get_world_position()
        # Fallback for components without local offset support
        actor = getattr(component, 'actor', None)
        if actor is not None:
            return (actor.position.x, actor.position.y)
        return (0.0, 0.0)

    def _sprite_for(self, actor):
        """Find the actor's current sprite by checking its
        components. Actors no longer carry a sprite directly —
        SpriteComponent and AnimatedSpriteComponent (Engine.Components)
        both expose a `.sprite` property, so this just looks for the
        first component that has one and returns whatever it's
        currently resolving to (None if that component's asset
        hasn't finished loading yet).

        Duck-typed on purpose (checks `hasattr(component, "sprite")`
        rather than isinstance against SpriteComponent /
        AnimatedSpriteComponent) so any future component that wants
        to be drawn just needs to expose `.sprite` — no changes
        needed here."""
        out_components: list[Any] = []

        components = getattr(actor, "components", None)
        if not components:
            return None

        for component in components:
            if hasattr(component, "sprite"):
                out_components.append(component)
        return out_components

    def _fill_solid(self, color: int):
        """One-shot solid color fill — the actual pixel-writing work.
        Used by clear() when there's no baked background, and by
        bake() itself to paint the initial background before drawing
        static actors onto it."""

        if self._clear_view is not None:
            pixel_value = color & ((1 << (self.pixel_size * 8)) - 1)
            self._clear_view[:, :self.width] = pixel_value
            return

        # Fallback for unusual pixel sizes that don't evenly divide
        # line_size (see init()).
        pixel_bytes = np.frombuffer(
            color.to_bytes(self.pixel_size, "little"), dtype=np.uint8
        )
        row = np.tile(pixel_bytes, self.width)
        if len(row) < self.line_size:
            row = np.concatenate(
                [row, np.zeros(self.line_size - len(row), dtype=np.uint8)]
            )
        self.buffer_np[:, :] = row

    def clear(self, color: int = 0xFF000000):
        """Clears the framebuffer before drawing the next frame.

        If bake() has been called AND the camera hasn't moved/zoomed
        since (see _camera_matches_bake), this copies the baked
        static-actor background in one vectorized operation instead
        of filling a solid color — `color` is ignored in that case,
        since the baked image already has its own background baked
        in.

        If the camera has since panned or zoomed away from where it
        was at bake time, the baked pixels no longer line up with the
        current view, so this falls back to a solid fill instead —
        render_draw() detects the same mismatch and redraws static
        actors fresh (with the current camera transform) that frame."""

        if self._baked and self._camera_matches_bake():
            self.buffer_np[:, :] = self.bake_np
            return

        self._fill_solid(color)

    def bake(self, world, background_color: int = 0xFF000000,
             max_wait_ticks: int = 300):
        """Pre-renders every static actor once into an internal
        background buffer. Call this after all static actors have
        been spawned — typically right before entering the main loop.

        From then on, clear() copies this baked image in a single
        buffer copy instead of re-blitting every static actor's
        sprite every single frame. render() also skips static actors
        in its per-frame draw loop, since they're already part of the
        baked background.

        An actor counts as static if `getattr(actor, "static", False)`
        is True — add a `static` attribute/flag to your Actor class
        (or subclasses) to opt in.

        Sprite assets resolve asynchronously (see _sprite_for) — a
        component's `.sprite` is None until its asset has finished
        loading. Since bake() only runs once, calling it before the
        assets are ready would silently skip those actors and leave
        a blank/solid-color background forever. To avoid that, bake()
        pumps Assets.update() (up to `max_wait_ticks` times) until
        every static actor's sprite components have resolved, or
        gives up and bakes anyway with a warning.

        Call bake() again (e.g. after spawning/removing static actors)
        to rebuild the background; call unbake() to go back to a
        plain solid-color clear()."""

        self._last_bake_world = world
        self._last_bake_background_color = background_color

        # Build directly into the main buffer as scratch — bypass the
        # baked shortcut in clear() while we're constructing the bake.
        self._baked = False
        self._fill_solid(background_color)

        static_actors = [a for a in world if getattr(a, "static", False)]

        def _sprites_pending() -> bool:
            for actor in static_actors:
                components = self._sprite_for(actor)
                if not components:
                    continue
                for component in components:
                    if getattr(component, 'sprite', None) is None:
                        return True
            return False

        ticks = 0
        while _sprites_pending() and ticks < max_wait_ticks:
            Assets.update()
            ticks += 1
        if ticks >= max_wait_ticks and _sprites_pending():
            self._logger.warning(
                "bake(): some static actor sprite(s) hadn't finished "
                f"loading after {max_wait_ticks} Assets.update() tick(s); "
                "baking anyway — those actors may be missing from the "
                "baked background."
            )

        # Collect every (actor, component) with a sprite, then sort by
        # render_layer — same rationale as render_draw(): guarantees
        # e.g. every wall (layer 0) bakes before any corner (layer 1)
        # across all cells, regardless of spawn order, so corners sit
        # on top at shared boundary pixels instead of it being
        # order-dependent.
        draw_list = []
        for actor in static_actors:
            components = self._sprite_for(actor)
            if components is None:
                continue
            for component in components:
                if getattr(component, 'sprite', None) is None:
                    continue
                draw_list.append((actor, component))

        draw_list.sort(key=lambda pair: getattr(pair[1], 'render_layer', 0))

        for actor, component in draw_list:
            sprite = component.sprite
            if sprite is None:
                continue
            try:
                rotation = getattr(actor, 'rotation', 0.0)
                component_rotation = getattr(component, 'local_rotation', 0.0)
                pivot = getattr(actor, 'pivot', (0.5, 0.5))
                position = self._get_component_position(component)
                # Create a position object with x,y attributes
                pos = type('Position', (), {'x': position[0], 'y': position[1]})()
                get_world_scale = getattr(component, 'get_world_scale', None)
                scale = get_world_scale() if get_world_scale is not None else actor.scale
                self.draw_sprite(sprite, pos, scale, rotation + component_rotation, pivot)
            except Exception:
                self._logger.exception(f"Failed to bake actor {actor!r}")

        if self.bake_buffer is None:
            self.bake_buffer = bytearray(self.buffer_size)
            self.bake_np = np.frombuffer(self.bake_buffer, dtype=np.uint8).reshape(
                self.height, self.line_size
            )

        self.bake_np[:, :] = self.buffer_np
        self._baked = True

        self._bake_camera_position = Vector2(
            self.camera_position.x, self.camera_position.y
        )
        self._bake_zoom = self.zoom

        self._logger.info(
            f"Baked {len(static_actors)} static actor(s) into background "
            f"at camera=({self._bake_camera_position.x}, "
            f"{self._bake_camera_position.y}), zoom={self._bake_zoom}."
        )

    def unbake(self):
        """Reverts to a plain solid-color clear() instead of the
        baked background. The baked buffer itself is kept around
        (not freed) so a later bake() call is cheap to redo."""

        self._baked = False

    def put_pixel(self, x: int, y: int, color: int):
        """Writes a pixel into the framebuffer. (x, y) is a WORLD
        coordinate — transformed through the current camera_position/
        zoom before writing."""

        screen_x, screen_y = self.world_to_screen(x, y)
        x, y = int(screen_x), int(screen_y)

        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return

        offset = x * self.pixel_size
        self.buffer_np[y, offset:offset + self.pixel_size] = np.frombuffer(
            color.to_bytes(self.pixel_size, "little"), dtype=np.uint8
        )

    def draw_rect(self, x, y, width, height, color: int):
        """Fill an axis-aligned rect with a solid 0xAARRGGBB color,
        alpha-blending against whatever's already in the framebuffer
        when color isn't fully opaque (same blend math as sprite
        drawing, just for a flat color instead of a texture).

        Meant for cheap effects that don't need a real texture — see
        ParticleSubsystem, which draws every particle this way
        instead of loading/blitting a sprite per particle.

        (x, y, width, height) are WORLD-space — transformed through
        the current camera_position/zoom before drawing."""

        screen_x, screen_y = self.world_to_screen(x, y)
        x, y = int(screen_x), int(screen_y)
        width = int(width * self.zoom)
        height = int(height * self.zoom)

        if width <= 0 or height <= 0:
            return

        clip_x0 = max(0, -x)
        clip_y0 = max(0, -y)
        x = max(0, x)
        y = max(0, y)

        dw = min(width - clip_x0, self.width - x)
        dh = min(height - clip_y0, self.height - y)

        if dw <= 0 or dh <= 0:
            return

        dest_view = self.buffer_np[
            y:y + dh,
            x * self.pixel_size: (x + dw) * self.pixel_size,
        ].reshape(dh, dw, self.pixel_size)

        pixel_bytes = np.frombuffer(
            color.to_bytes(self.pixel_size, "little"), dtype=np.uint8
        )

        alpha = (color >> 24) & 0xFF if self.pixel_size == 4 else 255

        if alpha == 0:
            return

        if alpha == 255:
            dest_view[:, :, :] = pixel_bytes
            return

        a = np.uint16(alpha)
        src = pixel_bytes.astype(np.uint16)
        blended = (src * a + dest_view.astype(np.uint16) * (255 - a)) // 255
        blended[..., 3] = 255
        dest_view[:, :, :] = blended.astype(np.uint8)

    def draw_sprite(self, texture, position, scale, rotation=0.0, pivot=(0.5, 0.5)):
        """Draws a texture into the framebuffer with scaling and
        rotation support. `position` is WORLD space — converted to
        screen pixels via world_to_screen() (current camera_position/
        zoom) before drawing. `scale` is likewise multiplied by the
        current zoom, so a sprite keeps its correct on-screen size as
        the camera zooms in/out.

        scale_x/scale_y apply in the sprite's own LOCAL (pre-rotation)
        frame — e.g. scale=(2.61, 1.0) always stretches along the
        sprite's own width axis, regardless of rotation. The actual
        on-screen box is then whatever that stretched local box looks
        like once rotated (so a wall stretched wide at rotation=0
        correctly becomes stretched TALL at rotation=90, rather than
        staying wide — see _blit_rotated)."""

        if hasattr(scale, 'x') and hasattr(scale, 'y'):
            scale_x = scale.x
            scale_y = scale.y
        else:
            scale_x = float(scale)
            scale_y = float(scale)

        screen_x, screen_y = self.world_to_screen(position.x, position.y)
        dest_x = int(screen_x)
        dest_y = int(screen_y)

        # Local (pre-rotation) box dimensions
        scaled_width = max(1, int(texture.width * scale_x * self.zoom))
        scaled_height = max(1, int(texture.height * scale_y * self.zoom))

        if scaled_width <= 0 or scaled_height <= 0:
            return

        # Use rotation if specified (with small epsilon to avoid unnecessary work)
        if abs(rotation) > 0.001:
            angle_rad = math.radians(rotation)
            cos_a = abs(math.cos(angle_rad))
            sin_a = abs(math.sin(angle_rad))

            # On-screen bounding box of the local box after rotation.
            # At 90/270 this cleanly swaps width<->height; at 0/180 it
            # stays as-is; angles in between blend smoothly.
            out_width = max(1, int(round(scaled_width * cos_a + scaled_height * sin_a)))
            out_height = max(1, int(round(scaled_width * sin_a + scaled_height * cos_a)))

            # dest_x/dest_y was computed (often by a component's
            # center=True logic) as the top-left of a box sized
            # (scaled_width, scaled_height). Since the box actually
            # drawn is (out_width, out_height), re-center around the
            # same point so a centered sprite's anchor doesn't drift
            # sideways just because rotation changed its footprint.
            dest_x -= (out_width - scaled_width) // 2
            dest_y -= (out_height - scaled_height) // 2

            self._blit_rotated(texture, dest_x, dest_y, rotation,
                            pivot[0], pivot[1],
                            scaled_width, scaled_height,
                            out_width, out_height)
        elif scale_x == 1.0 and scale_y == 1.0 and self.zoom == 1.0:
            self._blit(texture, dest_x, dest_y)
        else:
            self._blit(texture, dest_x, dest_y, scaled_width, scaled_height)

    @staticmethod
    def _get_texture_array(texture):
        """Returns a numpy (H, W, bpp) view over texture.data, cached on
        the texture itself. Textures are immutable after load, so this
        is safe to build once and reuse across every draw call/frame."""

        cached = getattr(texture, "_np_cache", None)
        if cached is not None:
            return cached

        raw = np.frombuffer(texture.data, dtype=np.uint8)
        raw = raw[: texture.line_size * texture.height].reshape(
            texture.height, texture.line_size
        )
        arr = raw[:, : texture.width * texture.bytes_per_pixel].reshape(
            texture.height, texture.width, texture.bytes_per_pixel
        )

        try:
            texture._np_cache = arr
        except AttributeError:
            pass

        return arr

    def _blit(self, texture, dest_x, dest_y, scaled_width=None, scaled_height=None):
        """Vectorized blit — replaces the old per-pixel draw_sprite /
        _draw_sprite_direct loops. Handles direct copy, nearest-neighbor
        scaling, and BGRA alpha blending, all as array ops."""

        tex = self._get_texture_array(texture)

        if scaled_width is None:
            region = tex
        else:
            # Same texture drawn at the same target size every frame
            # (the overwhelmingly common case — e.g. an actor with a
            # fixed scale) reuses the resampled array instead of
            # re-gathering it every call. Only actually re-resamples
            # the first time a given (texture, size) combo is seen.
            cache_key = (id(texture), scaled_width, scaled_height)
            region = self._scale_cache.get(cache_key)

            if region is None:
                src_ys = (np.arange(scaled_height) * texture.height // scaled_height)
                src_xs = (np.arange(scaled_width) * texture.width // scaled_width)
                src_ys = src_ys.clip(0, texture.height - 1)
                src_xs = src_xs.clip(0, texture.width - 1)
                region = tex[np.ix_(src_ys, src_xs)]
                self._scale_cache[cache_key] = region

        src_h, src_w = region.shape[0], region.shape[1]

        # Clip against screen bounds
        clip_x0, clip_y0 = 0, 0
        clip_x1, clip_y1 = src_w, src_h

        if dest_x < 0:
            clip_x0 = -dest_x
            dest_x = 0
        if dest_y < 0:
            clip_y0 = -dest_y
            dest_y = 0
        if dest_x + (clip_x1 - clip_x0) > self.width:
            clip_x1 = clip_x0 + (self.width - dest_x)
        if dest_y + (clip_y1 - clip_y0) > self.height:
            clip_y1 = clip_y0 + (self.height - dest_y)

        if clip_x1 <= clip_x0 or clip_y1 <= clip_y0:
            return  # fully off-screen

        region = region[clip_y0:clip_y1, clip_x0:clip_x1]
        dh, dw = region.shape[0], region.shape[1]

        dest_view = self.buffer_np[
            dest_y:dest_y + dh,
            dest_x * self.pixel_size: (dest_x + dw) * self.pixel_size,
        ].reshape(dh, dw, self.pixel_size)

        if texture.bytes_per_pixel == 4 and self.pixel_size == 4:
            alpha = region[:, :, 3]

            opaque_mask = alpha == 255
            transparent_mask = alpha == 0
            fully_opaque = opaque_mask.all()
            fully_transparent = transparent_mask.all()

            # Fast paths cover the overwhelmingly common cases: sprites
            # with hard-edged transparency (no soft/antialiased alpha).
            if fully_transparent:
                return
            if fully_opaque:
                dest_view[:, :, :] = region
                return

            blend_mask = ~(opaque_mask | transparent_mask)
            if not blend_mask.any():
                # Mixed opaque/transparent, but no partial-alpha pixels —
                # skip the blend math entirely.
                dest_view[opaque_mask] = region[opaque_mask]
                return

            # General path: real alpha blending where needed.
            a = alpha.astype(np.uint16)[:, :, None]
            blended = (
                region[:, :, :4].astype(np.uint16) * a
                + dest_view.astype(np.uint16) * (255 - a)
            ) // 255
            blended[:, :, 3] = 255

            dest_view[~transparent_mask] = blended[~transparent_mask].astype(np.uint8)
            dest_view[opaque_mask] = region[opaque_mask]
        else:
            # No alpha channel — straight copy.
            dest_view[:, :, :] = region[:, :, :self.pixel_size]

    def _blit_rotated(self, texture, dest_x, dest_y, angle_degrees,
                      pivot_x=0.5, pivot_y=0.5,
                      local_width=None, local_height=None,
                      out_width=None, out_height=None):
        """Vectorized blit with rotation support using nearest-neighbor rotation.

        local_width/local_height are the sprite's box dimensions in
        its own frame, BEFORE rotation is applied (i.e. after
        per-axis scale only) — used to work out which texture pixel
        each output pixel samples. out_width/out_height are the
        actual on-screen canvas size (the local box's bounding box
        AFTER rotation — see draw_sprite) — used for the drawn area.
        These two differ whenever scale_x != scale_y and rotation
        isn't a multiple of 180; keeping them separate is what lets a
        wall stretched wide at rotation=0 correctly render tall
        instead of wide once rotated to 90.

        pivot is treated as the same fractional point in both boxes,
        which is exact for the default center pivot (0.5, 0.5) used
        throughout this codebase; an off-center pivot combined with
        non-square scaling would need a fully general bounding-box
        calculation, which isn't implemented here."""

        tex = self._get_texture_array(texture)
        src_h, src_w = tex.shape[0], tex.shape[1]

        if local_width is None:
            local_width = src_w
        if local_height is None:
            local_height = src_h
        if out_width is None:
            out_width = local_width
        if out_height is None:
            out_height = local_height

        # Pre-compute cos/sin once
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Create output grid (post-rotation canvas size)
        y_coords, x_coords = np.mgrid[0:out_height, 0:out_width]

        # Pivot location within each box
        out_pivot_x = pivot_x * out_width
        out_pivot_y = pivot_y * out_height
        local_pivot_x = pivot_x * local_width
        local_pivot_y = pivot_y * local_height

        # Position relative to pivot, in OUTPUT (post-rotation) space
        x_rel = x_coords - out_pivot_x
        y_rel = y_coords - out_pivot_y

        # Inverse-rotate back into the LOCAL (pre-rotation) box, then
        # shift from pivot-relative back to local-box space
        local_x = x_rel * cos_a + y_rel * sin_a + local_pivot_x
        local_y = -x_rel * sin_a + y_rel * cos_a + local_pivot_y

        # Scale from the local (pre-rotation) box into texture pixels
        src_x = local_x * (src_w / local_width)
        src_y = local_y * (src_h / local_height)

        # Clip to texture bounds
        src_x = np.clip(src_x, 0, src_w - 1).astype(np.int32)
        src_y = np.clip(src_y, 0, src_h - 1).astype(np.int32)

        # Sample the texture
        region = tex[src_y, src_x]

        # Now blit this region like in _blit
        return self._blit_region(region, dest_x, dest_y,
                                out_width, out_height, texture.bytes_per_pixel)

    def _blit_region(self, region, dest_x, dest_y, region_w, region_h, bpp):
        """Internal method to blit a pre-processed region."""
        # Similar to the clipping/alpha blending code from _blit
        clip_x0, clip_y0 = 0, 0
        clip_x1, clip_y1 = region_w, region_h

        if dest_x < 0:
            clip_x0 = -dest_x
            dest_x = 0
        if dest_y < 0:
            clip_y0 = -dest_y
            dest_y = 0
        if dest_x + (clip_x1 - clip_x0) > self.width:
            clip_x1 = clip_x0 + (self.width - dest_x)
        if dest_y + (clip_y1 - clip_y0) > self.height:
            clip_y1 = clip_y0 + (self.height - dest_y)

        if clip_x1 <= clip_x0 or clip_y1 <= clip_y0:
            return

        region = region[clip_y0:clip_y1, clip_x0:clip_x1]
        dh, dw = region.shape[0], region.shape[1]

        dest_view = self.buffer_np[
            dest_y:dest_y + dh,
            dest_x * self.pixel_size: (dest_x + dw) * self.pixel_size,
        ].reshape(dh, dw, self.pixel_size)

        # Alpha blending (same as _blit)
        if bpp == 4 and self.pixel_size == 4:
            alpha = region[:, :, 3]

            opaque_mask = alpha == 255
            transparent_mask = alpha == 0
            fully_opaque = opaque_mask.all()
            fully_transparent = transparent_mask.all()

            if fully_transparent:
                return
            if fully_opaque:
                dest_view[:, :, :] = region
                return

            blend_mask = ~(opaque_mask | transparent_mask)
            if not blend_mask.any():
                dest_view[opaque_mask] = region[opaque_mask]
                return

            a = alpha.astype(np.uint16)[:, :, None]
            blended = (
                region[:, :, :4].astype(np.uint16) * a
                + dest_view.astype(np.uint16) * (255 - a)
            ) // 255
            blended[:, :, 3] = 255

            dest_view[~transparent_mask] = blended[~transparent_mask].astype(np.uint8)
            dest_view[opaque_mask] = region[opaque_mask]
        else:
            dest_view[:, :, :] = region[:, :, :self.pixel_size]

    def render_draw(self, world):
        """Draw all actors into the framebuffer (no presentation)."""
        if self.win_ptr is None:
            raise RuntimeError("RendererSubsystem.render_draw() called before .init().")

        # Clear with FULLY OPAQUE BLACK — or, if bake() has been called
        # and the camera still matches, copies the baked static-actor
        # background instead.
        self.clear(0xFFAAAAAA)

        baked_valid = self._baked and self._camera_matches_bake()

        # Collect every (actor, component) with a sprite to draw, then
        # sort by render_layer — a stable sort, so within the same
        # layer the original per-actor / per-component order (later
        # actors, and later components on the same actor, overwrite
        # earlier ones) is preserved as-is. This guarantees e.g. every
        # wall (layer 0) draws before any corner (layer 1) even across
        # different actors/cells, instead of depending on world/spawn
        # order at their shared boundary pixels.
        draw_list = []
        for actor in world:
            if baked_valid and getattr(actor, "static", False):
                continue

            components = self._sprite_for(actor)
            if components is None:
                continue
            for component in components:
                if getattr(component, 'sprite', None) is None:
                    continue
                draw_list.append((actor, component))

        draw_list.sort(key=lambda pair: getattr(pair[1], 'render_layer', 0))

        for actor, component in draw_list:
            sprite = component.sprite
            if sprite is None:
                continue

            try:
                rotation = getattr(actor, 'rotation', 0.0)
                pivot = getattr(actor, 'pivot', (0.5, 0.5))
                component_rotation = getattr(component, 'local_rotation', 0.0)
                position = self._get_component_position(component)
                # Create a position object with x,y attributes
                pos = type('Position', (), {'x': position[0], 'y': position[1]})()
                get_world_scale = getattr(component, 'get_world_scale', None)
                scale = get_world_scale() if get_world_scale is not None else actor.scale
                self.draw_sprite(
                    sprite,
                    pos,
                    scale,
                    rotation + component_rotation,
                    pivot
                )
            except Exception:
                self._logger.exception(f"Failed to draw actor {actor!r}")

    def render_level_banner(self) -> None:
        from assets.code.actors.player import Player

        # No level in progress (e.g. we're on the main menu) — nothing to
        # draw. Not an error, so don't fall through to the except below.
        if Player.current_player is None:
            return

        try:
            from .. import Actors
            text = (f"Score  {Player.current_player.score_info.score}   "
                    f"Lives  {Player.current_player.lives}   "
                    f"Level  {Player.current_level}    "
                    f"Time  {max(0, round(Actors.remaining_time, 1))}")
            self.mlx.mlx_string_put(
                self.mlx_ptr, self.win_ptr, 20,
                self.height - 50,
                0x000000FF,
                text)
        except Exception:
            self._logger.exception("Failed to draw level banner")

    def render_present(self):
        """Present the framebuffer to the screen."""
        if self.win_ptr is None:
            raise RuntimeError("RendererSubsystem.render_present() called before .init().")

        # Copy our buffer to the framebuffer (cached ctypes wrapper, no per-frame allocation)
        ctypes.memmove(
            self.framebuffer_ptr,
            ctypes.addressof(self._buffer_cbuf),
            self.buffer_size
        )

        # Present the framebuffer to the window
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr,
            self.win_ptr,
            self.framebuffer,
            0,
            0,
        )
        if self._draw_debug_banner:
            self.render_level_banner()

    def render(self, world):
        """Legacy method - draws and presents in one call."""
        self.render_draw(world)
        self.render_present()

    def hook_loop(self, callback, param=None):
        """Registers `callback` to run once per mlx event-loop tick."""
        self.mlx.mlx_loop_hook(self.mlx_ptr, callback, param)

    def hook_close(self, callback, param=None):
        """Registers a custom close callback."""
        self.mlx.mlx_hook(self.win_ptr, 33, 0, callback, param)

    def _close_window(self, param):
        """Default window close handler."""
        self._logger.info("Window close requested.")
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def loop(self):
        """Starts the mlx event loop."""
        self._logger.info("Starting MLX event loop...")
        result = self.mlx.mlx_loop(self.mlx_ptr)
        self._logger.info(f"MLX event loop exited with: {result}")

    def close(self):
        """Destroys the window."""
        if self.win_ptr is not None:
            self.mlx.mlx_destroy_window(self.mlx_ptr, self.win_ptr)
            self.win_ptr = None

    def close_request(self):
        """Request the MLX loop to exit."""

        self._logger.info("Quit requested.")

        if self.mlx_ptr is not None:
            self.mlx.mlx_loop_exit(
                self.mlx_ptr
            )

    def on_resize(self, callback):
        """Register a callback to be notified after resize() rebuilds
        the window. Called as callback(win_ptr, width, height) with
        the *new* window pointer — use this to rebind anything that
        hooked mlx_hook() onto the old win_ptr directly (e.g. Input's
        key/mouse hooks), since that window is destroyed by resize()
        and takes its hooks with it. Without rebinding, the engine
        keeps running fine (the frame loop is hooked to mlx_ptr, not
        the window) but input will silently stop responding."""
        self._resize_listeners.append(callback)

    def resize(self, width: int, height: int, title: str = None):
        """Resize the window and framebuffer to a new width/height.

        Destroys the current native window and rebuilds it (and the
        framebuffer image + all buffers) at the new size — mirrors
        the buffer-setup steps in init(), just without re-running
        mlx_init(). If bake() had been called, the old baked background
        no longer matches the new size, so it's dropped and immediately
        rebuilt at the new dimensions from the same world/background_color
        used last time — no need to call bake() again yourself. If a
        static actor was added or removed via a normal bake() call in
        between, that's still what gets rebaked here, since we just
        re-run bake() with whatever world reference was last given."""

        if self.win_ptr is None:
            raise RuntimeError("RendererSubsystem.resize() called before .init().")

        if title is None:
            title = self.title

        self.close()  # destroys the old window (self.win_ptr -> None)

        self.width = width
        self.height = height
        self.title = title

        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, width, height, title
        )

        if self.win_ptr is None:
            raise RuntimeError("mlx_new_window() failed during resize().")

        self.framebuffer = self.mlx.mlx_new_image(
            self.mlx_ptr, width, height
        )

        if self.framebuffer is None:
            raise RuntimeError("mlx_new_image() failed during resize().")

        (
            self.framebuffer_data,
            self.bpp,
            self.line_size,
            self.format
        ) = self.mlx.mlx_get_data_addr(self.framebuffer)

        self.pixel_size = self.bpp // 8
        self.framebuffer_ptr = ctypes.addressof(self.framebuffer_data.obj)
        self.buffer_size = self.height * self.line_size
        self.buffer = bytearray(self.buffer_size)

        self.buffer_np = np.frombuffer(self.buffer, dtype=np.uint8).reshape(
            self.height, self.line_size
        )
        self._buffer_cbuf = (ctypes.c_char * self.buffer_size).from_buffer(self.buffer)

        pixel_dtype = {1: np.uint8, 2: np.uint16, 4: np.uint32}.get(self.pixel_size)
        if pixel_dtype is not None and self.line_size % self.pixel_size == 0:
            self._clear_view = self.buffer_np.view(dtype=pixel_dtype)
        else:
            self._clear_view = None

        # Old bake buffer is the wrong size for the new dimensions — drop
        # it, then immediately rebake from the last world/color passed to
        # bake() (if any) so callers don't have to remember to redo it
        # after every resize. Falls back to a solid fill on the next
        # clear() if bake() was never called in the first place.
        self._baked = False
        self.bake_buffer = None
        self.bake_np = None

        if self._last_bake_world is not None:
            try:
                self.bake(self._last_bake_world, self._last_bake_background_color)
            except Exception:
                self._logger.exception("Failed to rebake background after resize")

        self.mlx.mlx_hook(
            self.win_ptr, 33, 0, self._close_window, self
        )

        self._logger.info(f'Window resized: {width}x{height} "{title}"')

        self.clear(0xFF000000)

        # Let anything bound to the old win_ptr (e.g. Input's key/mouse
        # hooks) rebind itself against the new one.
        for listener in self._resize_listeners:
            try:
                listener(self.win_ptr, width, height)
            except Exception:
                self._logger.exception("resize listener failed")

    def _color_to_bytes(self, color: int) -> np.ndarray:
        """Convert a 0xAARRGGBB color to a numpy array of bytes in the framebuffer's pixel format."""
        return np.frombuffer(
            color.to_bytes(self.pixel_size, "little"), dtype=np.uint8
        )

    def draw_rect_outline(self, x, y, width, height, color: int = 0xFFFF0000, thickness: int = 1):
        """
        Draw a rectangle outline with the given thickness in WORLD-space.
        Useful for debug visualization of colliders, bounding boxes, etc.

        x, y, width, height are in WORLD-space (transformed through camera).
        color: 0xAARRGGBB format, default is bright red (0xFFFF0000).
        thickness: outline thickness in screen pixels (default 1).
        """
        if width <= 0 or height <= 0:
            return

        # Convert world coords to screen coords
        screen_x, screen_y = self.world_to_screen(x, y)
        screen_w = int(max(1, width * self.zoom))
        screen_h = int(max(1, height * self.zoom))
        x0 = int(screen_x)
        y0 = int(screen_y)
        x1 = x0 + screen_w
        y1 = y0 + screen_h

        # Clip to screen bounds
        if x1 <= 0 or y1 <= 0 or x0 >= self.width or y0 >= self.height:
            return

        # Clamp
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.width, x1)
        y1 = min(self.height, y1)

        # For thick outlines, use draw_rect for simplicity
        if thickness > 1:
            # Draw filled rectangles for each edge
            self.draw_rect(x, y, width, thickness / self.zoom, color)  # Top
            self.draw_rect(x, y + height - thickness / self.zoom, width, thickness / self.zoom, color)  # Bottom
            self.draw_rect(x, y, thickness / self.zoom, height, color)  # Left
            self.draw_rect(x + width - thickness / self.zoom, y, thickness / self.zoom, height, color)  # Right
            return

        # For thickness 1, draw individual pixel lines
        color_bytes = self._color_to_bytes(color)

        # Create a repeated array of color bytes for horizontal lines
        # We need to tile/repeat the color bytes to fill the entire width
        pixel_count = x1 - x0
        row_bytes = np.tile(color_bytes, pixel_count)

        # Top edge
        if y0 >= 0 and y0 < self.height and x0 < x1:
            start = x0 * self.pixel_size
            end = x1 * self.pixel_size
            self.buffer_np[y0, start:end] = row_bytes

        # Bottom edge (if different from top)
        if y1 - 1 != y0 and y1 - 1 >= 0 and y1 - 1 < self.height and x0 < x1:
            start = x0 * self.pixel_size
            end = x1 * self.pixel_size
            self.buffer_np[y1 - 1, start:end] = row_bytes

        # Left and right edges (skip if height is 1 pixel)
        if y1 - y0 > 1 and x0 < x1:
            # Left edge
            left_start = x0 * self.pixel_size
            left_end = (x0 + 1) * self.pixel_size
            if left_start < left_end and x0 < self.width:
                # Fill left edge for all interior rows
                for y_pos in range(y0 + 1, y1 - 1):
                    self.buffer_np[y_pos, left_start:left_end] = color_bytes

            # Right edge
            right_start = (x1 - 1) * self.pixel_size
            right_end = x1 * self.pixel_size
            if right_start < right_end and x1 - 1 >= 0 and x1 - 1 < self.width:
                # Fill right edge for all interior rows
                for y_pos in range(y0 + 1, y1 - 1):
                    self.buffer_np[y_pos, right_start:right_end] = color_bytes

    def draw_rect_screen(self, x, y, width, height, color: int):
        """Fill a rect in SCREEN-space pixels, ignoring camera/zoom.
        Same blending as draw_rect(), just without world_to_screen()."""
        x, y, width, height = int(x), int(y), int(width), int(height)
        if width <= 0 or height <= 0:
            return
        clip_x0 = max(0, -x)
        clip_y0 = max(0, -y)
        x, y = max(0, x), max(0, y)
        dw = min(width - clip_x0, self.width - x)
        dh = min(height - clip_y0, self.height - y)
        if dw <= 0 or dh <= 0:
            return
        dest_view = self.buffer_np[
            y:y + dh, x * self.pixel_size:(x + dw) * self.pixel_size,
        ].reshape(dh, dw, self.pixel_size)
        pixel_bytes = np.frombuffer(color.to_bytes(self.pixel_size, "little"), dtype=np.uint8)
        alpha = (color >> 24) & 0xFF if self.pixel_size == 4 else 255
        if alpha == 0:
            return
        if alpha == 255:
            dest_view[:, :, :] = pixel_bytes
            return
        a = np.uint16(alpha)
        src = pixel_bytes.astype(np.uint16)
        blended = (src * a + dest_view.astype(np.uint16) * (255 - a)) // 255
        blended[..., 3] = 255
        dest_view[:, :, :] = blended.astype(np.uint8)

    def draw_texture_region_screen(self, texture, src_x, src_y, src_w, src_h,
                                    dest_x, dest_y, dest_w=None, dest_h=None):
        """Blit a sub-rectangle of `texture` — in texture pixels,
        (src_x, src_y, src_w, src_h) — to SCREEN-space (dest_x, dest_y),
        ignoring camera/zoom. Same alpha blending as draw_sprite_screen(),
        just restricted to one cell of a larger sheet.

        Used for sprite-sheet fonts / tile atlases: pull a single glyph
        or tile out of a shared texture and draw it at its screen
        position. If dest_w/dest_h are given and differ from
        src_w/src_h, the cell is nearest-neighbor resampled to fit —
        otherwise it's drawn at its native size."""
        tex = self._get_texture_array(texture)
        tex_h, tex_w = tex.shape[0], tex.shape[1]

        src_x, src_y = int(src_x), int(src_y)
        src_w, src_h = int(src_w), int(src_h)

        # Clip the requested cell to the texture's own bounds (a
        # misconfigured charset/grid shouldn't read past the sheet).
        src_x0 = max(0, min(src_x, tex_w))
        src_y0 = max(0, min(src_y, tex_h))
        src_x1 = max(src_x0, min(src_x + src_w, tex_w))
        src_y1 = max(src_y0, min(src_y + src_h, tex_h))

        if src_x1 <= src_x0 or src_y1 <= src_y0:
            return

        region = tex[src_y0:src_y1, src_x0:src_x1]

        dest_w = int(dest_w) if dest_w is not None else region.shape[1]
        dest_h = int(dest_h) if dest_h is not None else region.shape[0]

        if dest_w != region.shape[1] or dest_h != region.shape[0]:
            rh, rw = region.shape[0], region.shape[1]
            if dest_w <= 0 or dest_h <= 0:
                return
            ys = (np.arange(dest_h) * rh // dest_h).clip(0, rh - 1)
            xs = (np.arange(dest_w) * rw // dest_w).clip(0, rw - 1)
            region = region[np.ix_(ys, xs)]

        self._blit_region(region, int(dest_x), int(dest_y), dest_w, dest_h, texture.bytes_per_pixel)

    def draw_sprite_screen(self, texture, x, y, width=None, height=None):
        """Draw a texture at SCREEN-space pixel (x, y), ignoring
        camera/zoom. No rotation support (not needed for UI) — reuses
        the same _blit() draw_sprite() already calls internally, which
        works in raw screen pixels once world_to_screen() is out of the
        way, so this is just draw_sprite() minus the camera transform."""
        dest_x, dest_y = int(x), int(y)
        if width is None or height is None:
            self._blit(texture, dest_x, dest_y)
        else:
            self._blit(texture, dest_x, dest_y, max(1, int(width)), max(1, int(height)))


# Global renderer system
Renderer = RendererSubsystem()
