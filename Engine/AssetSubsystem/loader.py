import threading
import queue
import traceback
from abc import ABC, abstractmethod

from .. import Log


class AssetLoader(ABC):
    """One loader per asset type. Same idea as your DataProcessor:
    the manager asks can_load() to pick the right one, then calls
    load()/finalize() on it."""

    @abstractmethod
    def can_load(self, path):
        pass

    @abstractmethod
    def load(self, path):
        """Runs on the WORKER thread. Keep this to file I/O only —
        no mlx_* calls here. mlx talks to the X server through a
        single connection (mlx_ptr) and is NOT thread-safe, so every
        mlx_* call has to happen on the main thread, unlike pygame
        where decoding could safely happen off-thread."""
        pass

    def finalize(self, raw):
        """Runs on the MAIN thread, once load() has returned.
        This is where anything that touches mlx belongs
        (mlx_png_file_to_image, mlx_new_image, ...)."""
        return raw

    def placeholder(self):
        """Fallback asset handed back when load()/finalize() raises,
        so a bad path degrades gracefully instead of crashing or
        leaving a name stuck pending forever. Override to return
        something type-appropriate. Returns None by default."""
        return None


class MlxContext:
    """Holds the single Mlx() instance + mlx_ptr every loader needs.

    The AssetSubsystem is built at import time (like the pygame one
    was), but mlx_init() can only run once your app has started —
    so this gets filled in later via bind(), instead of at
    construction time. Call Assets.init(mlx, mlx_ptr) right after
    mlx_init() and before loading/queueing anything.
    """

    def __init__(self):
        self.mlx = None
        self.mlx_ptr = None

    def bind(self, mlx, mlx_ptr):
        self.mlx = mlx
        self.mlx_ptr = mlx_ptr

    @property
    def ready(self):
        return self.mlx is not None and self.mlx_ptr is not None


Context = MlxContext()


class Texture:
    """Wraps a loaded mlx image with the width/height mlx hands back
    as a separate tuple, so callers get one object instead of
    juggling three values.

    There's no `.surface` anymore — mlx has no Surface type — so
    anything downstream that assumed a pygame.Surface (Sprite's
    rotate/scale via pygame.transform, blit-based rendering, ...)
    needs rewriting against `.img` + mlx_put_image_to_window instead.
    mlx doesn't do image transforms itself; scaling/rotating an mlx
    image means walking mlx_get_data_addr() pixels by hand, or
    pre-baking the variants you need as separate PNG/XPM files.
    """

    def __init__(self, img, width, height):
        self.img = img
        self.width = width
        self.height = height


