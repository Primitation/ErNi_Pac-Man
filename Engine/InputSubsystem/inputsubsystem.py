# inputsubsystem.py (continued from where it left off)
from enum import Enum, auto
from typing import Dict, Set, Optional, Callable, List, Tuple
from dataclasses import dataclass
import queue
import threading
from .. import Log


class KeyState(Enum):
    """Represents the state of a key or button"""
    IDLE = auto()
    PRESSED = auto()
    HELD = auto()
    RELEASED = auto()


class MouseButton(Enum):
    LEFT = 1
    RIGHT = 2
    MIDDLE = 3
    WHEEL_UP = 4
    WHEEL_DOWN = 5


@dataclass
class InputEvent:
    """Represents an input event with context"""
    key: Optional[int] = None
    button: Optional[MouseButton] = None
    position: Optional[Tuple[int, int]] = None
    value: Optional[float] = None
    modifiers: Optional[List[str]] = None
    timestamp: float = 0.0


class InputSubsystem:
    """MLX-based Input Subsystem."""

    KEY_PRESS = 2
    KEY_RELEASE = 3
    BUTTON_PRESS = 4
    BUTTON_RELEASE = 5
    MOTION_NOTIFY = 6
    EXPOSE = 12
    DESTROY_NOTIFY = 33

    KEY_PRESS_MASK = 1 << 0
    BUTTON_RELEASE_MASK = 1 << 3
    POINTER_MOTION_MASK = 1 << 6

    KEYS = {
        'a': 97, 'b': 98, 'c': 99, 'd': 100,
        'e': 101, 'f': 102, 'g': 103, 'h': 104,
        'i': 105, 'j': 106, 'k': 107, 'l': 108,
        'm': 109, 'n': 110, 'o': 111, 'p': 112,
        'q': 113, 'r': 114, 's': 115, 't': 116,
        'u': 117, 'v': 118, 'w': 119, 'x': 120,
        'y': 121, 'z': 122,
        '0': 48, '1': 49, '2': 50, '3': 51, '4': 52,
        '5': 53, '6': 54, '7': 55, '8': 56, '9': 57,
        'space': 32,
        'tab': 65289,
        'enter': 65293,
        'escape': 65307,
        'backspace': 65288,
        'delete': 65535,
        'insert': 65379,
        'left': 65361,
        'up': 65362,
        'right': 65363,
        'down': 65364,
        'page_up': 65365,
        'page_down': 65366,
        'home': 65360,
        'end': 65367,
        'shift': 65505,
        'ctrl': 65507,
        'alt': 65513,
        'meta': 65515,
        'f1': 65470,
        'f2': 65471,
        'f3': 65472,
        'f4': 65473,
        'f5': 65474,
        'f6': 65475,
        'f7': 65476,
        'f8': 65477,
        'f9': 65478,
        'f10': 65479,
        'f11': 65480,
        'f12': 65481,
    }

    KEY_NAMES = {v: k for k, v in KEYS.items()}

    def __init__(self):
        self._logger = Log.get("input")
        self._initialized = False
        self._mlx_callbacks = {}

        self.key_states: Dict[int, KeyState] = {}
        self.active_keys: Set[int] = set()

        self.mouse_position: Tuple[int, int] = (0, 0)
        self.mouse_buttons: Dict[MouseButton, KeyState] = {
            MouseButton.LEFT: KeyState.IDLE,
            MouseButton.MIDDLE: KeyState.IDLE,
            MouseButton.RIGHT: KeyState.IDLE,
        }
        self.mouse_wheel: float = 0

        self.modifiers: Set[str] = set()
        self.modifier_map = {
            65505: 'shift', 65506: 'shift',
            65507: 'ctrl', 65508: 'ctrl',
            65513: 'alt', 65514: 'alt',
            65515: 'meta', 65516: 'meta',
        }

        self.action_mappings: Dict[str, List[int]] = {}
        self.combo_actions: Set[str] = set()

        self.key_press_callbacks: Dict[int, List[Callable]] = {}
        self.key_release_callbacks: Dict[int, List[Callable]] = {}
        self.mouse_callbacks: Dict[MouseButton, List[Callable]] = {}
        self.action_callbacks: Dict[str, List[Callable]] = {}
        self.any_key_callbacks: List[Callable] = []
        self.any_mouse_callbacks: List[Callable] = []
        self.close_callbacks: List[Callable] = []

        self.input_buffer: List[InputEvent] = []
        self.buffer_size: int = 100
        self.recording: bool = False

        self._frame_count = 0
        self._debug_print_keys = False
        self._event_queue = queue.SimpleQueue()
        self._state_lock = threading.Lock()

    def init(self) -> None:
        from .. import Renderer

        if self._initialized:
            return

        self._renderer = Renderer
        self.mlx = Renderer.mlx
        self.mlx_ptr = Renderer.mlx_ptr
        self.win_ptr = Renderer.win_ptr

        self.mlx.mlx_do_key_autorepeatoff(self.mlx_ptr)

        self._setup_input()
        self._register_mlx_hooks()

        self._initialized = True
        self._logger.info("Input subsystem initialized")
        self._renderer.on_resize(self.resize)

    def resize(self, win_ptr, width: int, height: int) -> None:
        self.win_ptr = win_ptr
        self._register_mlx_hooks()
        self._logger.info("Input hooks rebound "
                          f"to new window ({width}x{height})")

    def start_input_thread(self) -> None:
        pass

    def stop_input_thread(self) -> None:
        pass

    def close(self) -> None:
        if self._initialized and self.mlx_ptr is not None:
            self.mlx.mlx_do_key_autorepeaton(self.mlx_ptr)

    def _register_mlx_hooks(self) -> None:
        self._mlx_callbacks = {}

        def on_key_press(keycode, param):
            self._event_queue.put(("key_press", keycode))

        self._mlx_callbacks["key_press"] = on_key_press
        self.mlx.mlx_hook(
            self.win_ptr,
            self.KEY_PRESS,
            self.KEY_PRESS_MASK,
            on_key_press,
            self
        )

        def on_key_release(keycode, param):
            self._event_queue.put(("key_release", keycode))

        self._mlx_callbacks["key_release"] = on_key_release
        self.mlx.mlx_key_hook(
            self.win_ptr,
            on_key_release,
            self
        )

        def on_mouse_press(button, x, y, param):
            self._event_queue.put(("mouse_press", button, x, y))

        self._mlx_callbacks["mouse_press"] = on_mouse_press
        self.mlx.mlx_mouse_hook(
            self.win_ptr,
            on_mouse_press,
            self
        )

        def on_mouse_release(button, x, y, param):
            self._event_queue.put(("mouse_release", button, x, y))

        self._mlx_callbacks["mouse_release"] = on_mouse_release
        self.mlx.mlx_hook(
            self.win_ptr,
            self.BUTTON_RELEASE,
            self.BUTTON_RELEASE_MASK,
            on_mouse_release,
            self
        )

        def on_mouse_motion(x, y, param):
            self._event_queue.put(("motion", x, y))

        self._mlx_callbacks["mouse_motion"] = on_mouse_motion
        self.mlx.mlx_hook(
            self.win_ptr,
            self.MOTION_NOTIFY,
            self.POINTER_MOTION_MASK,
            on_mouse_motion,
            self
        )

        def on_destroy(param):
            for callback in self.close_callbacks:
                callback()

        self._mlx_callbacks["destroy"] = on_destroy
        self.mlx.mlx_hook(
            self.win_ptr,
            self.DESTROY_NOTIFY,
            0,
            on_destroy,
            self
        )

    def _setup_input(self) -> None:
        self.bind_action("quit", [self.KEYS["escape"]])
        self.bind_action("confirm", [self.KEYS["enter"], self.KEYS["space"]])
        self.bind_action("cancel", [self.KEYS["escape"]])
        self.bind_action("up", [self.KEYS["up"], self.KEYS["w"]])
        self.bind_action("down", [self.KEYS["down"], self.KEYS["s"]])
        self.bind_action("left", [self.KEYS["left"], self.KEYS["a"]])
        self.bind_action("right", [self.KEYS["right"], self.KEYS["d"]])
        self.bind_action("pause", [self.KEYS["p"]])
        self.bind_action("invinsible", [self.KEYS["i"]])
        self.bind_action("level win", [self.KEYS["l"]])
        self.bind_action("ghost freeze", [self.KEYS["g"]])
        self.bind_action("extra live", [self.KEYS["e"]])
        self.bind_action("increase speed", [self.KEYS["u"]])
        self.bind_action("decrease speed", [self.KEYS["y"]])
        self.bind_action("time stop", [self.KEYS["t"]])
        self.bind_action("quit to menu", [self.KEYS["m"]])

        from .. import Renderer
        self.register_action_callback("quit", Renderer.close_request)
        self.on_close(Renderer.close_request)
        self._logger.debug("Default input bindings set up")

    def _handle_key_press(self, keycode: int, param) -> None:
        self._set_key_state(keycode, True)

    def _handle_key_release(self, keycode: int, param) -> None:
        self._set_key_state(keycode, False)

    def _set_key_state(self, keycode: int, pressed: bool) -> None:
        with self._state_lock:
            if pressed:
                self.key_states[keycode] = KeyState.PRESSED
                self.active_keys.add(keycode)

                if keycode in self.modifier_map:
                    self.modifiers.add(self.modifier_map[keycode])

                if self.recording:
                    self.input_buffer.append(InputEvent(
                        key=keycode,
                        modifiers=list(self.modifiers)
                    ))
                    if len(self.input_buffer) > self.buffer_size:
                        self.input_buffer.pop(0)

                if keycode in self.key_press_callbacks:
                    for callback in self.key_press_callbacks[keycode]:
                        callback(KeyState.PRESSED, keycode)

                for callback in self.any_key_callbacks:
                    callback(keycode, KeyState.PRESSED)
            else:
                if keycode in self.key_states:
                    self.key_states[keycode] = KeyState.RELEASED
                    self.active_keys.discard(keycode)

                    if keycode in self.modifier_map:
                        self.modifiers.discard(self.modifier_map[keycode])

                    if keycode in self.key_release_callbacks:
                        for callback in self.key_release_callbacks[keycode]:
                            callback(KeyState.RELEASED, keycode)

                    for callback in self.any_key_callbacks:
                        callback(keycode, KeyState.RELEASED)

    def _handle_mouse_press(self, button: int, x: int, y: int, param) -> None:
        self.mouse_position = (x, y)

        if button == 4:
            self.mouse_wheel = 1
            return
        elif button == 5:
            self.mouse_wheel = -1
            return

        try:
            mouse_button = MouseButton(button)
        except ValueError:
            return

        self.mouse_buttons[mouse_button] = KeyState.PRESSED

        if mouse_button in self.mouse_callbacks:
            for callback in self.mouse_callbacks[mouse_button]:
                callback(KeyState.PRESSED, x, y)

        for callback in self.any_mouse_callbacks:
            callback(mouse_button, KeyState.PRESSED, x, y)

    def _handle_mouse_release(self, button: int, x: int,
                              y: int, param) -> None:
        self.mouse_position = (x, y)

        try:
            mouse_button = MouseButton(button)
        except ValueError:
            return

        self.mouse_buttons[mouse_button] = KeyState.RELEASED

        if mouse_button in self.mouse_callbacks:
            for callback in self.mouse_callbacks[mouse_button]:
                callback(KeyState.RELEASED, x, y)

        for callback in self.any_mouse_callbacks:
            callback(mouse_button, KeyState.RELEASED, x, y)

    def _handle_motion(self, x: int, y: int, param) -> None:
        self.mouse_position = (x, y)

    def update(self) -> None:
        with self._state_lock:
            self._frame_count += 1

            for key in list(self.key_states.keys()):
                if self.key_states[key] == KeyState.PRESSED:
                    self.key_states[key] = KeyState.HELD
                elif self.key_states[key] == KeyState.RELEASED:
                    self.key_states[key] = KeyState.IDLE

            for button in self.mouse_buttons:
                if self.mouse_buttons[button] == KeyState.PRESSED:
                    self.mouse_buttons[button] = KeyState.HELD
                elif self.mouse_buttons[button] == KeyState.RELEASED:
                    self.mouse_buttons[button] = KeyState.IDLE

            self.mouse_wheel = 0

    def process_events(self) -> None:
        while True:
            try:
                event = self._event_queue.get_nowait()
            except queue.Empty:
                break

            event_type = event[0]

            if event_type == "key_press":
                self._handle_key_press(event[1], None)
            elif event_type == "key_release":
                self._handle_key_release(event[1], None)
            elif event_type == "mouse_press":
                self._handle_mouse_press(event[1], event[2], event[3], None)
            elif event_type == "mouse_release":
                self._handle_mouse_release(event[1], event[2], event[3], None)
            elif event_type == "motion":
                self._handle_motion(event[1], event[2], None)
            elif event_type == "close":
                for callback in self.close_callbacks:
                    callback()

    def is_key_pressed(self, key: int) -> bool:
        return self.key_states.get(key) == KeyState.PRESSED

    def is_key_held(self, key: int) -> bool:
        return self.key_states.get(key) in (KeyState.PRESSED, KeyState.HELD)

    def is_key_released(self, key: int) -> bool:
        return self.key_states.get(key) == KeyState.RELEASED

    def is_key_down(self, key: int) -> bool:
        return key in self.active_keys

    def is_any_key_pressed(self, keys: List[int]) -> bool:
        return any(self.is_key_pressed(key) for key in keys)

    def is_any_key_held(self, keys: List[int]) -> bool:
        return any(self.is_key_held(key) for key in keys)

    def is_modifier_active(self, modifier: str) -> bool:
        return modifier in self.modifiers

    def get_mouse_position(self) -> Tuple[int, int]:
        return self.mouse_position

    def is_mouse_button_pressed(self, button: MouseButton) -> bool:
        return self.mouse_buttons.get(button) == KeyState.PRESSED

    def is_mouse_button_held(self, button: MouseButton) -> bool:
        return self.mouse_buttons.get(button) in (KeyState.PRESSED,
                                                  KeyState.HELD)

    def is_mouse_button_released(self, button: MouseButton) -> bool:
        return self.mouse_buttons.get(button) == KeyState.RELEASED

    def get_mouse_wheel(self) -> float:
        return self.mouse_wheel

    def bind_action(self, action_name: str, keys: List[int]) -> None:
        self.action_mappings[action_name] = keys
        self.combo_actions.discard(action_name)
        self._logger.debug(f"Bound action '{action_name}' to keys: {keys}")

    def bind_action_combo(self, action_name: str, combo: List[int]) -> None:
        self.action_mappings[action_name] = combo
        self.combo_actions.add(action_name)
        self._logger.debug(f"Bound combo action '{action_name}'"
                           f" to keys: {combo}")

    def is_action_triggered(self, action_name: str) -> bool:
        if action_name not in self.action_mappings:
            return False

        keys = self.action_mappings[action_name]

        if action_name in self.combo_actions and len(keys) > 1:
            if all(self.is_key_held(key) for key in keys):
                return any(self.is_key_pressed(key) for key in keys)
            return False

        return any(self.is_key_pressed(key) for key in keys)

    def is_action_held(self, action_name: str) -> bool:
        if action_name not in self.action_mappings:
            return False

        keys = self.action_mappings[action_name]

        if action_name in self.combo_actions:
            return all(self.is_key_held(key) for key in keys)

        return any(self.is_key_held(key) for key in keys)

    def is_action_released(self, action_name: str) -> bool:
        if action_name not in self.action_mappings:
            return False

        keys = self.action_mappings[action_name]
        return any(self.is_key_released(key) for key in keys)

    def register_action_callback(self, action_name: str,
                                 callback: Callable) -> None:
        if action_name not in self.action_callbacks:
            self.action_callbacks[action_name] = []
        self.action_callbacks[action_name].append(callback)
        self._logger.debug(f"Registered callback for action '{action_name}'")

    def remove_action_callback(self, action_name: str,
                               callback: Callable) -> None:
        if action_name not in self.action_callbacks:
            return
        self.action_callbacks[action_name].remove(callback)
        self._logger.debug(f"Unregistered callback for action '{action_name}'")

    def process_actions(self) -> None:
        for action_name in self.action_callbacks:
            if self.is_action_triggered(action_name):
                for callback in self.action_callbacks[action_name]:
                    callback()

    def on_key_press(self, key: int, callback: Callable) -> None:
        if key not in self.key_press_callbacks:
            self.key_press_callbacks[key] = []
        self.key_press_callbacks[key].append(callback)

    def on_key_release(self, key: int, callback: Callable) -> None:
        if key not in self.key_release_callbacks:
            self.key_release_callbacks[key] = []
        self.key_release_callbacks[key].append(callback)

    def on_any_key(self, callback: Callable) -> None:
        self.any_key_callbacks.append(callback)

    def on_mouse_click(self, button: MouseButton, callback: Callable) -> None:
        if button not in self.mouse_callbacks:
            self.mouse_callbacks[button] = []
        self.mouse_callbacks[button].append(callback)

    def on_any_mouse(self, callback: Callable) -> None:
        self.any_mouse_callbacks.append(callback)

    def on_close(self, callback: Callable) -> None:
        self.close_callbacks.append(callback)

    def start_recording(self) -> None:
        self.recording = True
        self.input_buffer.clear()
        self._logger.info("Started input recording")

    def stop_recording(self) -> List[InputEvent]:
        self.recording = False
        self._logger.info(f"Stopped input recording: {len(self.input_buffer)}"
                          " events")
        return self.input_buffer.copy()

    def play_recorded_input(self, events: List[InputEvent],
                            callback: Callable) -> None:
        for event in events:
            callback(event)

    def clear_states(self) -> None:
        self.key_states.clear()
        self.active_keys.clear()
        self.modifiers.clear()
        for button in self.mouse_buttons:
            self.mouse_buttons[button] = KeyState.IDLE
        self.mouse_wheel = 0
        self._logger.debug("Cleared all input states")

    def get_key_name(self, keycode: int) -> str:
        return self.KEY_NAMES.get(keycode, f"unknown_{keycode}")

    def get_active_keys(self) -> List[str]:
        return [self.get_key_name(key) for key in self.active_keys]

    def get_debug_info(self) -> str:
        active_keys = self.get_active_keys()
        active_mods = list(self.modifiers)
        mouse_pos = self.mouse_position
        return (f"Active Keys: {active_keys}\n"
                f"Modifiers: {active_mods}\n"
                f"Mouse: {mouse_pos}\n"
                f"Mouse Buttons: {self.mouse_buttons}")


Input = InputSubsystem()
