__all__ = ["level_t"]

from enum import IntEnum


class level_t(IntEnum):
    N = 0  # None
    D = 1  # Debug
    I = 2  # Info
    W = 3  # Warning
    E = 4  # Error
    T = 5  # Test

    F = 10  # Off
