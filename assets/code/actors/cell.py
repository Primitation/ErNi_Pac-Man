from __future__ import annotations

from typing import Optional

from Engine import AActor, Vector2
from ..components.wall_components import (  # type: ignore
    Wall_Component,
    Corner_Component,
    Inner_Corner_Component,
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
    ) -> None:
        super().__init__(
            position=position,
            scale=Vector2(1, 1),
            static=True,
        )

        self.north: Optional[Cell] = None
        self.south: Optional[Cell] = None
        self.east: Optional[Cell] = None
        self.west: Optional[Cell] = None

        self.open_north: bool = N
        self.open_south: bool = S
        self.open_east: bool = E
        self.open_west: bool = W

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
    def has_north_wall(self) -> bool:
        return not self.open_north

    @property
    def has_east_wall(self) -> bool:
        return not self.open_east

    @property
    def has_south_wall(self) -> bool:
        return not self.open_south

    @property
    def has_west_wall(self) -> bool:
        return not self.open_west

    @staticmethod
    def has_neighbor_wall(cell: Optional[Cell], wall: str) -> bool:
        """
        Missing neighbors are considered walls.
        """
        if cell is None:
            return True

        return bool(getattr(cell, wall))

    def build_geometry(self) -> None:
        """Build wall geometry for this cell."""

        # Outer (convex) NE corner
        if (
            self.open_north
            and self.open_east
            and (
                self.has_neighbor_wall(
                    self.north,
                    "has_east_wall"
                )
                or self.has_neighbor_wall(
                    self.east,
                    "has_north_wall"
                )
            )
        ):
            self.add_component(
                Corner_Component(local_rotation=180)
            )

        # Outer (convex) NW corner
        if (
            self.open_north
            and self.open_west
            and (
                self.has_neighbor_wall(
                    self.north,
                    "has_west_wall"
                )
                or self.has_neighbor_wall(
                    self.west,
                    "has_north_wall"
                )
            )
        ):
            self.add_component(
                Corner_Component(local_rotation=90)
            )

        # Outer (convex) SE corner
        if (
            self.open_south
            and self.open_east
            and (
                self.has_neighbor_wall(
                    self.south,
                    "has_east_wall"
                )
                or self.has_neighbor_wall(
                    self.east,
                    "has_south_wall"
                )
            )
        ):
            self.add_component(
                Corner_Component(local_rotation=270)
            )

        # Outer (convex) SW corner
        if (
            self.open_south
            and self.open_west
            and (
                self.has_neighbor_wall(
                    self.south,
                    "has_west_wall"
                )
                or self.has_neighbor_wall(
                    self.west,
                    "has_south_wall"
                )
            )
        ):
            self.add_component(
                Corner_Component(local_rotation=0)
            )

        # Inner (concave) NE corner
        if self.has_north_wall and self.has_east_wall:
            self.add_component(
                Inner_Corner_Component(local_rotation=180)
            )

        # Inner (concave) NW corner
        if self.has_north_wall and self.has_west_wall:
            self.add_component(
                Inner_Corner_Component(local_rotation=90)
            )

        # Inner (concave) SE corner
        if self.has_south_wall and self.has_east_wall:
            self.add_component(
                Inner_Corner_Component(local_rotation=270)
            )

        # Inner (concave) SW corner
        if self.has_south_wall and self.has_west_wall:
            self.add_component(
                Inner_Corner_Component(local_rotation=0)
            )
