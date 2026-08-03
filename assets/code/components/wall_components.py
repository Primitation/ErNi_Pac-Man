from Engine import AnimatedSpriteComponent, Vector2


class Wall_Component(AnimatedSpriteComponent):
    """Sprite drawn on a closed side of a cell."""

    def __init__(self, local_rotation: float = 0):
        super().__init__(
            frame_width=16,
            frame_height=16,
            center=True,
            scale=(2.7, 1),
            frame_count=1,
            start_frame=61,
            loop=False,
            path="assets/texture/spritesheets/pacman_hd/"
                 "PacManAssets_Map_TileSet.png",
            local_rotation=local_rotation,
            local_offset=Vector2(0, 21),
            render_layer=0
        )


class Corner_Component(AnimatedSpriteComponent):
    """Outer (convex) corner sprite."""

    def __init__(self, local_rotation: float = 0):
        super().__init__(
            frame_width=8,
            frame_height=8,
            center=True,
            scale=(1, 1),
            frame_count=1,
            start_frame=289,
            loop=False,
            path="assets/texture/spritesheets/pacman_hd/"
                 "PacManAssets_Map_TileSet.png",
            local_rotation=local_rotation,
            local_offset=Vector2(-17.1, 17.1),
            render_layer=1
        )


class Inner_Corner_Component(AnimatedSpriteComponent):
    """Inner (concave) corner sprite."""

    BACKGROUND_START_FRAME = 392

    def __init__(self, local_rotation: float = 0):
        super().__init__(
            frame_width=8,
            frame_height=8,
            center=True,
            scale=(1, 1),
            frame_count=1,
            start_frame=393,
            loop=False,
            path="assets/texture/spritesheets/pacman_hd/"
                 "PacManAssets_Map_TileSet.png",
            local_rotation=local_rotation,
            local_offset=Vector2(-14.0, 14.0),
            render_layer=2
        )
        self._local_rotation = local_rotation

    def on_added(self, actor) -> None:
        super().on_added(actor)

        background = AnimatedSpriteComponent(
            frame_width=8,
            frame_height=8,
            center=True,
            scale=(1, 1),
            frame_count=1,
            start_frame=self.BACKGROUND_START_FRAME,
            loop=False,
            path="assets/texture/spritesheets/pacman_hd/"
                 "PacManAssets_Map_TileSet.png",
            local_rotation=self._local_rotation,
            local_offset=Vector2(-18.0, 18.0),
            render_layer=1,
        )
        actor.add_component(background)


class Empty_Wall_Component(AnimatedSpriteComponent):
    """Sprite drawn on an open side of a cell."""

    def __init__(self, local_rotation: float = 0):
        super().__init__(
            frame_width=16,
            frame_height=16,
            center=True,
            frame_count=1,
            start_frame=20,
            loop=False,
            path="assets/texture/spritesheets/pacman_hd/"
                 "PacManAssets_Map_TileSet.png",
            local_rotation=local_rotation,
            local_offset=Vector2(0, 21)
        )
