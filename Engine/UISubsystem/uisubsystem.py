"""
UI Subsystem v2: a small widget tree (Canvas -> Box(es) -> leaf widgets),
laid out with a flexbox-lite algorithm and drawn in screen space.
"""

from typing import Any, Callable, List, Optional, TYPE_CHECKING, Tuple, Union
from .. import Log

if TYPE_CHECKING:
    from ..InputSubsystem.inputsubsystem import InputSubsystem

CHAR_WIDTH = 6
CHAR_HEIGHT = 10


class Widget:
    """Base class for anything placed in the UI tree."""

    def __init__(self) -> None:
        self.rect: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self.visible: bool = True

    def measure(self) -> Tuple[int, int]:
        """Return this widget's own desired (width, height)."""
        return (0, 0)

    def arrange(self, x: int, y: int, w: int, h: int) -> None:
        """Called by the parent with the space it decided to give."""
        self.rect = (x, y, w, h)

    def render(self, renderer: Any) -> None:
        pass

    def collect_focusable(self, out: List["Button"]) -> None:
        """Containers recurse into children; Button appends itself."""
        pass

    @property
    def center(self) -> Tuple[float, float]:
        x, y, w, h = self.rect
        return (x + w / 2.0, y + h / 2.0)


class Box(Widget):
    """Flexbox-lite container. Don't use directly — use HBox/VBox."""

    def __init__(
        self,
        orientation: str,
        padding: int = 0,
        spacing: int = 0,
        justify: str = "start",
        background_color: Optional[int] = None
    ):
        super().__init__()
        assert orientation in ("horizontal", "vertical")
        self.orientation = orientation
        self.padding = padding
        self.spacing = spacing
        self.justify = justify
        self.background_color = background_color
        self._children: List[Tuple[Widget, float, str]] = []

    def add(self, widget: Widget, weight: float = 0.0,
            align: str = "stretch") -> Widget:
        """align: 'start' | 'center' | 'end' | 'stretch'."""
        self._children.append((widget, weight, align))
        return widget

    def remove(self, widget: Widget) -> None:
        self._children = [c for c in self._children if c[0] is not widget]

    def clear(self) -> None:
        self._children.clear()

    def measure(self) -> Tuple[int, int]:
        if not self._children:
            return (self.padding * 2, self.padding * 2)

        main_total = 0
        cross_max = 0
        for widget, _weight, _align in self._children:
            if not widget.visible:
                continue
            w, h = widget.measure()
            main, cross = (w, h) if self.orientation == "horizontal" else (h,
                                                                           w)
            main_total += main
            cross_max = max(cross_max, cross)

        visible_count = sum(1 for w, _, _ in self._children if w.visible)
        main_total += self.spacing * max(0, visible_count - 1)
        main_total += self.padding * 2
        cross_max += self.padding * 2

        if self.orientation == "horizontal":
            return (main_total, cross_max)
        return (cross_max, main_total)

    def arrange(self, x: int, y: int, w: int, h: int) -> None:
        self.rect = (x, y, w, h)

        visible = [(widget, weight, align) for widget, weight, align
                   in self._children if widget.visible]
        if not visible:
            return

        inner_x = x + self.padding
        inner_y = y + self.padding
        inner_w = max(0, w - self.padding * 2)
        inner_h = max(0, h - self.padding * 2)
        available_main = inner_w if self.orientation == "horizontal" \
            else inner_h
        available_cross = inner_h if self.orientation == "horizontal" \
            else inner_w

        sizes = []
        total_weight = 0.0
        for widget, weight, _align in visible:
            mw, mh = widget.measure()
            main = mw if self.orientation == "horizontal" else mh
            sizes.append(main)
            total_weight += weight

        preferred_main_total = sum(sizes) + self.spacing * max(0, len(visible)
                                                               - 1)
        leftover = available_main - preferred_main_total

        lead = 0
        extra_gap = 0
        if total_weight <= 0 and leftover > 0:
            if self.justify == "center":
                lead = leftover // 2
            elif self.justify == "end":
                lead = leftover
            elif self.justify == "space_between" and len(visible) > 1:
                extra_gap = leftover // (len(visible) - 1)

        cursor = lead
        for i, (widget, weight, align) in enumerate(visible):
            main_size = sizes[i]
            if total_weight > 0 and leftover > 0:
                main_size += int(leftover * (weight / total_weight))

            mw, mh = widget.measure()
            cross_pref = mh if self.orientation == "horizontal" else mw

            if align == "stretch":
                cross_size = available_cross
                cross_off = 0
            else:
                cross_size = min(cross_pref, available_cross)
                if align == "center":
                    cross_off = (available_cross - cross_size) // 2
                elif align == "end":
                    cross_off = available_cross - cross_size
                else:
                    cross_off = 0

            if self.orientation == "horizontal":
                widget.arrange(inner_x + cursor, inner_y + cross_off,
                               main_size, cross_size)
            else:
                widget.arrange(inner_x + cross_off, inner_y + cursor,
                               cross_size, main_size)

            cursor += main_size + self.spacing + extra_gap

    def render(self, renderer: Any) -> None:
        if not self.visible:
            return
        if self.background_color is not None:
            x, y, w, h = self.rect
            renderer.draw_rect_screen(x, y, w, h, self.background_color)
        for widget, _weight, _align in self._children:
            if widget.visible:
                widget.render(renderer)

    def collect_focusable(self, out: List["Button"]) -> None:
        if not self.visible:
            return
        for widget, _weight, _align in self._children:
            widget.collect_focusable(out)


