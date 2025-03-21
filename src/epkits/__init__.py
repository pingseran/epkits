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

import sys


def main(argv: list[str]) -> int:
    pass


if __name__ == "__main__":
    main(sys.argv)
