from abc import ABC


class Component(ABC):
    """Base class for everything an Actor can carry as a component —
    SpriteComponent, AnimatedSpriteComponent, ColliderComponent, and
    later gameplay components like a Health component.

    An actor owns an ordered list of components (see
    AActor.add_component()). Every frame, AActor._tick() calls
    update() on each enabled/alive component before calling the
    actor's own update() — so components can, e.g., advance an
    animation before the actor reacts to it.

    Subclasses typically override on_added() (setup that needs
    self.actor to exist, e.g. registering with Collision),
    update(dt), and destroy() (release anything external, e.g.
    unregister from Collision). Always call super().destroy() so
    `alive` flips to False.
    """

    def __init__(self, enabled: bool = True):
        self.actor = None
        self.enabled = enabled
        self.alive = True

    def on_added(self, actor):
        """Called once by AActor.add_component(), right after this
        component has been appended to actor.components. self.actor
        is set here — do any setup that needs the owning actor to
        already exist (e.g. Collision.register(owner=actor, ...))."""
        self.actor = actor

    def update(self, dt):
        """Override for per-frame work. Only called while the
        component is enabled and alive, and its actor is alive."""
        pass

    def destroy(self):
        """Override to release anything external (unregister from
        Collision, cancel a pending asset load, etc). Always call
        super().destroy() so `alive` becomes False and the actor
        stops ticking/rendering it."""
        self.alive = False
