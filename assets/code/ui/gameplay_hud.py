"""Gameplay HUD — bottom-right overlay."""

from typing import Any

from Engine import Assets, Actors
from Engine.UISubsystem.uisubsystem import HBox, Image, BitmapText
from assets.code.actors.player import Player
from assets.code.ui.font_config import (
    ARCADE_FONT_PATH,
    ARCADE_FONT_CHARSET,
    ARCADE_FONT_CHAR_WIDTH,
    ARCADE_FONT_CHAR_HEIGHT,
    ARCADE_FONT_COLUMNS,
)

LIFE_ICON_PATH = "assets/texture/pacman.png"


class GameplayHUD:
    """Call .render(Renderer) once per frame."""

    LIFE_ICON_SIZE = 24
    LIFE_ICON_SPACING = 6
    TEXT_SCALE = 2.0
    SPACING = 24
    PADDING = 12
    MARGIN = 16
    BACKGROUND_COLOR = 0x88000000

    def __init__(self) -> None:
        self._font_texture = Assets.load(ARCADE_FONT_PATH)
        self._life_texture = Assets.load(LIFE_ICON_PATH)

    def _label(self, text: str) -> BitmapText:
        return BitmapText(
            text,
            self._font_texture,
            char_width=ARCADE_FONT_CHAR_WIDTH,
            char_height=ARCADE_FONT_CHAR_HEIGHT,
            charset=ARCADE_FONT_CHARSET,
            columns=ARCADE_FONT_COLUMNS,
            scale=self.TEXT_SCALE,
        )

    def _build_root(self) -> HBox:
        player = Player.current_player
        lives = player.lives if player is not None else 0
        score = player.score_info.score if player is not None else 0
        time_left = max(0, int(Actors.remaining_time))

        root = HBox(
            spacing=self.SPACING,
            padding=self.PADDING,
            background_color=self.BACKGROUND_COLOR,
        )

        lives_box = HBox(spacing=self.LIFE_ICON_SPACING)
        for _ in range(max(0, lives)):
            lives_box.add(
                Image(
                    self._life_texture,
                    width=self.LIFE_ICON_SIZE,
                    height=self.LIFE_ICON_SIZE
                ),
                align="center",
            )
        root.add(lives_box, align="center")

        root.add(self._label(f"{score:01d} ,[]"), align="center")
        root.add(self._label(f"{time_left:03d}"), align="center")

        return root

    def render(self, renderer: Any) -> None:
        root = self._build_root()
        w, h = root.measure()
        x = renderer.width - w - self.MARGIN
        y = renderer.height - h - self.MARGIN
        root.arrange(x, y, w, h)
        root.render(renderer)
