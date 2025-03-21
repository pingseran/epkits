__all__ = ["exception_t", "enable_debug", "set_level", "get_level", "is_debug_enabled"]

import copy

from .level import level_t

conf = {
    "debug": False,
    "level": level_t.I,
}


class exception_t(Exception):
    def __init__(self, message: str = "", *args) -> None:
        super().__init__(message, *args)
        self.message = message

    def __str__(self) -> str:
        return f"{self.message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message})"


def set_level(level: level_t) -> None:
    global conf
    conf["level"] = level


def get_level() -> level_t:
    global conf
    return conf["level"]


def enable_debug() -> None:
    global conf
    conf["debug"] = True
    set_level(level_t.D)


def is_debug_enabled() -> bool:
    global conf
    return conf["debug"]
