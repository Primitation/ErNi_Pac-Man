# loader.py
import threading
import queue
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Any, Dict, Set, Tuple


from .. import Log


class AssetLoader(ABC):
    """One loader per asset type."""

    @abstractmethod
    def can_load(self, path: Any) -> bool:
        pass

    @abstractmethod
    def load(self, path: Any) -> Any:
        """Runs on the WORKER thread."""
        pass

    def finalize(self, raw: Any) -> Any:
        """Runs on the MAIN thread."""
        return raw

    def placeholder(self) -> Any:
        """Fallback asset when load()/finalize() raises."""
        return None


class MlxContext:
    """Holds the single Mlx() instance + mlx_ptr."""

    def __init__(self) -> None:
        self.mlx: Optional[Any] = None
        self.mlx_ptr: Optional[Any] = None

    def bind(self, mlx: Any, mlx_ptr: Any) -> None:
        self.mlx = mlx
        self.mlx_ptr = mlx_ptr

    @property
    def ready(self) -> bool:
        return self.mlx is not None and self.mlx_ptr is not None


Context = MlxContext()


class Texture:
    """Wraps a loaded mlx image with its dimensions."""

    def __init__(
        self,
        img: Any,
        width: int,
        height: int,
        data: Any,
        bpp: int,
        line_size: int,
        endian: int,
    ) -> None:
        self.img = img
        self.width = width
        self.height = height
        self.data = data
        self.bpp = bpp
        self.line_size = line_size
        self.endian = endian
        self.bytes_per_pixel = bpp // 8


