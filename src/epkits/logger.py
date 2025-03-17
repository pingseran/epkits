__all__ = ["logger"]

import queue
import threading
import multiprocessing
import time
import os
import sys
import uuid
import platform

from .core import debug
from .zero import get_frame
from .level import level_t
from .record import record_t
from .logger_server import logger_server


class logger_t:
    def __init__(self):
        if debug:
            self.level = level_t.D
        else:
            self.level = level_t.I

        self.seq = 0
        self.seq_lock = threading.Lock()

        self.nid = uuid.getnode()
        self.nname = platform.node()

    def get_seq(self) -> int:
        with self.seq_lock:
            self.seq += 1

        return self.seq

    def output(self, record: record_t) -> None:
        if debug and record.level == level_t.T:
            logger_server.handle(record, quick=True)

        logger_server.handle(record)

    def rawlog(
        self,
        ts: float,
        seq: int,
        level: int,
        nid: int,
        nname: str,
        pid: int,
        pname: str,
        tid: int,
        tname: str,
        file: str,
        lineno: int,
        func: str,
        message: str,
    ) -> None:
        if level < self.level:
            return

        record = record_t(
            ts=ts,
            seq=seq,
            level=level,
            nid=nid,
            nname=nname,
            pid=pid,
            pname=pname,
            tid=tid,
            tname=tname,
            file=file,
            lineno=lineno,
            func=func,
            message=message,
        )
        self.output(record)

    def debug(self, message: str = "") -> None:
        if self.level > level_t.D:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.D,
            nid=self.nid,
            nname=self.nname,
            pid=os.getpid(),
            pname=multiprocessing.current_process().name,
            tid=threading.get_ident(),
            tname=threading.current_thread().name,
            file="",
            lineno=0,
            func="",
            message=message,
        )

        if frame:
            record.file = frame.f_code.co_filename
            record.lineno = frame.f_lineno
            record.func = frame.f_code.co_qualname

        self.rawlog(**record.__dict__)

    def info(self, message: str = "") -> None:
        if self.level > level_t.I:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.I,
            nid=self.nid,
            nname=self.nname,
            pid=os.getpid(),
            pname=multiprocessing.current_process().name,
            tid=threading.get_ident(),
            tname=threading.current_thread().name,
            file="",
            lineno=0,
            func="",
            message=message,
        )

        if frame:
            record.file = frame.f_code.co_filename
            record.lineno = frame.f_lineno
            record.func = frame.f_code.co_qualname

        self.rawlog(**record.__dict__)

    def warning(self, message: str = "") -> None:
        if self.level > level_t.W:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.W,
            nid=self.nid,
            nname=self.nname,
            pid=os.getpid(),
            pname=multiprocessing.current_process().name,
            tid=threading.get_ident(),
            tname=threading.current_thread().name,
            file="",
            lineno=0,
            func="",
            message=message,
        )

        if frame:
            record.file = frame.f_code.co_filename
            record.lineno = frame.f_lineno
            record.func = frame.f_code.co_qualname

        self.rawlog(**record.__dict__)

    def error(self, message: str = "") -> None:
        if self.level > level_t.E:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.E,
            nid=self.nid,
            nname=self.nname,
            pid=os.getpid(),
            pname=multiprocessing.current_process().name,
            tid=threading.get_ident(),
            tname=threading.current_thread().name,
            file="",
            lineno=0,
            func="",
            message=message,
        )

        if frame:
            record.file = frame.f_code.co_filename
            record.lineno = frame.f_lineno
            record.func = frame.f_code.co_qualname

        self.rawlog(**record.__dict__)

    def test(self, message: str = "") -> None:
        if self.level > level_t.T:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.T,
            nid=self.nid,
            nname=self.nname,
            pid=os.getpid(),
            pname=multiprocessing.current_process().name,
            tid=threading.get_ident(),
            tname=threading.current_thread().name,
            file="",
            lineno=0,
            func="",
            message=message,
        )

        if frame:
            record.file = frame.f_code.co_filename
            record.lineno = frame.f_lineno
            record.func = frame.f_code.co_qualname

        self.rawlog(**record.__dict__)


logger = logger_t()