class HBox(Box):
    """Horizontal box container."""

    def __init__(
        self,
        padding: int = 0,
        spacing: int = 0,
        justify: str = "start",
        background_color: Optional[int] = None
    ):
        super().__init__("horizontal", padding, spacing, justify,
                         background_color)


class VBox(Box):
    """Vertical box container."""

    def __init__(
        self,
        padding: int = 0,
        spacing: int = 0,
        justify: str = "start",
        background_color: Optional[int] = None
    ):
        super().__init__("vertical", padding, spacing, justify,
                         background_color)


class Spacer(Widget):
    """Empty widget for spacing."""

    def __init__(self, width: int = 0, height: int = 0):
        super().__init__()
        self._size = (width, height)

    def measure(self) -> Tuple[int, int]:
        return self._size


class Text(Widget):
    """Text drawn with mlx_string_put (debug font)."""

    def __init__(self, text: str, color: int = 0x00FFFFFF,
                 char_width: int = CHAR_WIDTH,
                 char_height: int = CHAR_HEIGHT):
        super().__init__()
        self.text = text
        self.color = color
        self.char_width = char_width
        self.char_height = char_height

    def measure(self) -> Tuple[int, int]:
        return (len(self.text) * self.char_width, self.char_height)

    def render(self, renderer: Any) -> None:
        if not self.visible or not self.text:
            return
        x, y, w, h = self.rect
        text_y = y + h // 2 + self.char_height // 2
        renderer.mlx.mlx_string_put(renderer.mlx_ptr, renderer.win_ptr,
                                    x, text_y, self.color, self.text)


