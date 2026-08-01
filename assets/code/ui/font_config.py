"""Shared sprite-sheet font config — see BitmapText in uisubsystem.py.

ArcadeFont.png is a 128x32 sheet, 8x8 px cells, 16 columns x 4 rows.
Both mainmenu.py and gameplay_hud.py import from here so the path/
charset/cell-size only need updating in one place.
"""

ARCADE_FONT_PATH = "assets/texture/ArcadeFont.png"
ARCADE_FONT_CHARSET = "ABCDEFGHIJKLMNO_PQRSTUVWXYZ!?pts0123456789/-'_ "
ARCADE_FONT_CHAR_WIDTH = 8
ARCADE_FONT_CHAR_HEIGHT = 8
ARCADE_FONT_COLUMNS = 16
