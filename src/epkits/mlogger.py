__all__ = ["mlogger"]

import threading
import multiprocessing
import os
import sys
import platform
import time
import uuid

from .core import debug
from .zero import get_frame
from .level import level_t
from .record import record_t


class mlogger_t:
    """迷你日志, 用于库调试自己使用. 请使用正式的logger"""

    def __init__(self) -> None:
        self.seq_lock = threading.Lock()
        self.seq = 0

    def get_seq(self) -> int:
        with self.seq_lock:
            self.seq += 1

        return self.seq

    def debug(self, message: str = "") -> None:
        if debug == 0:
            return

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.D,
            nid=uuid.getnode(),
            nname=platform.node(),
            pid=os.getpid(),
            pname=multiprocessing.current_process().name,
            tid=threading.get_ident(),
            tname=threading.current_thread().name,
            file="",
            lineno=0,
            func="",
            message=message,
        )

        frame = get_frame(1)

        if frame:
            record.file = frame.f_code.co_filename
            record.lineno = frame.f_lineno
            record.func = frame.f_code.co_qualname

        sys.stdout.write(str(record))
        sys.stdout.flush()


mlogger = mlogger_t()
