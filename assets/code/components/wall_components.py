from Engine import AnimatedSpriteComponent, Vector2


class Wall_Component(AnimatedSpriteComponent):
    """Sprite drawn on a closed side of a cell (a wall)."""

    def __init__(self, local_rotation=0):
        super().__init__(frame_width=16, frame_height=16, center=True, scale=(2.7, 1),
                       frame_count=1, start_frame=61, loop=False,
                       path="assets/texture/spritesheets/pacman_hd/PacManAssets_Map_TileSet.png",
                       local_rotation=local_rotation, local_offset=Vector2(0, 21),
                       render_layer=0)

class Corner_Component(AnimatedSpriteComponent):
    """Outer (convex) corner sprite.
 
    Placed when this cell is open on two adjacent sides but a diagonal
    neighbor has a wall poking toward this cell's corner — rounds off
    the outside of that wall.
 
    Unlike Wall_Component (which sits at an edge midpoint), a corner
    sprite needs a diagonal offset. The base offset below places the
    sprite at the SW corner (rotation=0); the engine rotates this
    offset along with local_rotation to reach NW (90), NE (180) and
    SE (270), matching the rotation convention used in Cell.build_geometry.
    """


    def __init__(self, local_rotation=0):
        super().__init__(frame_width=8, frame_height=8, center=True, scale=(1, 1),
                       frame_count=1, start_frame=289, loop=False,
                       path="assets/texture/spritesheets/pacman_hd/PacManAssets_Map_TileSet.png",
                       local_rotation=local_rotation, local_offset=Vector2(-17.1, 17.1),
                       render_layer=1)


class Inner_Corner_Component(AnimatedSpriteComponent):
    """Inner (concave) corner sprite.
 
    Placed when this cell itself has two adjacent walls (e.g. a north
    wall and an east wall) — rounds off the inside joint where those
    two walls meet, instead of leaving a hard right angle.
 
    Uses the same diagonal offset convention as Corner_Component: base
    offset targets the SW corner at rotation=0, and local_rotation
    rotates it to NW (90) / NE (180) / SE (270).
 
    The cutout tile (393) is small (8x8) and mostly transparent around
    the rounded edge, which lets a sliver of whatever's underneath
    bleed through at the wall/corner seam. To patch that, on_added()
    adds a second, solid wall-colored backing tile (392) at the exact
    same position/rotation, one layer below this overlay — see
    render_layer below.
    """
 
    BACKGROUND_START_FRAME = 392
 
    def __init__(self, local_rotation=0):
        super().__init__(frame_width=8, frame_height=8, center=True, scale=(1, 1),
                       frame_count=1, start_frame=393, loop=False,
                       path="assets/texture/spritesheets/pacman_hd/PacManAssets_Map_TileSet.png",
                       local_rotation=local_rotation, local_offset=Vector2(-14.0, 14.0),
                       render_layer=2)
        self._local_rotation = local_rotation
 
    def on_added(self, actor):
        super().on_added(actor)
 
        background = AnimatedSpriteComponent(
            frame_width=8, frame_height=8, center=True, scale=(1, 1),
            frame_count=1, start_frame=self.BACKGROUND_START_FRAME, loop=False,
            path="assets/texture/spritesheets/pacman_hd/PacManAssets_Map_TileSet.png",
            local_rotation=self._local_rotation, local_offset=Vector2(-18.0, 18.0),
            render_layer=1,
        )
        actor.add_component(background)


class Empty_Wall_Component(AnimatedSpriteComponent):
    """Sprite drawn on an open side of a cell (no wall).

    TODO: update start_frame to the actual "empty side" tile index in
    PacManAssets_Map_TileSet.png (39 is the closed-wall tile, reused
    here only as a placeholder so this compiles/runs).
    """

    def __init__(self, local_rotation=0):
        super().__init__(frame_width=16, frame_height=16, center=True,
                       frame_count=1, start_frame=20, loop=False,
                       path="assets/texture/spritesheets/pacman_hd/PacManAssets_Map_TileSet.png",
                       local_rotation=local_rotation, local_offset=Vector2(0, 21))