class BitmapText(Widget):
    """Text drawn from a sprite-sheet font texture."""

    def __init__(
        self,
        text: str,
        font_texture: Any,
        char_width: int,
        char_height: int,
        charset: str,
        columns: Optional[int] = None,
        spacing: int = 0,
        scale: float = 1.0,
        color: Optional[int] = None,
        lowercase_scale: float = 0.72
    ):
        super().__init__()
        self.text = text
        self.font_texture = font_texture
        self.char_width = char_width
        self.char_height = char_height
        self.charset = charset
        self.columns = columns if columns is not None else len(charset)
        self.spacing = spacing
        self.scale = scale
        self.color = color
        self.lowercase_scale = lowercase_scale
        self._index = {ch: i for i, ch in enumerate(charset)}

    @property
    def cell_size(self) -> Tuple[int, int]:
        return (max(1, round(self.char_width * self.scale)),
                max(1, round(self.char_height * self.scale)))

    def _glyph_index(self, char: str) -> Tuple[Optional[int], bool]:
        """Resolve a character to a (glyph_index, is_synthesized_lowercase)
        pair. If `char` isn't in the charset but its uppercase form is,
        reuse the uppercase glyph and flag it so render() draws it
        scaled down."""
        index = self._index.get(char)
        if index is not None:
            return index, False
        upper = char.upper()
        if upper != char:
            index = self._index.get(upper)
            if index is not None:
                return index, True
        return None, False

    def measure(self) -> Tuple[int, int]:
        cw, ch = self.cell_size
        n = len(self.text)
        if n == 0:
            return (0, ch)
        return (n * cw + (n - 1) * self.spacing, ch)

    def render(self, renderer: Any) -> None:
        if not self.visible or not self.text or self.font_texture is None:
            return
        x, y, w, h = self.rect
        cw, ch = self.cell_size
        draw_y = y + (h - ch) // 2
        draw_x = x

        for char in self.text:
            index, is_lower = self._glyph_index(char)
            if index is not None:
                col = index % self.columns
                row = index // self.columns

                if is_lower:
                    # Only shrink height (not width) so the glyph still
                    # fills its cell horizontally — shrinking width too
                    # left visible gaps between consecutive lowercase
                    # characters. Sit on the baseline (cell bottom) so
                    # lowercase reads like real text.
                    gw = cw
                    gh = max(1, round(ch * self.lowercase_scale))
                    gx = draw_x
                    gy = draw_y + (ch - gh)
                else:
                    gw, gh = cw, ch
                    gx, gy = draw_x, draw_y

                renderer.draw_texture_region_screen(
                    self.font_texture,
                    col * self.char_width,
                    row * self.char_height,
                    self.char_width,
                    self.char_height,
                    gx,
                    gy,
                    gw,
                    gh,
                )
            draw_x += cw + self.spacing


class Image(Widget):
    """Image widget drawn from a texture."""

    def __init__(self, texture: Any, width: Optional[int] = None,
                 height: Optional[int] = None):
        super().__init__()
        self.texture = texture
        self._width = width
        self._height = height

    def measure(self) -> Tuple[int, int]:
        w = self._width if self._width is not None else self.texture.width
        h = self._height if self._height is not None else self.texture.height
        return (w, h)

    def render(self, renderer: Any) -> None:
        if not self.visible or self.texture is None:
            return
        x, y, w, h = self.rect
        renderer.draw_sprite_screen(self.texture, x, y, w, h)