class TextureLoader(AssetLoader):
    """mlx only decodes two formats itself: PNG and XPM (see
    mlx_png_file_to_image / mlx_xpm_file_to_image in mlx.h). No
    jpg/bmp support like the pygame version had — anything else
    needs a separate decoder before it can become an mlx image."""

    def can_load(self, path):
        return path.lower().endswith((".png", ".xpm"))

    def load(self, path):
        """Nothing to decode off-thread: mlx does its own decoding
        inside mlx_png_file_to_image/mlx_xpm_file_to_image, and that
        call has to happen on the main thread anyway (see the
        AssetLoader docstring). So this just passes the path through
        — the same way the pygame version's SoundLoader.load() only
        passed a path through for pygame.mixer.Sound to consume in
        finalize()."""
        return path

    def finalize(self, path):
        if not Context.ready:
            raise RuntimeError(
                "MLX asset loading used before Context.bind(mlx, mlx_ptr) "
                "was called — call Assets.init(mlx, mlx_ptr) right after "
                "mlx_init()."
            )

        if path.lower().endswith(".xpm"):
            img, width, height = Context.mlx.mlx_xpm_file_to_image(
                Context.mlx_ptr, path
            )
        else:
            img, width, height = Context.mlx.mlx_png_file_to_image(
                Context.mlx_ptr, path
            )

        if img is None:
            raise ValueError(f"mlx failed to load image: {path}")

        return Texture(img, width, height)

    def placeholder(self):
        """Classic magenta/black 'missing texture' checkerboard, built
        by hand since mlx has no Surface.fill() to lean on — just a
        blank image plus mlx_get_data_addr() to write pixels into.

        Color packing follows the same 0xAARRGGBB-as-little-endian-
        bytes convention used in mlx's own test suite (mlxtest.py).
        """

        if not Context.ready:
            return None

        size = 64
        tile = 8
        magenta = 0xFFFF00FF
        black = 0xFF000000

        img = Context.mlx.mlx_new_image(Context.mlx_ptr, size, size)
        if img is None:
            return None

        data, bpp, size_line, _ = Context.mlx.mlx_get_data_addr(img)
        bytes_per_pixel = bpp // 8

        for y in range(size):
            for x in range(size):
                color = magenta if (x // tile + y // tile) % 2 == 0 else black
                offset = y * size_line + x * bytes_per_pixel
                data[offset:offset + 4] = color.to_bytes(4, "little")

        return Texture(img, size, size)


# --------------------------------------------------------------------
# Sound
# --------------------------------------------------------------------
# mlx (minilibx) has no audio API whatsoever — mlx.h only covers
# windows, images, events and the X11 event loop. There's nothing to
# adapt SoundLoader *to*, so it's dropped from this version rather
# than faked. Two ways to bring sound back:
#
#   1. Keep pygame around just for audio (`pygame.mixer`), running
#      alongside mlx for display. They don't conflict — mlx owns the
#      window/X11 connection, pygame.mixer only touches SDL_audio.
#      The old SoundLoader class works unchanged; just register it
#      here too.
#   2. Use a dedicated audio library (e.g. `sounddevice`, `simpleaudio`)
#      if you'd rather drop the pygame dependency entirely.
#
# Left out rather than guessed — tell me which and I'll wire it in.


class AssetManager:

    def __init__(self):

        self._loaders = []
        self._assets = {}
        self._pending = set()
        self._lock = threading.Lock()

        self._cache = {}            # path -> finalized asset
        self._path_pending = {}     # path -> list of names waiting on it

        self._logger = Log.get("assets")

        self._in_queue = queue.Queue()
        self._out_queue = queue.Queue()

        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def register(self, loader):
        self._loaders.append(loader)

    def _find_loader(self, path):

        for loader in self._loaders:
            if loader.can_load(path):
                return loader

        self._logger.error(f"No loader registered for: {path}")
        raise ValueError(f"No loader registered for: {path}")

    def load(self, name, path):
        """Synchronous, blocking load. Fine for a loading screen or
        startup assets. Reuses a cached asset if this path was
        already loaded under any name."""

        with self._lock:
            cached = self._cache.get(path)

        if cached is not None:
            with self._lock:
                self._assets[name] = cached
            return cached

        loader = self._find_loader(path)

        try:
            asset = loader.finalize(loader.load(path))
        except Exception as error:
            self._logger.error(
                f"Failed to load {path}: {error}\n{traceback.format_exc()}"
            )
            asset = loader.placeholder()

        with self._lock:
            self._assets[name] = asset
            self._cache[path] = asset

        return asset

    def queue(self, name, path):
        """Queue a load to happen in the background. If this path is
        already cached, or already loading under another name, this
        just piggybacks on that instead of loading it again."""

        with self._lock:

            if name in self._assets or name in self._pending:
                return

            cached = self._cache.get(path)
            if cached is not None:
                self._assets[name] = cached
                return

            self._pending.add(name)

            if path in self._path_pending:
                self._path_pending[path].append(name)
                return

            self._path_pending[path] = [name]

        loader = self._find_loader(path)
        self._in_queue.put((path, loader))

    def _run(self):

        while True:

            path, loader = self._in_queue.get()

            try:
                raw = loader.load(path)
                self._out_queue.put((path, loader, raw, None, None))
            except Exception as error:
                self._out_queue.put((path, loader, None, error,
                                     traceback.format_exc()))

    def update(self):
        """Call once per frame from the main thread. Finalizes
        anything the worker thread has finished loading, and hands
        the result to every name that was waiting on that path.

        For mlx this is the ONLY place image creation actually
        happens — finalize() is where the real mlx_*_to_image call
        runs, on the main thread, which is what keeps this
        thread-safe against mlx's single X11 connection."""

        while not self._out_queue.empty():

            path, loader, raw, error, tb = self._out_queue.get()

            with self._lock:
                names = self._path_pending.pop(path, [])
                for name in names:
                    self._pending.discard(name)

            if error is not None:
                self._logger.error(f"Failed to load {path}: {error}\n{tb}")
                asset = loader.placeholder()

                with self._lock:
                    self._cache[path] = asset
                    for name in names:
                        self._assets[name] = asset

                continue

            try:
                asset = loader.finalize(raw)
            except Exception as error:
                self._logger.error(
                    f"Failed to finalize {path}: {error}\n"
                    f"{traceback.format_exc()}"
                )
                asset = loader.placeholder()

            with self._lock:
                self._cache[path] = asset
                for name in names:
                    self._assets[name] = asset

    def get(self, name):
        return self._assets.get(name)

    def ready(self, name):
        return name in self._assets

    def loading(self, name):
        return name in self._pending

    def cached(self, path):
        return path in self._cache
