# epkits/__init__.py

__author__ = "平清然"
__email__ = "pingseran@gmail.com"
__version__ = "0.1.0"

from .core import *
from .zero import *

from .level import *
from .record import *
from .mlogger import *
from .logger import *
from .logger_server import *
from .test import *
from .filelock import *

import os
import sys
import atexit


def _deinit() -> None:
    os.remove("./log/ep.pid")


def init() -> None:
    if sys.version_info < (3, 12):
        raise RuntimeError("epkits 需要 Python 3.12 或更高版本")
    atexit.register(_deinit)

    with open("./log/ep.pid", "w") as f:
        f.write(str(os.getpid()))

    logger_server.init()


if __name__ == "__main__":
    pass
