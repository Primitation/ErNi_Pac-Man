from Engine import Assets, Actors, Renderer
from Engine.UISubsystem.uisubsystem import HBox, Image, BitmapText
from assets.code.actors.player import Player
from assets.code.ui.font_config import (
    ARCADE_FONT_PATH, ARCADE_FONT_CHARSET,
    ARCADE_FONT_CHAR_WIDTH, ARCADE_FONT_CHAR_HEIGHT, ARCADE_FONT_COLUMNS,
)


class PauseHUD:
    """Call .render(Renderer) once per frame, after drawing the world
    and before Renderer.render_present() — same slot MainMenu's
    canvas.render() occupies for menu screens."""

    TEXT_SCALE = 3.0
    SPACING = 24
    PADDING = 12
    MARGIN = 16
    BACKGROUND_COLOR = 0x88000000

    def __init__(self):
        """Initialize pause hud."""
        self._font_texture = Assets.load(ARCADE_FONT_PATH)

    def _label(self, text: str) -> BitmapText:
        return BitmapText(
            text, self._font_texture,
            char_width=ARCADE_FONT_CHAR_WIDTH, char_height=ARCADE_FONT_CHAR_HEIGHT,
            charset=ARCADE_FONT_CHARSET, columns=ARCADE_FONT_COLUMNS,
            scale=self.TEXT_SCALE,
        )

    def _build_root(self) -> HBox:
        root = HBox(
            spacing=self.SPACING, padding=self.PADDING,
            background_color=self.BACKGROUND_COLOR,
        )
        root.add(self._label(f"PAUSE - P RESUME - M MENU"), align="center")
        return root

    def render(self, renderer) -> None:
        root = self._build_root()
        w, h = root.measure()
        x = 0
        y = 0
        root.arrange(x, y, w, h)
        root.render(renderer)
