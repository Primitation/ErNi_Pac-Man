from Engine import World, AActor, Actors, Vector2
from abc import ABC
from ..code.player import Player


class Level(ABC):
    actors: AActor = []

    def load(self):
        World.clear()
        Actors.clear()
        self._spawn_actors()

    def _spawn_actors(self):
        """Spawn all actors from the actors list"""
        for actor_class, kwargs in self.actors:
            Actors.spawn(actor_class, **kwargs)

    def add_actor(self, actor_class: type, **kwargs):
        """Helper method to add an actor to be spawned"""
        self.actors.append((actor_class, kwargs))


class Level_1(Level):
    super.add_actor(Player, Vector2(0, 0), Vector2(0.25, 0.25),
                   "assets.texture.pacman.png")