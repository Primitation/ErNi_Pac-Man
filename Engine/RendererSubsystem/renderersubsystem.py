# renderersubsystem.py (complete)
import ctypes
import time
import numpy as np
from typing import Tuple, Optional, List, Callable, Any, Dict, Union, cast
from mlx import Mlx
import math
from .. import Assets
from .. import Log
from .. import Vector2


class RendererSubsystem:
    """Owns mlx_init(), the window and the render framebuffer."""

    def __init__(self) -> None:
        """Initialize renderer subsystem."""
        self.mlx: Optional[Mlx] = None
        self.mlx_ptr: Optional[Any] = None
        self.win_ptr: Optional[Any] = None

        self.framebuffer: Optional[Any] = None
        self.framebuffer_data: Optional[Any] = None
        self.framebuffer_ptr: Optional[int] = None

        self.width: int = 0
        self.height: int = 0
        self.title: str = "PacEngine"

        self.bpp: int = 0
        self.line_size: int = 0
        self.pixel_size: int = 0
        self.format: int = 0

        self.buffer: Optional[bytearray] = None
        self.buffer_size: int = 0
        self.buffer_np: Optional[np.ndarray] = None
        self._buffer_cbuf: Optional[Any] = None
        self._clear_view: Optional[np.ndarray] = None

        self.bake_buffer: Optional[bytearray] = None
        self.bake_np: Optional[np.ndarray] = None
        self._baked: bool = False
        self._last_bake_world: Optional[List[Any]] = None
        self._last_bake_background_color: int = 0xFF000000

        self.camera_position: Vector2 = Vector2(0.0, 0.0)
        self.zoom: float = 1.0

        self._bake_camera_position: Vector2 = Vector2(0.0, 0.0)
        self._bake_zoom: float = 1.0

        self._scale_cache: Dict[Tuple[int, int, int], np.ndarray] = {}
        self._resize_listeners: List[Callable[[Any, int, int], None]] = []

        self._logger = Log.get("renderer")
        self._frame_count: int = 0

        self._debug_draw_colliders: bool = False
        self._debug_collider_color_map: Optional[Any] = None
        self._draw_debug_banner: bool = False

    def init(self, width: int, height: int, title: str = "PacEngine") -> None:
        """Initialize. Call once, at startup, before anything else touches mlx.

        Args:
            width: width
            height: height
            title: title
        """
        self.width = width
        self.height = height
        self.title = title

        self.mlx = Mlx()
        if self.mlx is not None:
            self.mlx_ptr = self.mlx.mlx_init()
        else:
            self.mlx_ptr = None

        if self.mlx_ptr is None:
            raise RuntimeError("mlx_init() failed — no display available.")

        if self.mlx is None:
            raise RuntimeError("MLX not initialized")

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
        if self.framebuffer_data is not None:
            self.framebuffer_ptr = ctypes.addressof(self.framebuffer_data.obj)
        else:
            self.framebuffer_ptr = None
        self.buffer_size = self.height * self.line_size
        self.buffer = bytearray(self.buffer_size)

        if self.buffer is not None:
            self.buffer_np = np.frombuffer(self.buffer,
                                           dtype=np.uint8).reshape(
                self.height, self.line_size
            )

            self._buffer_cbuf = (ctypes.c_char * self.buffer_size).from_buffer(
                self.buffer
            )

        pixel_dtype = {1: np.uint8, 2: np.uint16, 4: np.uint32}.get(
            self.pixel_size
        )
        if pixel_dtype is not None and self.line_size % self.pixel_size == 0:
            if self.buffer_np is not None:
                self._clear_view = self.buffer_np.view(dtype=pixel_dtype)
        else:
            self._clear_view = None

        self._logger.debug(
            f"Framebuffer info: bpp={self.bpp}, line_size={self.line_size}, "
            f"format={self.format}, pixel_size={self.pixel_size}"
        )

        if self.mlx is not None:
            Assets.init(self.mlx, self.mlx_ptr)

        if self.win_ptr is not None and self.mlx is not None:
            self.mlx.mlx_hook(
                self.win_ptr, 33, 0, self._close_window, self
            )

        self._logger.info(f'Window created: {width}x{height} "{title}"')

        self.clear(0xFF000000)

    def set_camera(self, position: Vector2) -> None:
        """Move the camera. position is the world point centered on screen.

        Args:
            position: position
        """
        self.camera_position = position

    def move_camera(self, dx: float, dy: float) -> None:
        """Pan the camera by (dx, dy) in world units.

        Args:
            dx: dx
            dy: dy
        """
        self.camera_position = Vector2(
            self.camera_position.x + dx, self.camera_position.y + dy
        )

    def set_zoom(self, zoom: float) -> None:
        """Set the zoom level. 1.0 = no zoom.

        Args:
            zoom: zoom
        """
        if zoom <= 0:
            raise ValueError("zoom must be > 0")
        self.zoom = zoom

    def zoom_by(self, factor: float) -> None:
        """Multiply the current zoom by factor.

        Args:
            factor: factor
        """
        self.set_zoom(self.zoom * factor)

    def _camera_matches_bake(self) -> bool:
        """Whether the live camera matches the baked background.

        Returns:
            Returns if camera is baked.
        """
        return (
            abs(self.camera_position.x - self._bake_camera_position.x) < 1e-6
            and abs(self.camera_position.y - self._bake_camera_position.y)
            < 1e-6
            and abs(self.zoom - self._bake_zoom) < 1e-6
        )

    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Converts world-space coordinates
         to framebuffer pixel coordinates.

        Args:
            x: x
            y: y

        Returns:
            Returns framebuffer pixel coordinates
        """

        screen_x = (x - self.camera_position.x) * self.zoom + self.width / 2.0
        screen_y = (y - self.camera_position.y) * self.zoom + self.height / 2.0
        return screen_x, screen_y

    def _get_component_position(self, component: Any) -> Tuple[float, float]:
        """Get the world position of a component.

        Args:
            component: component

        Returns:
            Returns the world position of a component.
        """
        if hasattr(component, 'get_world_position'):
            pos = component.get_world_position()
            return (pos.x, pos.y) if hasattr(pos, 'x') else (float(pos[0]),
                                                             float(pos[1]))
        actor = getattr(component, 'actor', None)
        if actor is not None:
            return (actor.position.x, actor.position.y)
        return (0.0, 0.0)

    def _sprite_for(self, actor: Any) -> Optional[List[Any]]:
        """Find the actor's current sprite by checking its components.

        Args:
            actor: actor

        Returns:
            Returns current sprite by checking its components.
        """
        components = getattr(actor, "components", None)
        if not components:
            return None

        out_components: List[Any] = []
        for component in components:
            if hasattr(component, "sprite"):
                out_components.append(component)
        return out_components

    def _fill_solid(self, color: int) -> None:
        """One-shot solid color fill.

        Args:
            color: color
        """
        if self.buffer_np is None:
            return

        if self._clear_view is not None:
            pixel_value = color & ((1 << (self.pixel_size * 8)) - 1)
            self._clear_view[:, :self.width] = pixel_value
            return

        pixel_bytes = np.frombuffer(
            color.to_bytes(self.pixel_size, "little"), dtype=np.uint8
        )
        row = np.tile(pixel_bytes, self.width)
        if len(row) < self.line_size:
            row = np.concatenate(
                [row, np.zeros(self.line_size - len(row), dtype=np.uint8)]
            )
        self.buffer_np[:, :] = row

    def clear(self, color: int = 0xFF000000) -> None:
        """Clears the framebuffer before drawing the next frame.

        Args:
            color: color
        """
        if self.buffer_np is None or self.bake_np is None:
            self._fill_solid(color)
            return

        if self._baked and self._camera_matches_bake():
            self.buffer_np[:, :] = self.bake_np
            return

        self._fill_solid(color)

    def bake(self, world: List[Any], background_color: int = 0xFF000000,
             max_wait_ticks: int = 300) -> None:
        """Pre-renders every static actor once into
         an internal background buffer.

        Args:
            world: world
            background_color: background color
            max_wait_ticks: max wait ticks
        """
        self._last_bake_world = world
        self._last_bake_background_color = background_color

        self._baked = False
        self._fill_solid(background_color)

        static_actors = [a for a in world if getattr(a, "static", False)]

        def _sprites_pending() -> bool:
            """Returns if sprite pending.

            Args:
                _sprites_pending:  sprites pending

            Returns:
                Returns if sprite pending.
            """
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
            # A tight loop here only spins the interpreter — it doesn't
            # give the background loader thread any real wall-clock time
            # to actually read/decode textures from disk. On a cold cache
            # (typically the very first level of a run, before anything
            # has been loaded yet) that starves the loader thread and the
            # wait loop can burn through all max_wait_ticks in a few
            # milliseconds without a single sprite finishing, so we sleep
            # a little each tick to yield real time to the loader thread.
            time.sleep(0.001)
            ticks += 1

        if ticks >= max_wait_ticks and _sprites_pending():
            self._logger.warning(
                "bake(): some static actor sprite(s) hadn't finished "
                f"loading after {max_wait_ticks} Assets.update() tick(s); "
                "baking anyway — those actors may be missing from the "
                "baked background."
            )

        draw_list: List[Tuple[Any, Any]] = []
        for actor in static_actors:
            components = self._sprite_for(actor)
            if components is None:
                continue
            for component in components:
                if getattr(component, 'sprite', None) is None:
                    continue
                draw_list.append((actor, component))

        draw_list.sort(key=lambda pair: getattr(pair[1], 'render_layer', 0))

        if static_actors and not draw_list:
            self._logger.error(
                "bake(): %d static actor(s) were present but NONE had a "
                "loaded sprite — the baked background will be solid "
                "background_color=0x%08X (this is the 'black bake' bug: "
                "the loader thread never got real time to load assets "
                "before bake() ran; make sure something has primed the "
                "sprite components — e.g. an Actors.update(0) call — "
                "before Renderer.bake() is invoked).",
                len(static_actors), background_color,
            )

        for actor, component in draw_list:
            sprite = component.sprite
            if sprite is None:
                continue
            try:
                rotation = getattr(actor, 'rotation', 0.0)
                component_rotation = getattr(component, 'local_rotation', 0.0)
                pivot = getattr(actor, 'pivot', (0.5, 0.5))
                position = self._get_component_position(component)
                pos = type('Position', (), {'x': position[0],
                           'y': position[1]})()
                get_world_scale = getattr(component, 'get_world_scale', None)
                scale = get_world_scale() if get_world_scale is not None \
                    else actor.scale
                self.draw_sprite(sprite, pos, scale, rotation
                                 + component_rotation, pivot)
            except Exception:
                self._logger.exception(f"Failed to bake actor {actor!r}")

        if self.buffer is None or self.buffer_np is None:
            return

        if self.bake_buffer is None:
            self.bake_buffer = bytearray(self.buffer_size)
            if self.bake_buffer is not None:
                self.bake_np = np.frombuffer(self.bake_buffer,
                                             dtype=np.uint8).reshape(
                    self.height, self.line_size
                )

        if self.bake_np is not None:
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

    def unbake(self) -> None:
        """Reverts to a plain solid-color clear() instead
         of the baked background."""
        self._baked = False

    def put_pixel(self, x: float, y: float, color: int) -> None:
        """Writes a pixel into the framebuffer.

        Args:
            x: x
            y: y
            color: color
        """
        if self.buffer_np is None:
            return

        screen_x, screen_y = self.world_to_screen(x, y)
        x_int, y_int = int(screen_x), int(screen_y)

        if x_int < 0 or y_int < 0 or x_int >= self.width \
                or y_int >= self.height:
            return

        offset = x_int * self.pixel_size
        self.buffer_np[y_int, offset:offset + self.pixel_size] = np.frombuffer(
            color.to_bytes(self.pixel_size, "little"), dtype=np.uint8
        )

    def draw_rect(self, x: float, y: float, width: float, height: float,
                  color: int) -> None:
        """Fill an axis-aligned rect with a solid color.

        Args:
            x: x
            y: y
            width: width
            height: height
            color: color
        """
        if self.buffer_np is None:
            return

        screen_x, screen_y = self.world_to_screen(x, y)
        x_int, y_int = int(screen_x), int(screen_y)
        width_int = int(width * self.zoom)
        height_int = int(height * self.zoom)

        if width_int <= 0 or height_int <= 0:
            return

        clip_x0 = max(0, -x_int)
        clip_y0 = max(0, -y_int)
        x_int = max(0, x_int)
        y_int = max(0, y_int)

        dw = min(width_int - clip_x0, self.width - x_int)
        dh = min(height_int - clip_y0, self.height - y_int)

        if dw <= 0 or dh <= 0:
            return

        dest_view = self.buffer_np[
            y_int:y_int + dh,
            x_int * self.pixel_size: (x_int + dw) * self.pixel_size,
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

    def draw_sprite(self, texture: Any, position: Any,
                    scale: Union[float, Any],
                    rotation: float = 0.0,
                    pivot: Tuple[float, float] = (0.5, 0.5)) -> None:
        """Draws a texture into the framebuffer with scaling and rotation.

        Args:
            texture: texture
            position: position
            scale: scale
            rotation: rotation
            pivot: pivot
        """
        if hasattr(scale, 'x') and hasattr(scale, 'y'):
            scale_x = scale.x
            scale_y = scale.y
        else:
            scale_x = float(scale)
            scale_y = float(scale)

        screen_x, screen_y = self.world_to_screen(position.x, position.y)
        dest_x = int(screen_x)
        dest_y = int(screen_y)

        scaled_width = max(1, int(texture.width * scale_x * self.zoom))
        scaled_height = max(1, int(texture.height * scale_y * self.zoom))

        if scaled_width <= 0 or scaled_height <= 0:
            return

        if abs(rotation) > 0.001:
            angle_rad = math.radians(rotation)
            cos_a = abs(math.cos(angle_rad))
            sin_a = abs(math.sin(angle_rad))

            out_width = max(1, int(round(scaled_width * cos_a + scaled_height
                                         * sin_a)))
            out_height = max(1, int(round(scaled_width * sin_a + scaled_height
                                          * cos_a)))

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
    def _get_texture_array(texture: Any) -> np.ndarray:
        """Returns a numpy (H, W, bpp) view over texture.data.

        Args:
            texture: texture

        Returns:
            Returns a numpy (H, W, bpp) view over texture.data.
        """
        cached = getattr(texture, "_np_cache", None)
        if cached is not None:
            return cast(np.ndarray, cached)

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

    def _blit(self, texture: Any, dest_x: int, dest_y: int,
              scaled_width: Optional[int] = None,
              scaled_height: Optional[int] = None) -> None:
        """Vectorized blit.

        Args:
            texture: texture
            dest_x: dest x
            dest_y: dest y
            scaled_width: scaled width
            scaled_height: scaled height
        """
        if self.buffer_np is None:
            return

        tex = self._get_texture_array(texture)

        if scaled_width is None:
            region = tex
        else:
            # Ensure scaled_width and scaled_height are not None
            sw = scaled_width
            sh = scaled_height if scaled_height is not None else scaled_width
            cache_key = (id(texture), sw, sh)
            region = self._scale_cache.get(cache_key)

            if region is None:
                src_ys = (np.arange(sh) * texture.height // sh)
                src_xs = (np.arange(sw) * texture.width // sw)
                src_ys = src_ys.clip(0, texture.height - 1)
                src_xs = src_xs.clip(0, texture.width - 1)
                region = tex[np.ix_(src_ys, src_xs)]
                self._scale_cache[cache_key] = region

        src_h, src_w = region.shape[0], region.shape[1]

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
            return

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

            dest_view[~transparent_mask] = \
                blended[~transparent_mask].astype(np.uint8)
            dest_view[opaque_mask] = region[opaque_mask]
        else:
            dest_view[:, :, :] = region[:, :, :self.pixel_size]

    def _blit_rotated(self, texture: Any, dest_x: int, dest_y: int,
                      angle_degrees: float, pivot_x: float = 0.5,
                      pivot_y: float = 0.5, local_width: Optional[int] = None,
                      local_height: Optional[int] = None,
                      out_width: Optional[int] = None,
                      out_height: Optional[int] = None) -> None:
        """Vectorized blit with rotation support.

        Args:
            texture: texture
            dest_x: dest x
            dest_y: dest y
            angle_degrees: angle degrees
            pivot_x: pivot x
            pivot_y: pivot y
            local_width: local width
            local_height: local height
            out_width: out width
            out_height: out height
        """
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

        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        y_coords, x_coords = np.mgrid[0:out_height, 0:out_width]

        out_pivot_x = pivot_x * out_width
        out_pivot_y = pivot_y * out_height
        local_pivot_x = pivot_x * local_width
        local_pivot_y = pivot_y * local_height

        x_rel = x_coords - out_pivot_x
        y_rel = y_coords - out_pivot_y

        local_x = x_rel * cos_a + y_rel * sin_a + local_pivot_x
        local_y = -x_rel * sin_a + y_rel * cos_a + local_pivot_y

        src_x = local_x * (src_w / local_width)
        src_y = local_y * (src_h / local_height)

        src_x = np.clip(src_x, 0, src_w - 1).astype(np.int32)
        src_y = np.clip(src_y, 0, src_h - 1).astype(np.int32)

        region = tex[src_y, src_x]

        self._blit_region(region, dest_x, dest_y, out_width, out_height,
                          texture.bytes_per_pixel)

    def _blit_region(self, region: np.ndarray, dest_x: int, dest_y: int,
                     region_w: int, region_h: int, bpp: int) -> None:
        """Internal method to blit a pre-processed region.

        Args:
            region: region
            dest_x: dest x
            dest_y: dest y
            region_w: region w
            region_h: region h
            bpp: bpp
        """
        if self.buffer_np is None:
            return

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

            dest_view[~transparent_mask] = \
                blended[~transparent_mask].astype(np.uint8)
            dest_view[opaque_mask] = region[opaque_mask]
        else:
            dest_view[:, :, :] = region[:, :, :self.pixel_size]

    def render_draw(self, world: List[Any]) -> None:
        """Draw all actors into the framebuffer (no presentation).

        Args:
            world: world
        """

        if self.win_ptr is None:
            raise RuntimeError("RendererSubsystem.render_draw()"
                               " called before .init().")

        self.clear(0xFFAAAAAA)

        baked_valid = self._baked and self._camera_matches_bake()

        draw_list: List[Tuple[Any, Any]] = []
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
                pos = type('Position', (), {'x': position[0],
                           'y': position[1]})()
                get_world_scale = getattr(component, 'get_world_scale', None)
                scale = get_world_scale() if get_world_scale is not None \
                    else actor.scale
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
        """Render level banner."""
        from assets.code.actors.player import Player

        if Player.current_player is None:
            return

        try:
            from .. import Actors
            text = (f"Score  {Player.current_player.score_info.score}   "
                    f"Lives  {Player.current_player.lives}   "
                    f"Level  {Player.current_level}    "
                    f"Time  {max(0, round(Actors.remaining_time, 1))}")
            if self.mlx is not None and self.mlx_ptr is not None \
                    and self.win_ptr is not None:
                self.mlx.mlx_string_put(
                    self.mlx_ptr, self.win_ptr, 20,
                    self.height - 50,
                    0x000000FF,
                    text)
        except Exception:
            self._logger.exception("Failed to draw level banner")

    def render_present(self) -> None:
        """Present the framebuffer to the screen."""
        if self.win_ptr is None:
            raise RuntimeError("RendererSubsystem.render_present()"
                               " called before .init().")

        if self.framebuffer_ptr is None or self._buffer_cbuf is None:
            return

        ctypes.memmove(
            self.framebuffer_ptr,
            ctypes.addressof(self._buffer_cbuf),
            self.buffer_size
        )

        if self.mlx is not None and self.mlx_ptr is not None:
            self.mlx.mlx_put_image_to_window(
                self.mlx_ptr,
                self.win_ptr,
                self.framebuffer,
                0,
                0,
            )
        if self._draw_debug_banner:
            self.render_level_banner()

    def render(self, world: List[Any]) -> None:
        """Legacy method - draws and presents in one call.

        Args:
            world: world
        """
        self.render_draw(world)
        self.render_present()

    def hook_loop(self, callback: Callable[..., Any],
                  param: Any = None) -> None:
        """Registers callback to run once per mlx event-loop tick.

        Args:
            callback: callback
            param: param
        """
        if self.mlx is not None and self.mlx_ptr is not None:
            self.mlx.mlx_loop_hook(self.mlx_ptr, callback, param)

    def hook_close(self, callback: Callable[..., Any],
                   param: Any = None) -> None:
        """Registers a custom close callback.

        Args:
            callback: callback
            param: param
        """
        if self.mlx is not None and self.win_ptr is not None:
            self.mlx.mlx_hook(self.win_ptr, 33, 0, callback, param)

    def _close_window(self, param: Any) -> None:
        """Default window close handler.

        Args:
            param: param
        """
        self._logger.info("Window close requested.")
        if self.mlx is not None and self.mlx_ptr is not None:
            self.mlx.mlx_loop_exit(self.mlx_ptr)

    def loop(self) -> None:
        """Starts the mlx event loop."""
        self._logger.info("Starting MLX event loop...")
        if self.mlx is not None and self.mlx_ptr is not None:
            result = self.mlx.mlx_loop(self.mlx_ptr)
            self._logger.info(f"MLX event loop exited with: {result}")

    def close(self) -> None:
        """Destroys the window."""
        if self.win_ptr is not None and self.mlx is not None \
                and self.mlx_ptr is not None:
            self.mlx.mlx_destroy_window(self.mlx_ptr, self.win_ptr)
            self.win_ptr = None

    def close_request(self) -> None:
        """Request the MLX loop to exit."""
        self._logger.info("Quit requested.")
        if self.mlx is not None and self.mlx_ptr is not None:
            self.mlx.mlx_loop_exit(self.mlx_ptr)

    def on_resize(self, callback: Callable[[Any, int, int], None]) -> None:
        """Register a callback to be notified after resize().

        Args:
            callback: callback
        """
        self._resize_listeners.append(callback)

    def resize(self, width: int, height: int,
               title: Optional[str] = None) -> None:
        """Resize the window and framebuffer to a new width/height.

        Args:
            width: width
            height: height
            title: title
        """
        if self.win_ptr is None:
            raise RuntimeError("RendererSubsystem.resize()"
                               " called before .init().")

        if self.mlx is None or self.mlx_ptr is None:
            raise RuntimeError("MLX not initialized")

        if title is None:
            title = self.title

        self.close()

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
        if self.framebuffer_data is not None:
            self.framebuffer_ptr = ctypes.addressof(self.framebuffer_data.obj)
        else:
            self.framebuffer_ptr = None
        self.buffer_size = self.height * self.line_size
        self.buffer = bytearray(self.buffer_size)

        if self.buffer is not None:
            self.buffer_np = np.frombuffer(self.buffer,
                                           dtype=np.uint8).reshape(
                self.height, self.line_size
            )
            self._buffer_cbuf = (ctypes.c_char * self.buffer_size).from_buffer(
                self.buffer
            )

        pixel_dtype = {1: np.uint8, 2: np.uint16, 4: np.uint32}.get(
            self.pixel_size
        )
        if pixel_dtype is not None and self.line_size % self.pixel_size == 0:
            if self.buffer_np is not None:
                self._clear_view = self.buffer_np.view(dtype=pixel_dtype)
        else:
            self._clear_view = None

        self._baked = False
        self.bake_buffer = None
        self.bake_np = None

        if self._last_bake_world is not None:
            try:
                self.bake(self._last_bake_world,
                          self._last_bake_background_color)
            except Exception:
                self._logger.exception("Failed to rebake "
                                       "background after resize")

        if self.win_ptr is not None:
            self.mlx.mlx_hook(
                self.win_ptr, 33, 0, self._close_window, self
            )

        self._logger.info(f'Window resized: {width}x{height} "{title}"')

        self.clear(0xFF000000)

        for listener in self._resize_listeners:
            try:
                listener(self.win_ptr, width, height)
            except Exception:
                self._logger.exception("resize listener failed")

    def _color_to_bytes(self, color: int) -> np.ndarray:
        """Convert a 0xAARRGGBB color to a numpy array of bytes.

        Args:
            color: color

        Returns:
            Returns color to a numpy array of bytes.
        """
        return np.frombuffer(
            color.to_bytes(self.pixel_size, "little"), dtype=np.uint8
        )

    def draw_rect_outline(self, x: float, y: float, width: float,
                          height: float, color: int = 0xFFFF0000,
                          thickness: int = 1) -> None:
        """Draw a rectangle outline in WORLD-space.

        Args:
            x: x
            y: y
            width: width
            height: height
            color: color
            thickness: thickness
        """

        if self.buffer_np is None:
            return

        if width <= 0 or height <= 0:
            return

        screen_x, screen_y = self.world_to_screen(x, y)
        screen_w = int(max(1, width * self.zoom))
        screen_h = int(max(1, height * self.zoom))
        x0 = int(screen_x)
        y0 = int(screen_y)
        x1 = x0 + screen_w
        y1 = y0 + screen_h

        if x1 <= 0 or y1 <= 0 or x0 >= self.width or y0 >= self.height:
            return

        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.width, x1)
        y1 = min(self.height, y1)

        if thickness > 1:
            self.draw_rect(x, y, width, thickness / self.zoom, color)
            self.draw_rect(x, y + height - thickness / self.zoom,
                           width, thickness / self.zoom, color)
            self.draw_rect(x, y, thickness / self.zoom, height, color)
            self.draw_rect(x + width - thickness / self.zoom, y,
                           thickness / self.zoom, height, color)
            return

        color_bytes = self._color_to_bytes(color)
        pixel_count = x1 - x0
        row_bytes = np.tile(color_bytes, pixel_count)

        if y0 >= 0 and y0 < self.height and x0 < x1:
            start = x0 * self.pixel_size
            end = x1 * self.pixel_size
            self.buffer_np[y0, start:end] = row_bytes

        if y1 - 1 != y0 and y1 - 1 >= 0 and y1 - 1 < self.height and x0 < x1:
            start = x0 * self.pixel_size
            end = x1 * self.pixel_size
            self.buffer_np[y1 - 1, start:end] = row_bytes

        if y1 - y0 > 1 and x0 < x1:
            left_start = x0 * self.pixel_size
            left_end = (x0 + 1) * self.pixel_size
            if left_start < left_end and x0 < self.width:
                for y_pos in range(y0 + 1, y1 - 1):
                    self.buffer_np[y_pos, left_start:left_end] = color_bytes

            right_start = (x1 - 1) * self.pixel_size
            right_end = x1 * self.pixel_size
            if right_start < right_end and x1 - 1 >= 0 and x1 - 1 < self.width:
                for y_pos in range(y0 + 1, y1 - 1):
                    self.buffer_np[y_pos, right_start:right_end] = color_bytes

    def draw_rect_screen(self, x: int, y: int, width: int, height: int,
                         color: int) -> None:
        """Fill a rect in SCREEN-space pixels.

        Args:
            x: x
            y: y
            width: width
            height: height
            color: color
        """
        if self.buffer_np is None:
            return

        x_int, y_int, width_int, height_int = int(x), int(y), \
            int(width), int(height)
        if width_int <= 0 or height_int <= 0:
            return

        clip_x0 = max(0, -x_int)
        clip_y0 = max(0, -y_int)
        x_int, y_int = max(0, x_int), max(0, y_int)
        dw = min(width_int - clip_x0, self.width - x_int)
        dh = min(height_int - clip_y0, self.height - y_int)

        if dw <= 0 or dh <= 0:
            return

        dest_view = self.buffer_np[
            y_int:y_int + dh,
            x_int * self.pixel_size:(x_int + dw) * self.pixel_size,
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

    def draw_texture_region_screen(self, texture: Any, src_x: int, src_y: int,
                                   src_w: int, src_h: int, dest_x: int,
                                   dest_y: int, dest_w: Optional[int] = None,
                                   dest_h: Optional[int] = None) -> None:
        """Blit a sub-rectangle of texture to SCREEN-space.

        Args:
            texture: texture
            src_x: src x
            src_y: src y
            src_w: src w
            src_h: src h
            dest_x: dest x
            dest_y: dest y
            dest_w: dest w
            dest_h: dest h
        """
        tex = self._get_texture_array(texture)
        tex_h, tex_w = tex.shape[0], tex.shape[1]

        src_x0 = max(0, min(src_x, tex_w))
        src_y0 = max(0, min(src_y, tex_h))
        src_x1 = max(src_x0, min(src_x + src_w, tex_w))
        src_y1 = max(src_y0, min(src_y + src_h, tex_h))

        if src_x1 <= src_x0 or src_y1 <= src_y0:
            return

        region = tex[src_y0:src_y1, src_x0:src_x1]

        dest_w_int = int(dest_w) if dest_w is not None else region.shape[1]
        dest_h_int = int(dest_h) if dest_h is not None else region.shape[0]

        if dest_w_int != region.shape[1] or dest_h_int != region.shape[0]:
            rh, rw = region.shape[0], region.shape[1]
            if dest_w_int <= 0 or dest_h_int <= 0:
                return
            ys = (np.arange(dest_h_int) * rh // dest_h_int).clip(0, rh - 1)
            xs = (np.arange(dest_w_int) * rw // dest_w_int).clip(0, rw - 1)
            region = region[np.ix_(ys, xs)]

        self._blit_region(region, int(dest_x), int(dest_y),
                          dest_w_int, dest_h_int,
                          texture.bytes_per_pixel)

    def draw_sprite_screen(self, texture: Any, x: int, y: int,
                           width: Optional[int] = None,
                           height: Optional[int] = None) -> None:
        """Draw a texture at SCREEN-space pixel (x, y).

        Args:
            texture: texture
            x: x
            y: y
            width: width
            height: height
        """
        dest_x, dest_y = int(x), int(y)
        if width is None or height is None:
            self._blit(texture, dest_x, dest_y)
        else:
            self._blit(texture, dest_x, dest_y, max(1, int(width)),
                       max(1, int(height)))


Renderer = RendererSubsystem()
