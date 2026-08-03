from __future__ import annotations

import queue
import threading
import datetime
import traceback
from enum import Enum
from pathlib import Path
from dataclasses import dataclass


class LogType(Enum):
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4
    FATAL = 5


class LogMode(Enum):
    DEBUG = 0
    RELEASE = 1
    QUIET = 2


class Color:
    RESET = "\033[0m"
    GREY = "\033[90m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


COLORS = {
    LogType.DEBUG: Color.GREY,
    LogType.INFO: "",
    LogType.SUCCESS: Color.GREEN,
    LogType.WARNING: Color.YELLOW,
    LogType.ERROR: Color.RED,
    LogType.FATAL: Color.MAGENTA,
}


@dataclass
class LogMessage:
    logger: str
    type: LogType
    message: str
    time: datetime.datetime


class NamedLogger:
    """Named logger instance."""

    def __init__(self, parent: "Logger", name: str):
        self.parent = parent
        self.name = name

    def debug(self, message: str) -> None:
        self.parent._push(self.name, LogType.DEBUG, message)

    def info(self, message: str) -> None:
        self.parent._push(self.name, LogType.INFO, message)

    def success(self, message: str) -> None:
        self.parent._push(self.name, LogType.SUCCESS, message)

    def warning(self, message: str) -> None:
        self.parent._push(self.name, LogType.WARNING, message)

    def error(self, message: str) -> None:
        self.parent._push(self.name, LogType.ERROR, message)

    def fatal(self, message: str) -> None:
        self.parent._push(self.name, LogType.FATAL, message)

    def exception(self, message: str) -> None:
        self.parent._push(
            self.name,
            LogType.ERROR,
            message + "\n" + traceback.format_exc()
        )


class Logger:
    """Main logging system."""

    def __init__(
        self,
        mode: LogMode = LogMode.DEBUG,
        file: str | None = "logs/latest.log",
        console: bool = True
    ):
        self.mode = mode
        self.console = console

        self.loggers: dict[str, NamedLogger] = {}
        self.queue: queue.Queue[LogMessage | None] = queue.Queue()

        self.enabled_categories: set[str] = set()
        self.disabled_categories: set[str] = set()

        self.file = None
        self.file_lock = threading.Lock()

        if file:
            path = Path(file)
            path.parent.mkdir(parents=True, exist_ok=True)
            self.file = open(path, "w", encoding="utf-8")

        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def get(self, name: str) -> NamedLogger:
        if name not in self.loggers:
            self.loggers[name] = NamedLogger(self, name)
        return self.loggers[name]

    def set_mode(self, mode: LogMode) -> None:
        self.mode = mode

    def enable_console(self) -> None:
        self.console = True

    def disable_console(self) -> None:
        self.console = False

    def enable_file(self, file: str = "logs/latest.log") -> None:
        path = Path(file)
        path.parent.mkdir(parents=True, exist_ok=True)
        new_file = open(path, "w", encoding="utf-8")

        with self.file_lock:
            old_file = self.file
            self.file = new_file

        if old_file:
            old_file.close()

    def disable_file(self) -> None:
        with self.file_lock:
            old_file = self.file
            self.file = None

        if old_file:
            old_file.close()

    def _push(self, logger: str, type: LogType, message: str) -> None:
        if logger in self.disabled_categories:
            return
        if not self._allowed(type):
            return

        self.queue.put(
            LogMessage(
                logger,
                type,
                message,
                datetime.datetime.now()
            )
        )

    def _allowed(self, type: LogType) -> bool:
        if self.mode == LogMode.DEBUG:
            return True
        if self.mode == LogMode.RELEASE:
            return type.value >= LogType.INFO.value
        if self.mode == LogMode.QUIET:
            return type.value >= LogType.WARNING.value
        return True

    def _worker(self) -> None:
        while self.running:
            item = self.queue.get()

            if item is None:
                break

            text = self._format(item)

            if self.console:
                print(COLORS[item.type] + text + Color.RESET)

            if self.file:
                with self.file_lock:
                    if self.file:
                        self.file.write(text + "\n")
                        self.file.flush()

    def _format(self, msg: LogMessage) -> str:
        time = msg.time.strftime("%H:%M:%S")
        return f"[{time}] [{msg.type.name: ^9}] [{msg.logger}] {msg.message}"

    def close(self) -> None:
        self.running = False
        self.queue.put(None)
        self.thread.join()

        if self.file:
            with self.file_lock:
                self.file.close()
