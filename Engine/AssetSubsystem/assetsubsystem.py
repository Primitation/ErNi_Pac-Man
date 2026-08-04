# assetsubsystem.py
from typing import Any, Dict, Set, Optional
from .loader import AssetManager, TextureLoader, SpriteSheetLoader, Context


class AssetSubsystem:
    """Global asset management system."""

    def __init__(self) -> None:
        """Initialize an asset manager."""
        self._manager = AssetManager()
        self._manager.register(TextureLoader())
        self._manager.register(SpriteSheetLoader())
        self._cache: Dict[str, Any] = {}
        self._loading: Set[str] = set()

    def init(self, mlx: Any, mlx_ptr: Any) -> None:
        """Call once, right after mlx_init().

        Args:
            mlx: the minilibx instance.
            mlx_ptr: the minilibX initialized instance.
        """
        Context.bind(mlx, mlx_ptr)

    def register(self, loader: Any) -> None:
        """Register a new asset loader.

        Args:
            loader: a loader.
        """
        self._manager.register(loader)

    def load(self, path: str) -> Any:
        """Immediately load an asset.

        Args:
            path: the path of the asset.

        Returns:
            Returns the asset.
        """
        if path in self._cache:
            return self._cache[path]

        asset = self._manager.load(path)
        self._cache[path] = asset
        return asset

    def queue(self, path: str) -> None:
        """Queue an asset for loading.

        Args:
            path: the path of the asset.
        """
        if path in self._cache:
            return
        if path in self._loading:
            return
        self._loading.add(path)
        self._manager.queue(path)

    def update(self) -> None:
        """Updates asynchronous loaders."""
        self._manager.update()
        finished = [
            path for path in self._loading
            if self._manager.ready(path)
        ]
        for path in finished:
            self._cache[path] = self._manager.get(path)
            self._loading.remove(path)

    def get(self, path: str) -> Optional[Any]:
        """Returns the cached asset, or None.

        Args:
            path: the path of the asset.

        Returns:
            Returns the cached asset.
        """
        return self._cache.get(path)

    def ready(self, path: str) -> bool:
        """Returns True when an asset finished loading.

        Args:
            path: the path of the asset.

        Returns:
            Returns if the asset is ready or not.
        """
        return path in self._cache

    def loading(self, path: str) -> bool:
        """Returns True while an asset is being loaded.

        Args:
            path: the path of the asset.

        Returns:
            Returns the asset is loading or not.
        """
        return path in self._loading

    def cached(self, path: str) -> bool:
        """Returns True when an asset exists in the cache.

        Args:
            path: the path of the asset.

        Returns:
            Returns the asset is cached or not.
        """
        return path in self._cache


Assets = AssetSubsystem()
