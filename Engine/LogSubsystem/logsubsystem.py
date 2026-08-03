from .logger import Logger, LogMode
import time
import functools


class LogSubsystem:
    """Global logging system."""

    def __init__(self):
        self._logger = Logger()

    def get(self, name: str):
        return self._logger.get(name)

    def verbose(self) -> None:
        self._logger.set_mode(LogMode.DEBUG)

    def normal(self) -> None:
        self._logger.set_mode(LogMode.RELEASE)

    def errors(self) -> None:
        self._logger.set_mode(LogMode.QUIET)

    def enable_console(self) -> None:
        self._logger.enable_console()

    def disable_console(self) -> None:
        self._logger.disable_console()

    def enable_file(self, file: str = "logs/latest.log") -> None:
        self._logger.enable_file(file)

    def disable_file(self) -> None:
        self._logger.disable_file()

    def close(self) -> None:
        self._logger.close()


def log_timing(label=None, logger_attr="_logger", every: int = 300):
    """Decorator for subsystem update()/render() methods."""

    def decorator(func):
        name = label or func.__name__
        counter_name = f"_log_timing_{func.__name__}_counter"
        total_name = f"_log_timing_{func.__name__}_total"

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
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
                        logger.debug(f"{name} average took {average_ms:.3f}"
                                     f" ms ({counter} calls)")
                    setattr(self, counter_name, 0)
                    setattr(self, total_name, 0.0)

        return wrapper

    return decorator


Log = LogSubsystem()
