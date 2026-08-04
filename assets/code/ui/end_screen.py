"""End screen — win/lose result page."""

from typing import Any, Dict

from Engine import Assets, Input, Log, Renderer
from Engine.UISubsystem.uisubsystem import VBox, HBox, BitmapText, Spacer
from assets.code.ui.font_config import (
    ARCADE_FONT_PATH,
    ARCADE_FONT_CHARSET,
    ARCADE_FONT_CHAR_WIDTH,
    ARCADE_FONT_CHAR_HEIGHT,
    ARCADE_FONT_COLUMNS,
)
from assets.code.ui.screen_transition import PacmanTransition as Transition


class EndScreen:
    """Call .show() to run the loop."""

    MAX_NAME_LENGTH = 10
    ALLOWED_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        "abcdefghijklmnopqrstuvwxyz0123456789 ")
    DEFAULT_NAME = "PLAYER"

    def __init__(self, won: bool, score: int):
        self._logger = Log.get("menu")
        self._font_texture = Assets.load(ARCADE_FONT_PATH)
        self._won = won
        self._score = score
        self._name = ""
        self._result: str | None = None
        self._char_keys = self._build_char_keys()

        self._fade_in: Transition | None = Transition(650)
        self._fade_out: Transition | None = None

    @staticmethod
    def _build_char_keys() -> Dict[Any, str]:
        """keycode -> character it types (lowercase by default; the
        letter is upper-cased at input time if Shift is held)."""
        keys = {}
        for ch in "abcdefghijklmnopqrstuvwxyz":
            keys[Input.KEYS[ch]] = ch
        for ch in "0123456789":
            keys[Input.KEYS[ch]] = ch
        keys[Input.KEYS["space"]] = " "
        return keys

    @staticmethod
    def _shift_held() -> bool:
        """Best-effort check for a held Shift key. Falls back to False
        (i.e. lowercase) if the InputSubsystem doesn't expose a
        continuous key-down query or a shift keycode."""
        is_down = getattr(Input, "is_key_down", None)
        if is_down is None:
            return False
        shift_key = Input.KEYS.get("shift") or Input.KEYS.get("lshift") \
            or Input.KEYS.get("rshift")
        if shift_key is None:
            return False
        return bool(is_down(shift_key))

    def _label(self, text: str, scale: float = 3.0) -> BitmapText:
        return BitmapText(
            text,
            self._font_texture,
            char_width=ARCADE_FONT_CHAR_WIDTH,
            char_height=ARCADE_FONT_CHAR_HEIGHT,
            charset=ARCADE_FONT_CHARSET,
            columns=ARCADE_FONT_COLUMNS,
            scale=scale,
        )

    def _build_root(self) -> VBox:
        root = VBox(spacing=20, justify="center", background_color=0xFF000000)

        title = "WINNER" if self._won else "GAME OVER"
        root.add(self._label(title, scale=8.0), align="center")
        root.add(Spacer(height=10))
        root.add(self._label(f"SCORE {self._score}",
                 scale=5.0), align="center")

        root.add(Spacer(height=20))
        root.add(self._label("ENTER YOUR NAME", scale=3.0), align="center")

        cursor = "_" if len(self._name) < self.MAX_NAME_LENGTH else ""
        name_box = HBox(padding=10, background_color=0xFF222222)
        name_box.add(self._label(self._name + cursor, scale=4.0),
                     align="center")
        root.add(name_box, align="center")

        root.add(Spacer(height=10))
        hint = (
            "ENTER TO CONFIRM - BACKSPACE TO DELETE"
            if self._name else "A-Z 0-9 SPACE - 10 CHAR MAX"
        )
        root.add(self._label(hint, scale=2.0), align="center")

        return root

    def _handle_text_input(self) -> None:
        if self._fade_out is not None:
            return

        if Input.is_key_pressed(Input.KEYS["backspace"]):
            self._name = self._name[:-1]
            return

        if Input.is_key_pressed(Input.KEYS["enter"]):
            self._confirm()
            return

        if Input.is_key_pressed(Input.KEYS["escape"]):
            self._confirm()
            return

        shift = self._shift_held()
        for keycode, char in self._char_keys.items():
            if Input.is_key_pressed(keycode):
                if char.isalpha() and shift:
                    char = char.upper()
                if (len(self._name) < self.MAX_NAME_LENGTH
                        and char in self.ALLOWED_CHARS):
                    self._name += char
                break

    def _confirm(self) -> None:
        self._result = self._name.strip() or self.DEFAULT_NAME
        self._fade_out = Transition(650)

    def show(self) -> str:
        """Runs its own mlx loop until Enter/Escape confirms a name."""

        def frame(_param: Any) -> None:
            Assets.update()

            Input.process_events()
            self._handle_text_input()

            root = self._build_root()

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

            Input.update()

        Renderer.hook_loop(frame)
        self._logger.info("Entering end screen loop.")
        Renderer.loop()

        return self._result or self.DEFAULT_NAME
