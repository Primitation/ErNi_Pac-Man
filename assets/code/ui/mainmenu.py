"""Main menu screen."""

from typing import Any, Callable

from Engine import Assets, Input, Log, Renderer
from Engine.UISubsystem.uisubsystem import (
    BitmapText,
    Canvas,
    VBox,
    HBox,
    Text,
    Button,
    Spacer
)
from assets.code.ui.font_config import (
    ARCADE_FONT_PATH as BUTTON_FONT_PATH,
    ARCADE_FONT_CHARSET as BUTTON_FONT_CHARSET,
    ARCADE_FONT_CHAR_WIDTH as BUTTON_FONT_CHAR_WIDTH,
    ARCADE_FONT_CHAR_HEIGHT as BUTTON_FONT_CHAR_HEIGHT,
    ARCADE_FONT_COLUMNS as BUTTON_FONT_COLUMNS,
)
from game.game_instance.score import Scores
from assets.code.ui.screen_transition import PacmanTransition as Transition


class MainMenu:
    """Call .show() to run the menu loop."""

    def __init__(self, scores: Scores) -> None:
        """Initialize main menu.

        Args:
            scores: scores
        """
        self._logger = Log.get("menu")
        self._result: str | None = None
        self._font_texture = Assets.load(BUTTON_FONT_PATH)

        self._fade_in: Transition | None = Transition(650)
        self._fade_out: Transition | None = None

        self._scores = scores
        self.SHOW_MAX_SCORES = 10

        self.canvas = Canvas(0, 0, Renderer.width, Renderer.height)
        self._menu_root = self._build_menu_root()
        self._options_root = self._build_options_root()
        self._scores_root = self._build_scores_root()
        self._instructions_root = self._build_instructions_root()
        self.canvas.set_root(self._menu_root)

        Renderer.on_resize(self._on_resize)

    def _button(
        self,
        label: str,
        callback: Callable[[], None],
        min_width: int = 220,
        min_height: int = 48,
        font_scale: int = 10
    ) -> Button:
        """Button.

        Args:
            label: label
            callback: callback
            None]: None]
            min_width: min width
            min_height: min height
            font_scale: font scale

        Returns:
            Returns button.
        """
        return Button(
            label,
            callback=callback,
            min_width=min_width,
            min_height=min_height,
            font_texture=self._font_texture,
            char_width=BUTTON_FONT_CHAR_WIDTH,
            char_height=BUTTON_FONT_CHAR_HEIGHT,
            charset=BUTTON_FONT_CHARSET,
            columns=BUTTON_FONT_COLUMNS,
            font_scale=font_scale,
            color_normal=0xFF000000,
            color_focused=0xFFFFFF00
        )

    def _label(self, text: str, text_scale: float = 2.0) -> BitmapText:
        """Label.

        Args:
            text: text
            text_scale: text scale

        Returns:
            Returns label.
        """
        return BitmapText(
            text,
            self._font_texture,
            char_width=BUTTON_FONT_CHAR_WIDTH,
            char_height=BUTTON_FONT_CHAR_HEIGHT,
            charset=BUTTON_FONT_CHARSET,
            columns=BUTTON_FONT_COLUMNS,
            scale=text_scale,
        )

    def _build_menu_root(self) -> VBox:
        """Build menu root.

        Returns:
            Returns build menu root.
        """
        root = VBox(spacing=24, justify="center", background_color=0xFF000000)

        root.add(
            Text("PACENGINE", color=0x00FFEE55, char_width=12, char_height=20),
            align="center",
        )
        root.add(Spacer(height=10))

        buttons = VBox(spacing=12, justify="center")
        buttons.add(self._button("PLAY", self._on_play), align="center")
        buttons.add(self._button("SCORES", self._on_scores), align="center")
        buttons.add(self._button("INSTRUCTIONS", self._on_instructions),
                    align="center")
        buttons.add(self._button("QUIT", self._on_quit), align="center")
        root.add(buttons, align="center")

        return root

    def _build_options_root(self) -> VBox:
        """Build options root.

        Returns:
            Returns build options root.
        """
        root = VBox(spacing=20, justify="center")
        root.add(
            Text("OPTIONS", color=0x00FFEE55, char_width=10, char_height=18),
            align="center"
        )
        root.add(Spacer(height=10))

        self._music_label = Text(f"Music: {self.music_volume}%",
                                 color=0x00FFFFFF)
        music_row = HBox(spacing=10, justify="center")
        music_row.add(Button("-", callback=self._on_music_down, min_width=40,
                             min_height=40))
        music_row.add(self._music_label, align="center")
        music_row.add(Button("+", callback=self._on_music_up, min_width=40,
                             min_height=40))
        root.add(music_row, align="center")

        self._sfx_label = Text(f"SFX:   {self.sfx_volume}%", color=0x00FFFFFF)
        sfx_row = HBox(spacing=10, justify="center")
        sfx_row.add(Button("-", callback=self._on_sfx_down, min_width=40,
                           min_height=40))
        sfx_row.add(self._sfx_label, align="center")
        sfx_row.add(Button("+", callback=self._on_sfx_up, min_width=40,
                           min_height=40))
        root.add(sfx_row, align="center")

        root.add(Spacer(height=10))
        root.add(Button("Back", callback=self._on_back, min_width=140,
                        min_height=42), align="center")

        return root

    def _build_scores_root(self) -> VBox:
        """Build scores root.

        Returns:
            Returns build scores root.
        """
        root = VBox(spacing=20, justify="center", background_color=0xFF000000)
        root.add(self._label("SCORES", text_scale=10.0), align="center")
        text_scale = 7.0
        for rank, player_score in enumerate(
                self._scores.get_top_scores(self.SHOW_MAX_SCORES)):
            root.add(
                self._label(
                    f"{rank + 1} {player_score[0]} - {player_score[1]}",
                    text_scale=text_scale
                ),
                align="center"
            )
            text_scale = max(4.0, text_scale - 1)
        root.add(Spacer(height=10))

        root.add(self._button("BACK", callback=self._on_back), align="center")
        return root

    def _build_instructions_root(self) -> VBox:
        """Build instructions root.

        Returns:
            Returns build instructions root.
        """
        root = VBox(spacing=20, justify="center", background_color=0xFF000000)
        root.add(self._label("INSTRUCTIONS", text_scale=8.0), align="center")
        instructions = [
            "RULES",
            "WIN - EAT ALL PACGUMS",
            "LOSE - NO MORE LIVE OR TIME AT 0",
            "LOSE LIVE - NON EDIBLE GHOST ON PACMAN",
            "EDIBLE GHOST - SHORT DURATION AFTER EATING A SUPER-PACGUM",
            "SCORE - EAT PACGUM / SUPER-PACGUM / EDIBLE GHOST",
            "",
            "COMMANDS",
            "WASD - MOVE",
            "P - PAUSE",
            "E - EXTRA LIVE",
            "I - INVINSIBLE",
            "U - SPEED UP",
            "Y - SPEED DOWN",
            "G - GHOSTS FREEZE",
            "L - LEVEL WIN",
            "T - TIME STOP",
        ]
        for instruction in instructions:
            root.add(self._label(instruction, text_scale=2.0), align="center")
        root.add(Spacer(height=10))

        root.add(self._button("BACK", callback=self._on_back), align="center")
        return root

    music_volume = 80
    sfx_volume = 80

    def _on_music_down(self) -> None:
        """Action on music down."""
        self.music_volume = max(0, self.music_volume - 10)
        self._music_label.text = f"Music: {self.music_volume}%"

    def _on_music_up(self) -> None:
        """Action on music up."""
        self.music_volume = min(100, self.music_volume + 10)
        self._music_label.text = f"Music: {self.music_volume}%"

    def _on_sfx_down(self) -> None:
        """Action on sfx down."""
        self.sfx_volume = max(0, self.sfx_volume - 10)
        self._sfx_label.text = f"SFX:   {self.sfx_volume}%"

    def _on_sfx_up(self) -> None:
        """Action on sfx up."""
        self.sfx_volume = min(100, self.sfx_volume + 10)
        self._sfx_label.text = f"SFX:   {self.sfx_volume}%"

    def _on_options(self) -> None:
        """Action on options button."""
        self.canvas.set_root(self._options_root)

    def _on_scores(self) -> None:
        """Action on scores button."""
        self.canvas.set_root(self._scores_root)

    def _on_instructions(self) -> None:
        """Action on instructions button."""
        self.canvas.set_root(self._instructions_root)

    def _on_back(self) -> None:
        """Action on back button."""
        self.canvas.set_root(self._menu_root)

    def _on_play(self) -> None:
        """Action on play button."""
        self._close("play")

    def _on_quit(self) -> None:
        """Action on quit button."""
        self._close("quit")

    def _close(self, result: str) -> None:
        """Close.

        Args:
            result: result type.
        """
        self._result = result
        self._fade_out = Transition(650)

    def _on_resize(self, win_ptr: Any, width: int, height: int) -> None:
        """Action on resize."""
        self.canvas.set_rect(0, 0, width, height)

    def show(self) -> str:
        """Runs its own mlx loop until Play/Quit is chosen.

        Returns:
            Returns string show.
        """

        def frame(_param: Any) -> None:
            """Frame update.

            Args:
                _param: parameter
            """
            Assets.update()

            Input.process_events()
            if self._fade_out is None:
                self.canvas.update()
            Input.process_actions()

            Renderer.clear(0xFF101018)
            self.canvas.render(Renderer)

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
        self._logger.info("Entering menu loop.")
        Renderer.loop()

        return self._result or "quit"
