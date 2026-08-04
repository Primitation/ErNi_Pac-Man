# logsubsystem.py
from .logger import Logger, LogMode
import time
import functools
from typing import Any, Optional, Callable, TypeVar, cast


class LogSubsystem:
    """Global logging system."""

    def __init__(self) -> None:
        """Initialize the log subsystem."""
        self._logger = Logger()

    def get(self, name: str) -> Any:
        """Get a logger.

        Args:
            name: the logger name

        Returns:
            Returns the logger.
        """
        return self._logger.get(name)

    def verbose(self) -> None:
        """Verbose mode."""
        self._logger.set_mode(LogMode.DEBUG)

    def normal(self) -> None:
        """Normal mode."""
        self._logger.set_mode(LogMode.RELEASE)

    def errors(self) -> None:
        """Error mode."""
        self._logger.set_mode(LogMode.QUIET)

    def enable_console(self) -> None:
        """Enable console."""
        self._logger.enable_console()

    def disable_console(self) -> None:
        """Disable console."""
        self._logger.disable_console()

    def enable_file(self, file: str = "logs/latest.log") -> None:
        """Enable file saves.

        Args:
            file: the file to logs.
        """
        self._logger.enable_file(file)

    def disable_file(self) -> None:
        """Disable file saves."""
        self._logger.disable_file()

    def close(self) -> None:
        """Close."""
        self._logger.close()


F = TypeVar('F', bound=Callable[..., Any])


def log_timing(label: Optional[str] = None,
               logger_attr: str = "_logger",
               every: int = 300) -> Callable[[F], F]:
    """Decorator for subsystem update()/render() methods.

    Args:
        label: label name.
        logger_attr: logger attributes.
        every: on every loop.
    """

    def decorator(func: F) -> F:
        """Decorator for a function.

        Args:
            F: the function to decorate.

        Returns:
            Returns the function F decorated.
        """
        name = label or func.__name__
        counter_name = f"_log_timing_{func.__name__}_counter"
        total_name = f"_log_timing_{func.__name__}_total"

        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            """Wrapper

            Args:
                args: args for the function.
                kwargs: kwargs for the function.

            Returns:
                Returns the function wrapped.
            """
            start = time.perf_counter()

            try:
                return func(self, *args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000

                counter = getattr(self, counter_name, 0) + 1
                total = getattr(self, total_name, 0.0) + elapsed_ms

                setattr(self, counter_name, counter)
                setattr(self, total_name, total)

                if counter >= every:
                    logger = getattr(self, logger_attr, None)
                    if logger is not None:
                        average_ms = total / counter
                        logger.debug(f"{name} average took {average_ms:.3f} "
                                     f"ms ({counter} calls)")
                    setattr(self, counter_name, 0)
                    setattr(self, total_name, 0.0)

        return cast(F, wrapper)

    return decorator


Log = LogSubsystem()
