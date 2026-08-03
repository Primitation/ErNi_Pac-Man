from typing import Any

from Engine import Assets
from Engine.UISubsystem.uisubsystem import HBox, BitmapText
from assets.code.ui.font_config import (
    ARCADE_FONT_PATH,
    ARCADE_FONT_CHARSET,
    ARCADE_FONT_CHAR_WIDTH,
    ARCADE_FONT_CHAR_HEIGHT,
    ARCADE_FONT_COLUMNS,
)


class PauseHUD:
    """Call .render(Renderer) once per frame."""

    TEXT_SCALE = 3.0
    SPACING = 24
    PADDING = 12
    MARGIN = 16
    BACKGROUND_COLOR = 0x88000000

    def __init__(self) -> None:
        self._font_texture = Assets.load(ARCADE_FONT_PATH)

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
        root = HBox(
            spacing=self.SPACING,
            padding=self.PADDING,
            background_color=self.BACKGROUND_COLOR,
        )
        root.add(self._label("PAUSE - P RESUME - M MENU"), align="center")
        return root

    def render(self, renderer: Any) -> None:
        root = self._build_root()
        w, h = root.measure()
        x = (renderer.width - w) // 2
        y = (renderer.height - h) // 2
        root.arrange(x, y, w, h)
        root.render(renderer)
