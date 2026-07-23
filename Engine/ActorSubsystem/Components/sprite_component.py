from .component import Component
from ... import Assets


class SpriteComponent(Component):
    """A static, single-image sprite.

    Same lazy/caching behavior AActor.sprite used to have: this
    doesn't hold the loaded image itself, only the path. `.sprite`
    resolves from AssetSubsystem's cache on every access — it reads
    back None until the background load finishes, then the same
    (cached, shared) Texture every other user of that path gets.
    """

    def __init__(self, path: str = None, enabled: bool = True):
        super().__init__(enabled)
        self._path = path

    def on_added(self, actor):
        super().on_added(actor)
        if self._path is not None:
            Assets.queue(self._path)

    def set_sprite(self, path: str):
        """Swap to a different static image."""
        self._path = path
        Assets.queue(path)

    @property
    def sprite(self):
        if self._path is None:
            return None
        return Assets.get(self._path)

    @property
    def width(self):
        sprite = self.sprite
        return sprite.width if sprite is not None else 0

    @property
    def height(self):
        sprite = self.sprite
        return sprite.height if sprite is not None else 0

    def get_rect(self):
        """Rect (x, y, width, height) from the actor's position and
        scale — handy to pass straight into a ColliderComponent as
        `get_rect=sprite_component.get_rect`, or to use as the
        fallback ColliderComponent picks up automatically when no
        get_rect is given."""
        actor = self.actor
        width = self.width * actor.scale.x
        height = self.height * actor.scale.y
        return (actor.position.x, actor.position.y, width, height)
