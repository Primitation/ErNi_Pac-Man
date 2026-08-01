"""End screen — win/lose result page where the player types a name to
register their score on the local high-score table.

Mirrors MainMenu's shape: builds a small widget tree and runs its own
mlx loop via Renderer.hook_loop(), same pattern as LevelInstance and
MainMenu.

Text entry deliberately bypasses the action system and polls raw key
codes via Input.is_key_pressed() instead. Reason: InputSubsystem's
default bindings put "up/down/left/right" on WASD and "confirm" on
Enter *and* Space (see InputSubsystem._setup_input). If this screen
read actions instead of raw keys, typing "W", "A", "S", "D" or Space
into the name would also fire navigation/confirm — so process_actions()
is never called here, only process_events()/update().
"""

from Engine import Assets, Input, Log, Renderer
from Engine.UISubsystem.uisubsystem import VBox, HBox, BitmapText, Spacer
from assets.code.ui.font_config import (
    ARCADE_FONT_PATH, ARCADE_FONT_CHARSET,
    ARCADE_FONT_CHAR_WIDTH, ARCADE_FONT_CHAR_HEIGHT, ARCADE_FONT_COLUMNS,
)
from assets.code.ui.screen_transition import PacmanTransition as Transition


class EndScreen:
    """Call .show() to run the loop. Blocks until the player confirms
    a name, then returns it (str, 1-10 chars: uppercase A-Z, 0-9,
    spaces only)."""

    MAX_NAME_LENGTH = 10
    ALLOWED_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ")
    DEFAULT_NAME = "PLAYER"

    def __init__(self, won: bool, score: int):
        self._logger = Log.get("menu")
        self._font_texture = Assets.load(ARCADE_FONT_PATH)
        self._won = won
        self._score = score
        self._name = ""
        self._result = None
        self._char_keys = self._build_char_keys()

        self._fade_in = Transition(650)
        self._fade_out = None  # created once a name is confirmed

    @staticmethod
    def _build_char_keys():
        """keycode -> character it types. Only built from keys that
        already exist in Input.KEYS (a-z, 0-9, space)."""
        keys = {}
        for ch in "abcdefghijklmnopqrstuvwxyz":
            keys[Input.KEYS[ch]] = ch.upper()
        for ch in "0123456789":
            keys[Input.KEYS[ch]] = ch
        keys[Input.KEYS["space"]] = " "
        return keys

    # ----- widgets -----

    def _label(self, text: str, scale: float = 3.0) -> BitmapText:
        return BitmapText(
            text, self._font_texture,
            char_width=ARCADE_FONT_CHAR_WIDTH, char_height=ARCADE_FONT_CHAR_HEIGHT,
            charset=ARCADE_FONT_CHARSET, columns=ARCADE_FONT_COLUMNS,
            scale=scale,
        )

    def _build_root(self) -> VBox:
        root = VBox(spacing=20, justify="center", background_color=0xFF000000)

        title = "WINNER" if self._won else "GAME OVER"
        root.add(self._label(title, scale=8.0), align="center")
        root.add(Spacer(height=10))
        root.add(self._label(f"SCORE {self._score}", scale=5.0), align="center")

        root.add(Spacer(height=20))
        root.add(self._label("ENTER YOUR NAME", scale=3.0), align="center")

        cursor = "_" if len(self._name) < self.MAX_NAME_LENGTH else ""
        name_box = HBox(padding=10, background_color=0xFF222222)
        name_box.add(self._label(self._name + cursor, scale=4.0), align="center")
        root.add(name_box, align="center")

        root.add(Spacer(height=10))
        hint = ("ENTER TO CONFIRM - BACKSPACE TO DELETE"
                if self._name else "A-Z 0-9 SPACE - 10 CHAR MAX")
        root.add(self._label(hint, scale=2.0), align="center")

        return root

    # ----- input -----

    def _handle_text_input(self) -> None:
        if self._fade_out is not None:
            return  # confirmed already, ignore further typing during fade

        if Input.is_key_pressed(Input.KEYS["backspace"]):
            self._name = self._name[:-1]
            return

        if Input.is_key_pressed(Input.KEYS["enter"]):
            self._confirm()
            return

        if Input.is_key_pressed(Input.KEYS["escape"]):
            self._confirm()
            return

        for keycode, char in self._char_keys.items():
            if Input.is_key_pressed(keycode):
                if (len(self._name) < self.MAX_NAME_LENGTH
                        and char in self.ALLOWED_CHARS):
                    self._name += char
                break  # one character per frame is plenty

    def _confirm(self) -> None:
        self._result = self._name.strip() or self.DEFAULT_NAME
        self._fade_out = Transition(650)

    # ----- loop -----

    def show(self) -> str:
        """Runs its own mlx loop until Enter/Escape confirms a name.
        Blocks until Renderer.close_request() fires."""

        def frame(_param):
            Assets.update()

            Input.process_events()
            self._handle_text_input()

            root = self._build_root()

            # Arrange to the FULL window rect, not root.measure(). Box
            # only paints its background_color across the rect it was
            # arrange()'d into — sizing it to its own measured content
            # (then centering that small rect on screen) leaves the
            # baked level geometry from before visible around the
            # edges. VBox's justify="center" still centers the actual
            # content within the full rect, same as Canvas does for
            # MainMenu.
            Renderer.clear(0xFF101018)
            root.arrange(0, 0, Renderer.width, Renderer.height)
            root.render(Renderer)

            if self._fade_in is not None:
                self._fade_in.draw_fade_in(Renderer)
                if self._fade_in.done:
                    self._fade_in = None

            if self._fade_out is not None:
                self._fade_out.draw_fade_out(Renderer)
                if self._fade_out.done:
                    Renderer.close_request()

            Renderer.render_present()

            # LAST — same frame-order note as MainMenu/LevelInstance:
            # everything above needs PRESSED/RELEASED still intact.
            Input.update()

        Renderer.hook_loop(frame)
        self._logger.info("Entering end screen loop.")
        Renderer.loop()

        return self._result or self.DEFAULT_NAME
