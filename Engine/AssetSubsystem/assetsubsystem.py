from .loader import AssetManager, TextureLoader, SpriteSheetLoader, Context


class AssetSubsystem:
    """Global asset management system."""

    def __init__(self):
        self._manager = AssetManager()
        self._manager.register(TextureLoader())
        self._manager.register(SpriteSheetLoader())
        self._cache = {}
        self._loading = set()

    def init(self, mlx, mlx_ptr):
        """Call once, right after mlx_init()."""
        Context.bind(mlx, mlx_ptr)

    def register(self, loader):
        """Register a new asset loader."""
        self._manager.register(loader)

    def load(self, path: str):
        """Immediately load an asset."""
        if path in self._cache:
            return self._cache[path]

        asset = self._manager.load(path)
        self._cache[path] = asset
        return asset

    def queue(self, path: str):
        """Queue an asset for loading."""
        if path in self._cache:
            return
        if path in self._loading:
            return
        self._loading.add(path)
        self._manager.queue(path)

    def update(self):
        """Updates asynchronous loaders."""
        self._manager.update()
        finished = [
            path for path in self._loading
            if self._manager.ready(path)
        ]
        for path in finished:
            self._cache[path] = self._manager.get(path)
            self._loading.remove(path)

    def get(self, path: str):
        """Returns the cached asset, or None."""
        return self._cache.get(path)

    def ready(self, path: str) -> bool:
        """Returns True when an asset finished loading."""
        return path in self._cache

    def loading(self, path: str) -> bool:
        """Returns True while an asset is being loaded."""
        return path in self._loading

    def cached(self, path: str) -> bool:
        """Returns True when an asset exists in the cache."""
        return path in self._cache


Assets = AssetSubsystem()
