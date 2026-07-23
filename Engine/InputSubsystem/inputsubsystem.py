from enum import Enum, auto
from typing import Dict, Set, Optional, Callable, Any, List, Tuple
from dataclasses import dataclass, field
from .. import Log


class KeyState(Enum):
    """Represents the state of a key or button"""
    IDLE = auto()
    PRESSED = auto()      # Just pressed this frame
    HELD = auto()         # Being held down
    RELEASED = auto()     # Just released this frame


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
    """
    MLX-based Input Subsystem that integrates with the Renderer.
    Must be initialized after Renderer.init() is called.
    """

    # MLX event codes (from X11)
    KEY_PRESS = 2
    KEY_RELEASE = 3
    BUTTON_PRESS = 4
    BUTTON_RELEASE = 5
    MOTION_NOTIFY = 6
    EXPOSE = 12
    DESTROY_NOTIFY = 33

    # Key codes mapping (X11 keycodes)
    KEYS = {
        'a': 38, 'b': 56, 'c': 54, 'd': 40, 'e': 26, 'f': 41, 'g': 42, 'h': 43,
        'i': 31, 'j': 44, 'k': 45, 'l': 46, 'm': 58, 'n': 57, 'o': 32,
        'p': 33, 'q': 24, 'r': 27, 's': 39, 't': 28, 'u': 30, 'v': 55,
        'w': 25, 'x': 53, 'y': 29, 'z': 52,
        '0': 19, '1': 10, '2': 11, '3': 12, '4': 13, '5': 14,
        '6': 15, '7': 16, '8': 17, '9': 18,
        'space': 65, 'escape': 9, 'enter': 36, 'tab': 23,
        'backspace': 22, 'delete': 119, 'insert': 118,
        'up': 111, 'down': 116, 'left': 113, 'right': 114,
        'home': 110, 'end': 115, 'page_up': 112, 'page_down': 117,
        'shift': 50, 'ctrl': 37, 'alt': 64, 'meta': 133,
        'f1': 122, 'f2': 120, 'f3': 99, 'f4': 118,
        'f5': 96, 'f6': 97, 'f7': 98, 'f8': 100,
        'f9': 101, 'f10': 109, 'f11': 110, 'f12': 102,
    }

    # Reverse mapping for debug
    KEY_NAMES = {v: k for k, v in KEYS.items()}

    def __init__(self):
        """Initialize the input subsystem."""
        self._logger = Log.get("input")
        self._initialized = False
        self._mlx_callbacks = {}

        # Key states
        self.key_states: Dict[int, KeyState] = {}
        self.active_keys: Set[int] = set()

        # Mouse states
        self.mouse_position: Tuple[int, int] = (0, 0)
        self.mouse_buttons: Dict[MouseButton, KeyState] = {
            MouseButton.LEFT: KeyState.IDLE,
            MouseButton.MIDDLE: KeyState.IDLE,
            MouseButton.RIGHT: KeyState.IDLE,
        }
        self.mouse_wheel: float = 0

        # Modifier keys
        self.modifiers: Set[str] = set()
        self.modifier_map = {
            50: 'shift',   # Left Shift
            62: 'shift',   # Right Shift
            37: 'ctrl',    # Left Ctrl
            105: 'ctrl',   # Right Ctrl
            64: 'alt',     # Left Alt
            108: 'alt',    # Right Alt
            133: 'meta',   # Left Meta
            134: 'meta',   # Right Meta
        }

        # Input mappings (action name -> list of keys)
        self.action_mappings: Dict[str, List[int]] = {}

        # Callbacks
        self.key_callbacks: Dict[int, List[Callable]] = {}
        self.mouse_callbacks: Dict[MouseButton, List[Callable]] = {}
        self.action_callbacks: Dict[str, List[Callable]] = {}
        self.any_key_callbacks: List[Callable] = []
        self.any_mouse_callbacks: List[Callable] = []
        self.close_callbacks: List[Callable] = []

        # Input recording
        self.input_buffer: List[InputEvent] = []
        self.buffer_size: int = 100
        self.recording: bool = False

        # State
        self._frame_count = 0

        # Debug flag
        self._debug_print_keys = False

    def init(self, renderer):
        """Initialize the input subsystem with the renderer's MLX instance."""
        if self._initialized:
            return

        # Get MLX from renderer
        self._renderer = renderer
        self.mlx = renderer.mlx
        self.mlx_ptr = renderer.mlx_ptr
        self.win_ptr = renderer.win_ptr

        print(f"[DEBUG] Input.init() - Got MLX from renderer: {self.mlx}")
        print(f"[DEBUG] Input.init() - win_ptr: {self.win_ptr}")

        # Set up input handlers
        self._setup_input()
        self._register_mlx_hooks()

        self._initialized = True
        self._logger.info("Input subsystem initialized")
        print("[DEBUG] Input initialized successfully")

    def _register_mlx_hooks(self):
        """Register MLX event hooks."""

        print("[DEBUG] Registering MLX hooks...")

        # Keep references alive (important for ctypes callbacks)
        self._mlx_callbacks = {}

        # KEY PRESS
        def on_key_press(keycode, param):
            print(f"[MLX] Key PRESS: {keycode}")
            self._handle_key_press(keycode, param)

        self._mlx_callbacks["key_press"] = on_key_press

        self.mlx.mlx_hook(
            self.win_ptr,
            self.KEY_PRESS,
            0,
            on_key_press,
            self
        )


        # KEY RELEASE
        def on_key_release(keycode, param):
            print(f"[MLX] Key RELEASE: {keycode}")
            self._handle_key_release(keycode, param)

        self._mlx_callbacks["key_release"] = on_key_release

        self.mlx.mlx_key_hook(
            self.win_ptr,
            on_key_release,
            self
        )


        # MOUSE PRESS
        def on_mouse_press(button, x, y, param):
            print(
                f"[MLX] Mouse PRESS: "
                f"button={button} x={x} y={y}"
            )

            self._handle_mouse_press(
                button,
                x,
                y,
                param
            )

        self._mlx_callbacks["mouse_press"] = on_mouse_press

        self.mlx.mlx_mouse_hook(
            self.win_ptr,
            on_mouse_press,
            self
        )


        # MOUSE RELEASE
        def on_mouse_release(button, x, y, param):
            print(
                f"[MLX] Mouse RELEASE: "
                f"button={button} x={x} y={y}"
            )

            self._handle_mouse_release(
                button,
                x,
                y,
                param
            )

        self._mlx_callbacks["mouse_release"] = on_mouse_release

        self.mlx.mlx_hook(
            self.win_ptr,
            self.BUTTON_RELEASE,
            0,
            on_mouse_release,
            self
        )


        # MOUSE MOTION
        def on_mouse_motion(x, y, param):
            self._handle_motion(
                x,
                y,
                param
            )

        self._mlx_callbacks["mouse_motion"] = on_mouse_motion

        self.mlx.mlx_hook(
            self.win_ptr,
            self.MOTION_NOTIFY,
            0,
            on_mouse_motion,
            self
        )


        # WINDOW CLOSE (X button)
        def on_destroy(param):
            print("[MLX] Window destroyed")

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


        print("[DEBUG] All MLX hooks registered")

    def _setup_input(self):
        """Setup default input bindings and callbacks."""

        self.bind_action(
            "quit",
            [self.KEYS["escape"]]
        )

        self.bind_action(
            "confirm",
            [self.KEYS["enter"], self.KEYS["space"]]
        )

        self.bind_action(
            "cancel",
            [self.KEYS["escape"]]
        )

        self.bind_action(
            "up",
            [self.KEYS["up"], self.KEYS["w"]]
        )

        self.bind_action(
            "down",
            [self.KEYS["down"], self.KEYS["s"]]
        )

        self.bind_action(
            "left",
            [self.KEYS["left"], self.KEYS["a"]]
        )

        self.bind_action(
            "right",
            [self.KEYS["right"], self.KEYS["d"]]
        )

        from .. import Renderer

        self.register_action_callback(
            "quit",
            Renderer.close_request
        )

        self.on_close(
            Renderer.close_request
        )

        self._logger.debug(
            "Default input bindings set up"
        )

    def _handle_key_press(self, keycode: int, param):
        """Handle key press event from MLX."""
        print(f"[INPUT] Key PRESS: {keycode}")
        self._set_key_state(keycode, True)

        if self._debug_print_keys:
            key_name = self.get_key_name(keycode)
            print(f"[KEY PRESS] {key_name} (code: {keycode})")

    def _handle_key_release(self, keycode: int, param):
        """Handle key release event from MLX."""
        print(f"[INPUT] Key RELEASE: {keycode}")
        self._set_key_state(keycode, False)

        if self._debug_print_keys:
            key_name = self.get_key_name(keycode)
            print(f"[KEY RELEASE] {key_name} (code: {keycode})")

    def _set_key_state(self, keycode: int, pressed: bool):
        """Set the state of a key."""
        if pressed:
            if keycode not in self.key_states or self.key_states[keycode] == KeyState.IDLE:
                self.key_states[keycode] = KeyState.PRESSED
                self.active_keys.add(keycode)

                # Check for modifiers
                if keycode in self.modifier_map:
                    self.modifiers.add(self.modifier_map[keycode])

                # Record input
                if self.recording:
                    self.input_buffer.append(InputEvent(
                        key=keycode,
                        modifiers=list(self.modifiers)
                    ))
                    if len(self.input_buffer) > self.buffer_size:
                        self.input_buffer.pop(0)

                # Trigger callbacks
                if keycode in self.key_callbacks:
                    for callback in self.key_callbacks[keycode]:
                        callback(KeyState.PRESSED, keycode)

                for callback in self.any_key_callbacks:
                    callback(keycode, KeyState.PRESSED)
        else:
            if keycode in self.key_states:
                self.key_states[keycode] = KeyState.RELEASED
                self.active_keys.discard(keycode)

                if keycode in self.modifier_map:
                    self.modifiers.discard(self.modifier_map[keycode])

                if keycode in self.key_callbacks:
                    for callback in self.key_callbacks[keycode]:
                        callback(KeyState.RELEASED, keycode)

                for callback in self.any_key_callbacks:
                    callback(keycode, KeyState.RELEASED)

    def _handle_mouse_press(self, button: int, x: int, y: int, param):
        """Handle mouse button press event from MLX."""
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

        # Trigger callbacks
        if mouse_button in self.mouse_callbacks:
            for callback in self.mouse_callbacks[mouse_button]:
                callback(KeyState.PRESSED, x, y)

        for callback in self.any_mouse_callbacks:
            callback(mouse_button, KeyState.PRESSED, x, y)

    def _handle_mouse_release(self, button: int, x: int, y: int, param):
        """Handle mouse button release event from MLX."""
        self.mouse_position = (x, y)

        try:
            mouse_button = MouseButton(button)
        except ValueError:
            return

        self.mouse_buttons[mouse_button] = KeyState.RELEASED

        # Trigger callbacks
        if mouse_button in self.mouse_callbacks:
            for callback in self.mouse_callbacks[mouse_button]:
                callback(KeyState.RELEASED, x, y)

        for callback in self.any_mouse_callbacks:
            callback(mouse_button, KeyState.RELEASED, x, y)

    def _handle_motion(self, x: int, y: int, param):
        """Handle mouse motion event from MLX."""
        self.mouse_position = (x, y)

    def update(self):
        """Call this once per frame to update input states."""
        self._frame_count += 1

        # Reset pressed/released states
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

        # Reset mouse wheel
        self.mouse_wheel = 0

    # ===== Query Methods =====

    def is_key_pressed(self, key: int) -> bool:
        """Check if key was just pressed this frame."""
        return self.key_states.get(key) == KeyState.PRESSED

    def is_key_held(self, key: int) -> bool:
        """Check if key is currently held down."""
        return self.key_states.get(key) in (KeyState.PRESSED, KeyState.HELD)

    def is_key_released(self, key: int) -> bool:
        """Check if key was just released this frame."""
        return self.key_states.get(key) == KeyState.RELEASED

    def is_key_down(self, key: int) -> bool:
        """Check if key is down (held or just pressed)."""
        return key in self.active_keys

    def is_any_key_pressed(self, keys: List[int]) -> bool:
        """Check if any key in the list was just pressed."""
        return any(self.is_key_pressed(key) for key in keys)

    def is_any_key_held(self, keys: List[int]) -> bool:
        """Check if any key in the list is being held."""
        return any(self.is_key_held(key) for key in keys)

    def is_modifier_active(self, modifier: str) -> bool:
        """Check if a modifier key is active."""
        return modifier in self.modifiers

    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return self.mouse_position

    def is_mouse_button_pressed(self, button: MouseButton) -> bool:
        """Check if mouse button was just pressed."""
        return self.mouse_buttons.get(button) == KeyState.PRESSED

    def is_mouse_button_held(self, button: MouseButton) -> bool:
        """Check if mouse button is being held."""
        return self.mouse_buttons.get(button) in (KeyState.PRESSED, KeyState.HELD)

    def is_mouse_button_released(self, button: MouseButton) -> bool:
        """Check if mouse button was just released."""
        return self.mouse_buttons.get(button) == KeyState.RELEASED

    def get_mouse_wheel(self) -> float:
        """Get mouse wheel scroll (positive = up, negative = down)."""
        return self.mouse_wheel

    # ===== Action System =====

    def bind_action(self, action_name: str, keys: List[int]):
        """Bind one or more keys to an action."""
        self.action_mappings[action_name] = keys
        self._logger.debug(f"Bound action '{action_name}' to keys: {keys}")

    def bind_action_combo(self, action_name: str, combo: List[int]):
        """Bind a key combination to an action (all keys must be held)."""
        self.action_mappings[action_name] = combo
        self._logger.debug(f"Bound combo action '{action_name}' to keys: {combo}")

    def is_action_triggered(self, action_name: str) -> bool:
        """Check if an action was just triggered."""
        if action_name not in self.action_mappings:
            return False

        keys = self.action_mappings[action_name]

        # Check if all keys in the combo are held
        if len(keys) > 1:
            if all(self.is_key_held(key) for key in keys):
                return any(self.is_key_pressed(key) for key in keys)
            return False

        # Single key
        return self.is_key_pressed(keys[0])

    def is_action_held(self, action_name: str) -> bool:
        """Check if an action is currently being held."""
        if action_name not in self.action_mappings:
            return False

        keys = self.action_mappings[action_name]
        return all(self.is_key_held(key) for key in keys)

    def is_action_released(self, action_name: str) -> bool:
        """Check if an action was just released."""
        if action_name not in self.action_mappings:
            return False

        keys = self.action_mappings[action_name]
        return any(self.is_key_released(key) for key in keys)

    def register_action_callback(self, action_name: str, callback: Callable):
        """Register a callback for when an action is triggered."""
        if action_name not in self.action_callbacks:
            self.action_callbacks[action_name] = []
        self.action_callbacks[action_name].append(callback)
        self._logger.debug(f"Registered callback for action '{action_name}'")

    def process_actions(self):
        """Process all action triggers and callbacks."""
        for action_name in self.action_callbacks:
            if self.is_action_triggered(action_name):
                for callback in self.action_callbacks[action_name]:
                    callback()

    # ===== Callback System =====

    def on_key_press(self, key: int, callback: Callable):
        """Register callback for key press."""
        if key not in self.key_callbacks:
            self.key_callbacks[key] = []
        self.key_callbacks[key].append(callback)

    def on_key_release(self, key: int, callback: Callable):
        """Register callback for key release."""
        if key not in self.key_callbacks:
            self.key_callbacks[key] = []
        self.key_callbacks[key].append(callback)

    def on_any_key(self, callback: Callable):
        """Register callback for any key press/release."""
        self.any_key_callbacks.append(callback)
        print(f"[DEBUG] Registered any-key callback: {callback}")

    def on_mouse_click(self, button: MouseButton, callback: Callable):
        """Register callback for mouse click."""
        if button not in self.mouse_callbacks:
            self.mouse_callbacks[button] = []
        self.mouse_callbacks[button].append(callback)

    def on_any_mouse(self, callback: Callable):
        """Register callback for any mouse event."""
        self.any_mouse_callbacks.append(callback)

    def on_close(self, callback: Callable):
        """Register callback for window close."""
        self.close_callbacks.append(callback)

    # ===== Input Recording =====

    def start_recording(self):
        """Start recording input events."""
        self.recording = True
        self.input_buffer.clear()
        self._logger.info("Started input recording")

    def stop_recording(self) -> List[InputEvent]:
        """Stop recording and return recorded events."""
        self.recording = False
        self._logger.info(f"Stopped input recording: {len(self.input_buffer)} events")
        return self.input_buffer.copy()

    def play_recorded_input(self, events: List[InputEvent], callback: Callable):
        """Play back recorded input events."""
        for event in events:
            callback(event)

    # ===== Utility Methods =====

    def clear_states(self):
        """Reset all input states."""
        self.key_states.clear()
        self.active_keys.clear()
        self.modifiers.clear()
        for button in self.mouse_buttons:
            self.mouse_buttons[button] = KeyState.IDLE
        self.mouse_wheel = 0
        self._logger.debug("Cleared all input states")

    def get_key_name(self, keycode: int) -> str:
        """Get the name of a key from its keycode."""
        return self.KEY_NAMES.get(keycode, f"unknown_{keycode}")

    def get_active_keys(self) -> List[str]:
        """Get list of currently active key names."""
        return [self.get_key_name(key) for key in self.active_keys]

    def get_debug_info(self) -> str:
        """Get debug information about current input state."""
        active_keys = self.get_active_keys()
        active_mods = list(self.modifiers)
        mouse_pos = self.mouse_position

        return (f"Active Keys: {active_keys}\n"
                f"Modifiers: {active_mods}\n"
                f"Mouse: {mouse_pos}\n"
                f"Mouse Buttons: {self.mouse_buttons}")

    # ===== DEBUG FUNCTIONS =====

    def enable_key_debug(self, enabled: bool = True):
        """Enable or disable printing all key presses/releases."""
        self._debug_print_keys = enabled
        status = "enabled" if enabled else "disabled"
        print(f"[DEBUG] Key printing {status}")
        if enabled:
            print("[DEBUG] Press any key to see its code and name")

    def print_active_keys(self):
        """Print all currently active (held) keys."""
        if self.active_keys:
            key_list = []
            for keycode in sorted(self.active_keys):
                key_name = self.get_key_name(keycode)
                key_list.append(f"{key_name}({keycode})")
            print(f"[ACTIVE KEYS] {', '.join(key_list)}")
        else:
            print("[ACTIVE KEYS] None")

    def debug_key_logger(self):
        """Register a callback that prints every key press/release."""
        def log_key(keycode, state):
            key_name = self.get_key_name(keycode)
            print(f"[KEY EVENT] {key_name} (code: {keycode}) - {state.name}")

        self.on_any_key(log_key)
        print("[DEBUG] Key logger registered - all key events will be printed")


# Global input system (must be initialized after Renderer)
Input = InputSubsystem()
