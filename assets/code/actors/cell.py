from __future__ import annotations

from Engine import AActor, Vector2
from ..components.wall_components import (
    Wall_Component, Corner_Component, Inner_Corner_Component,
)


class Cell(AActor):
    """Cell Actor"""

    def __init__(
        self,
        position: Vector2,
        N: bool = True,
        S: bool = True,
        E: bool = True,
        W: bool = True,
    ):
        super().__init__(
            position=position,
            scale=Vector2(1, 1),
            static=True,
        )

        self.north: Cell | None = None
        self.south: Cell | None = None
        self.east: Cell | None = None
        self.west: Cell | None = None

        self.open_north = N
        self.open_south = S
        self.open_east = E
        self.open_west = W

        sides = {
            "N": (N, 180),
            "E": (E, 270),
            "S": (S, 0),
            "W": (W, 90),
        }

        for is_open, rotation in sides.values():
            if not is_open:
                self.add_component(Wall_Component(rotation))


    @property
    def has_north_wall(self):
        return not self.open_north

    @property
    def has_east_wall(self):
        return not self.open_east

    @property
    def has_south_wall(self):
        return not self.open_south

    @property
    def has_west_wall(self):
        return not self.open_west

    def build_geometry(self):
        # Outer (convex) NE corner
        if (
            self.open_north
            and self.open_east
            and self.north
            and self.north.has_east_wall
        ):
            self.add_component(Corner_Component(local_rotation=180))

        # Outer (convex) NW corner
        if (
            self.open_north
            and self.open_west
            and self.north
            and self.north.has_west_wall
        ):
            self.add_component(Corner_Component(local_rotation=90))

        # Outer (convex) SE corner
        if (
            self.open_south
            and self.open_east
            and self.south
            and self.south.has_east_wall
        ):
            self.add_component(Corner_Component(local_rotation=270))

        # Outer (convex) SW corner
        if (
            self.open_south
            and self.open_west
            and self.south
            and self.south.has_west_wall
        ):
            self.add_component(Corner_Component(local_rotation=0))

        # Inner (concave) NE corner: this cell's own N and E walls meet
        if self.has_north_wall and self.has_east_wall:
            self.add_component(Inner_Corner_Component(local_rotation=180))

        # Inner (concave) NW corner: this cell's own N and W walls meet
        if self.has_north_wall and self.has_west_wall:
            self.add_component(Inner_Corner_Component(local_rotation=90))

        # Inner (concave) SE corner: this cell's own S and E walls meet
        if self.has_south_wall and self.has_east_wall:
            self.add_component(Inner_Corner_Component(local_rotation=270))

        # Inner (concave) SW corner: this cell's own S and W walls meet
        if self.has_south_wall and self.has_west_wall:
            self.add_component(Inner_Corner_Component(local_rotation=0))