class Button(Widget):
    """Focusable button with callback."""

    def __init__(
        self,
        label: str,
        callback: Optional[Callable[[], None]] = None,
        min_width: int = 0,
        min_height: int = 0,
        padding: int = 10,
        enabled: bool = True,
        color_normal: int = 0x88222222,
        color_focused: int = 0xCC4488FF,
        color_disabled: int = 0x44222222,
        text_color: int = 0x00FFFFFF,
        text_background_color: Optional[int] = None,
        text_background_padding: int = 4,
        font_texture: Any = None,
        char_width: int = 0,
        char_height: int = 0,
        charset: str = "",
        columns: Optional[int] = None,
        font_scale: float = 1.0
    ):
        super().__init__()
        self.callback = callback
        self.enabled = enabled
        self.padding = padding
        self.min_width = min_width
        self.min_height = min_height
        self.color_normal = color_normal
        self.color_focused = color_focused
        self.color_disabled = color_disabled
        self.text_background_color = text_background_color
        self.text_background_padding = text_background_padding

        self._text: Union[Text, BitmapText]
        if font_texture is not None:
            self._text = BitmapText(
                label, font_texture, char_width, char_height,
                charset, columns=columns, scale=font_scale,
            )
        else:
            self._text = Text(label, color=text_color)

        self.focused = False

    @property
    def label(self) -> str:
        return self._text.text

    @label.setter
    def label(self, value: str) -> None:
        self._text.text = value

    def measure(self) -> Tuple[int, int]:
        tw, th = self._text.measure()
        return (max(self.min_width, tw + self.padding * 2),
                max(self.min_height, th + self.padding * 2))

    def arrange(self, x: int, y: int, w: int, h: int) -> None:
        self.rect = (x, y, w, h)
        tw, th = self._text.measure()
        text_x = x + max(self.padding, (w - tw) // 2)
        self._text.arrange(text_x, y, w, h)

    def render(self, renderer: Any) -> None:
        if not self.visible:
            return
        x, y, w, h = self.rect
        if not self.enabled:
            color = self.color_disabled
        elif self.focused:
            color = self.color_focused
        else:
            color = self.color_normal
        renderer.draw_rect_screen(x, y, w, h, color)

        if self.text_background_color is not None:
            tw, th = self._text.measure()
            tx, _ty, _tw, _th = self._text.rect
            pad = self.text_background_padding
            bg_x = tx - pad
            bg_y = y + (h - th) // 2 - pad
            bg_w = tw + pad * 2
            bg_h = th + pad * 2
            renderer.draw_rect_screen(bg_x, bg_y, bg_w, bg_h,
                                      self.text_background_color)

        self._text.render(renderer)

    def collect_focusable(self, out: List["Button"]) -> None:
        if self.visible and self.enabled:
            out.append(self)

    def activate(self) -> None:
        if self.enabled and self.callback is not None:
            self.callback()


class Canvas:
    """Top-level UI surface: owns a screen-space rect and one root widget."""

    def __init__(self, x: int = 0, y: int = 0, width: int = 0,
                 height: int = 0):
        self._logger = Log.get("ui")
        self.x, self.y, self.width, self.height = x, y, width, height
        self.root: Optional[Widget] = None
        self.visible: bool = True
        self._focused: Optional[Button] = None
        self._input: Optional["InputSubsystem"] = None

    def _ensure_input(self) -> None:
        if self._input is None:
            from .. import Input
            self._input = Input

    def set_root(self, widget: Widget) -> None:
        self.root = widget

    def set_rect(self, x: int, y: int, width: int, height: int) -> None:
        self.x, self.y, self.width, self.height = x, y, width, height

    _DIRECTIONS = {
        "up": (0.0, -1.0),
        "down": (0.0, 1.0),
        "left": (-1.0, 0.0),
        "right": (1.0, 0.0),
    }

    def _find_neighbor(self, buttons: List[Button], current: Button,
                       direction: Tuple[float, float]) -> Optional[Button]:
        """Closest enabled button roughly in `direction` from `current`."""
        dx, dy = direction
        cx, cy = current.center
        best, best_score = None, float("inf")

        for b in buttons:
            if b is current:
                continue
            bx, by = b.center
            vx, vy = bx - cx, by - cy
            along = vx * dx + vy * dy
            if along <= 0:
                continue
            perp = abs(vx * dy - vy * dx)
            score = along + perp * 2.0
            if score < best_score:
                best_score = score
                best = b

        return best

    def update(self) -> None:
        """Call once per frame, after Input.process_events()."""
        if not self.visible or self.root is None:
            return

        self._ensure_input()
        assert self._input is not None
        input_subsystem = self._input

        buttons: List[Button] = []
        self.root.collect_focusable(buttons)

        if self._focused not in buttons:
            self._focused = buttons[0] if buttons else None

        if self._focused is not None:
            for direction, vec in self._DIRECTIONS.items():
                if input_subsystem.is_action_triggered(direction):
                    neighbor = self._find_neighbor(buttons, self._focused, vec)
                    if neighbor is not None:
                        self._focused = neighbor
                    break

            if input_subsystem.is_action_triggered("confirm"):
                self._focused.activate()

        for b in buttons:
            b.focused = (b is self._focused)

    def render(self, renderer: Any) -> None:
        if not self.visible or self.root is None:
            return
        self.root.measure()
        self.root.arrange(self.x, self.y, self.width, self.height)
        self.root.render(renderer)
