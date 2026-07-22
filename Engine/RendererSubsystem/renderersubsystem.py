import ctypes
from mlx import Mlx
from .. import Assets
from .. import Log


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

        self.bpp = 0
        self.line_size = 0
        self.pixel_size = 0
        self.format = 0
        
        self.buffer = None
        self.buffer_size = 0

        self._logger = Log.get("renderer")
        self._frame_count = 0

    def init(self, width: int, height: int, title: str = "PrimiEngine"):
        """Call once, at startup, before anything else touches mlx."""
        
        self.width = width
        self.height = height

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

    def clear(self, color: int = 0xFF000000):
        """Clears the framebuffer before drawing the next frame."""
        
        pixel_bytes = color.to_bytes(self.pixel_size, "little")
        
        # Create a row pattern
        row = pixel_bytes * self.width
        if len(row) < self.line_size:
            row = row + b'\x00' * (self.line_size - len(row))
        
        # Fill the entire buffer
        for y in range(self.height):
            offset = y * self.line_size
            self.buffer[offset:offset + self.line_size] = row

    def put_pixel(self, x: int, y: int, color: int):
        """Writes a pixel directly into the framebuffer."""
        
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return

        offset = y * self.line_size + x * self.pixel_size
        self.buffer[offset:offset + self.pixel_size] = color.to_bytes(
            self.pixel_size, "little"
        )

    def draw_sprite(self, texture, position, scale):
        """Draws a texture into the framebuffer with scaling support."""
        
        # Extract scale components
        if hasattr(scale, 'x') and hasattr(scale, 'y'):
            scale_x = scale.x
            scale_y = scale.y
        else:
            scale_x = float(scale)
            scale_y = float(scale)
        
        dest_x = int(position.x)
        dest_y = int(position.y)
        
        # Calculate scaled dimensions
        scaled_width = int(texture.width * scale_x)
        scaled_height = int(texture.height * scale_y)
        
        # If scale is 1.0, do direct copy (optimization)
        if scale_x == 1.0 and scale_y == 1.0:
            self._draw_sprite_direct(texture, dest_x, dest_y)
            return
        
        # For each pixel in the scaled sprite
        for dest_y_offset in range(scaled_height):
            screen_y = dest_y + dest_y_offset
            if screen_y < 0 or screen_y >= self.height:
                continue
            
            # Calculate source Y
            src_y = (dest_y_offset / scaled_height) * texture.height
            src_y_int = int(src_y)
            
            if src_y_int >= texture.height:
                continue
            
            dest_row_start = screen_y * self.line_size + dest_x * self.pixel_size
            
            for dest_x_offset in range(scaled_width):
                screen_x = dest_x + dest_x_offset
                if screen_x < 0 or screen_x >= self.width:
                    continue
                
                # Calculate source X
                src_x = (dest_x_offset / scaled_width) * texture.width
                src_x_int = int(src_x)
                
                if src_x_int >= texture.width:
                    continue
                
                src_offset = src_y_int * texture.line_size + src_x_int * texture.bytes_per_pixel
                dest_offset = dest_row_start + dest_x_offset * self.pixel_size
                
                # Handle pixel with alpha (BGRA format)
                if texture.bytes_per_pixel == 4:
                    # BGRA format: B, G, R, A
                    blue = texture.data[src_offset]
                    green = texture.data[src_offset + 1]
                    red = texture.data[src_offset + 2]
                    alpha = texture.data[src_offset + 3]
                    
                    # Fully transparent - skip
                    if alpha == 0:
                        continue
                    
                    # Fully opaque - overwrite completely
                    if alpha == 255:
                        self.buffer[dest_offset:dest_offset + 4] = \
                            texture.data[src_offset:src_offset + 4]
                    else:
                        # Semi-transparent - alpha blend with background
                        # Background is also BGRA
                        dest_b = self.buffer[dest_offset]
                        dest_g = self.buffer[dest_offset + 1]
                        dest_r = self.buffer[dest_offset + 2]
                        dest_a = self.buffer[dest_offset + 3]  # Background alpha (should be 255)
                        
                        alpha_factor = alpha / 255.0
                        new_b = int(blue * alpha_factor + dest_b * (1 - alpha_factor))
                        new_g = int(green * alpha_factor + dest_g * (1 - alpha_factor))
                        new_r = int(red * alpha_factor + dest_r * (1 - alpha_factor))
                        
                        # Alpha stays 255 (fully opaque background)
                        self.buffer[dest_offset:dest_offset + 4] = \
                            bytes([new_b, new_g, new_r, 255])
                else:
                    # No alpha channel - just copy
                    self.buffer[dest_offset:dest_offset + texture.bytes_per_pixel] = \
                        texture.data[src_offset:src_offset + texture.bytes_per_pixel]

    def _draw_sprite_direct(self, texture, dest_x, dest_y):
        """Optimized direct sprite drawing (no scaling)."""
        
        for y in range(texture.height):
            screen_y = dest_y + y
            if screen_y < 0 or screen_y >= self.height:
                continue
                
            src_row_start = y * texture.line_size
            dest_row_start = screen_y * self.line_size + dest_x * self.pixel_size
            
            for x in range(texture.width):
                screen_x = dest_x + x
                if screen_x < 0 or screen_x >= self.width:
                    continue
                    
                src_offset = src_row_start + x * texture.bytes_per_pixel
                dest_offset = dest_row_start + x * self.pixel_size
                
                # Handle pixel with alpha (BGRA format)
                if texture.bytes_per_pixel == 4:
                    # BGRA format: B, G, R, A
                    blue = texture.data[src_offset]
                    green = texture.data[src_offset + 1]
                    red = texture.data[src_offset + 2]
                    alpha = texture.data[src_offset + 3]
                    
                    # Fully transparent - skip
                    if alpha == 0:
                        continue
                    
                    # Fully opaque - overwrite completely
                    if alpha == 255:
                        self.buffer[dest_offset:dest_offset + 4] = \
                            texture.data[src_offset:src_offset + 4]
                    else:
                        # Semi-transparent - alpha blend with background
                        # Background is also BGRA
                        dest_b = self.buffer[dest_offset]
                        dest_g = self.buffer[dest_offset + 1]
                        dest_r = self.buffer[dest_offset + 2]
                        
                        alpha_factor = alpha / 255.0
                        new_b = int(blue * alpha_factor + dest_b * (1 - alpha_factor))
                        new_g = int(green * alpha_factor + dest_g * (1 - alpha_factor))
                        new_r = int(red * alpha_factor + dest_r * (1 - alpha_factor))
                        
                        # Alpha stays 255 (fully opaque background)
                        self.buffer[dest_offset:dest_offset + 4] = \
                            bytes([new_b, new_g, new_r, 255])
                else:
                    # No alpha channel - just copy
                    self.buffer[dest_offset:dest_offset + texture.bytes_per_pixel] = \
                        texture.data[src_offset:src_offset + texture.bytes_per_pixel]

    def render(self, world):
        """Render one frame."""
        
        if self.win_ptr is None:
            raise RuntimeError("RendererSubsystem.render() called before .init().")

        # Clear with FULLY OPAQUE BLACK
        self.clear(0xFFAAAAAA)

        # Draw all actors in order (later actors will overwrite earlier ones)
        for actor in world:
            sprite = actor.sprite
            if sprite is None:
                continue

            try:
                self.draw_sprite(
                    sprite,
                    actor.position,
                    actor.scale,
                )
            except Exception:
                self._logger.exception(f"Failed to draw actor {actor!r}")

        # Copy our buffer to the framebuffer
        ctypes.memmove(
            self.framebuffer_ptr,
            ctypes.addressof(ctypes.c_char.from_buffer(self.buffer)),
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


# Global renderer system
Renderer = RendererSubsystem()