class TextureLoader(AssetLoader):
    """mlx decodes PNG and XPM formats."""

    def can_load(self, path: Any) -> bool:
        return isinstance(path, str) \
            and path.lower().endswith((".png", ".xpm"))

    def load(self, path: Any) -> Any:
        return path

    def finalize(self, path: Any) -> Optional[Texture]:
        if not Context.ready:
            raise RuntimeError(
                "MLX asset loading used before Context.bind(mlx, mlx_ptr) "
                "was called — call Assets.init(mlx, mlx_ptr) right after "
                "mlx_init()."
            )

        mlx = Context.mlx
        mlx_ptr = Context.mlx_ptr

        if mlx is None or mlx_ptr is None:
            raise RuntimeError("MLX context not properly initialized")

        if path.lower().endswith(".xpm"):
            img, width, height = mlx.mlx_xpm_file_to_image(mlx_ptr, path)
        else:
            img, width, height = mlx.mlx_png_file_to_image(mlx_ptr, path)

        if img is None:
            raise ValueError(f"mlx failed to load image: {path}")

        data, bpp, line_size, endian = mlx.mlx_get_data_addr(img)

        return Texture(img, width, height, data, bpp, line_size, endian)

    def placeholder(self) -> Optional[Texture]:
        """Classic magenta/black 'missing texture' checkerboard."""
        if not Context.ready:
            return None

        mlx = Context.mlx
        mlx_ptr = Context.mlx_ptr

        if mlx is None or mlx_ptr is None:
            return None

        size = 64
        tile = 8
        magenta = 0xFFFF00FF
        black = 0xFF000000

        img = mlx.mlx_new_image(mlx_ptr, size, size)
        if img is None:
            return None

        data, bpp, size_line, _ = mlx.mlx_get_data_addr(img)
        bytes_per_pixel = bpp // 8

        for y in range(size):
            for x in range(size):
                color = magenta if (x // tile + y // tile) % 2 == 0 else black
                offset = y * size_line + x * bytes_per_pixel
                data[offset:offset + 4] = color.to_bytes(4, "little")

        data, bpp, line_size, endian = mlx.mlx_get_data_addr(img)
        return Texture(img, size, size, data, bpp, line_size, endian)


@dataclass(frozen=True)
class SpriteSheetKey:
    """Identifies one way of slicing a sheet into frames."""
    path: str
    frame_width: int
    frame_height: int
    frame_count: Optional[int] = None
    columns: Optional[int] = None
    start_frame: int = 0


class Animation:
    """Plays back a list of frame Textures at a fixed rate."""

    def __init__(self, frames: List[Texture], fps: float = 10.0,
                 loop: bool = True) -> None:
        self.frames = frames
        self.loop = loop
        self.fps: float = fps
        self.frame_duration: float = 0.0
        self.set_fps(fps)

    def set_fps(self, fps: float) -> None:
        self.fps = fps
        self.frame_duration = (1000.0 / fps) if fps > 0 else 0.0

    def frame_at(self, elapsed_ms: float) -> Optional[Texture]:
        if not self.frames:
            return None
        if self.frame_duration <= 0:
            return self.frames[0]
        index = int(elapsed_ms // self.frame_duration)
        if self.loop:
            index %= len(self.frames)
        else:
            index = min(index, len(self.frames) - 1)
        return self.frames[index]

    def finished(self, elapsed_ms: float) -> bool:
        if self.loop or not self.frames:
            return False
        return elapsed_ms >= self.frame_duration * len(self.frames)


class SpriteSheetLoader(AssetLoader):
    """Slices one sprite-sheet image into frames."""

    def can_load(self, key: Any) -> bool:
        return isinstance(key, SpriteSheetKey)

    def load(self, key: SpriteSheetKey) -> SpriteSheetKey:
        return key

    def finalize(self, key: SpriteSheetKey) -> List[Texture]:
        if not Context.ready:
            raise RuntimeError(
                "MLX asset loading used before Context.bind(mlx, mlx_ptr) "
                "was called — call Assets.init(mlx, mlx_ptr) right after "
                "mlx_init()."
            )

        mlx = Context.mlx
        mlx_ptr = Context.mlx_ptr

        if mlx is None or mlx_ptr is None:
            raise RuntimeError("MLX context not properly initialized")

        path = key.path

        if path.lower().endswith(".xpm"):
            img, sheet_w, sheet_h = mlx.mlx_xpm_file_to_image(mlx_ptr, path)
        else:
            img, sheet_w, sheet_h = mlx.mlx_png_file_to_image(mlx_ptr, path)

        if img is None:
            raise ValueError(f"mlx failed to load sprite sheet: {path}")

        sheet_data, bpp, sheet_line_size, endian = mlx.mlx_get_data_addr(img)
        bytes_per_pixel = bpp // 8

        columns = key.columns or max(1, sheet_w // key.frame_width)
        rows = max(1, sheet_h // key.frame_height)
        available = columns * rows
        start = min(max(key.start_frame, 0), available)
        remaining = available - start
        frame_count = key.frame_count if key.frame_count is not None \
            else remaining
        frame_count = min(frame_count, remaining)

        frame_line_size = key.frame_width * bytes_per_pixel
        frames: List[Texture] = []

        for i in range(frame_count):
            idx = start + i
            col = idx % columns
            row = idx // columns

            src_x = col * key.frame_width
            src_y = row * key.frame_height

            frame_data = bytearray(frame_line_size * key.frame_height)

            for y in range(key.frame_height):
                src_offset = (src_y + y) * sheet_line_size + src_x \
                    * bytes_per_pixel
                dst_offset = y * frame_line_size
                frame_data[dst_offset:dst_offset + frame_line_size] = (
                    sheet_data[src_offset:src_offset + frame_line_size]
                )

            frames.append(Texture(
                img=None,
                width=key.frame_width,
                height=key.frame_height,
                data=frame_data,
                bpp=bpp,
                line_size=frame_line_size,
                endian=endian,
            ))

        return frames

    def placeholder(self) -> Optional[List[Texture]]:
        """A single-frame magenta/black placeholder list."""
        if not Context.ready:
            return None

        mlx = Context.mlx
        mlx_ptr = Context.mlx_ptr

        if mlx is None or mlx_ptr is None:
            return None

        size = 64
        tile = 8
        magenta = 0xFFFF00FF
        black = 0xFF000000

        img = mlx.mlx_new_image(mlx_ptr, size, size)
        if img is None:
            return None

        data, bpp, size_line, endian = mlx.mlx_get_data_addr(img)
        bytes_per_pixel = bpp // 8

        for y in range(size):
            for x in range(size):
                color = magenta if (x // tile + y // tile) % 2 == 0 else black
                offset = y * size_line + x * bytes_per_pixel
                data[offset:offset + 4] = color.to_bytes(4, "little")

        return [Texture(None, size, size, data, bpp, size_line, endian)]


class AssetManager:
    """Manages asset loading with threading."""

    def __init__(self) -> None:
        self._loaders: List[AssetLoader] = []
        self._cache: Dict[str, Any] = {}
        self._pending: Set[str] = set()
        self._lock = threading.Lock()
        self._logger = Log.get("assets")
        self._in_queue: queue.Queue[Tuple[str, AssetLoader]] = queue.Queue()
        self._out_queue: queue.Queue[Tuple[str, AssetLoader, Any,
                                     Optional[Exception],
                                     Optional[str]]] = queue.Queue()

        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def register(self, loader: AssetLoader) -> None:
        self._loaders.append(loader)

    def _find_loader(self, path: Any) -> AssetLoader:
        for loader in self._loaders:
            if loader.can_load(path):
                return loader
        self._logger.error(f"No loader registered for: {path}")
        raise ValueError(f"No loader registered for: {path}")

    def load(self, path: str) -> Any:
        """Synchronous, blocking load."""
        with self._lock:
            if path in self._cache:
                return self._cache[path]

        loader = self._find_loader(path)

        try:
            asset = loader.finalize(loader.load(path))
        except Exception as error:
            self._logger.error(f"Failed to load {path}: {error}"
                               f"\n{traceback.format_exc()}")
            asset = loader.placeholder()

        with self._lock:
            self._cache[path] = asset

        return asset

    def queue(self, path: str) -> None:
        """Queue an asset load."""
        with self._lock:
            if path in self._cache:
                return
            if path in self._pending:
                return
            self._pending.add(path)

        loader = self._find_loader(path)
        self._in_queue.put((path, loader))

    def _run(self) -> None:
        while True:
            path, loader = self._in_queue.get()
            try:
                raw = loader.load(path)
                self._out_queue.put((path, loader, raw, None, None))
            except Exception as error:
                self._out_queue.put((path, loader, None,
                                     error, traceback.format_exc()))

    def update(self) -> None:
        """Call once per frame from the main thread."""
        while not self._out_queue.empty():
            path, loader, raw, error, tb = self._out_queue.get()

            if error is not None:
                self._logger.error(f"Failed to load {path}: {error}\n{tb}")
                asset = loader.placeholder()
            else:
                try:
                    asset = loader.finalize(raw)
                except Exception as error:
                    self._logger.error(f"Failed to finalize {path}: {error}"
                                       f"\n{traceback.format_exc()}")
                    asset = loader.placeholder()

            with self._lock:
                self._cache[path] = asset
                self._pending.discard(path)

    def get(self, path: str) -> Any:
        return self._cache.get(path)

    def ready(self, path: str) -> bool:
        return path in self._cache

    def loading(self, path: str) -> bool:
        return path in self._pending

    def cached(self, path: str) -> bool:
        return path in self._cache
