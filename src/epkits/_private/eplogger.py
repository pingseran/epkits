from dataclasses import dataclass
from enum import IntEnum
import types
import time
import math
import os
import sys
import threading
import inspect
import queue
import atexit

import epkits as ep


class level_t(IntEnum):
    N = 0  # None
    D = 1  # Debug
    I = 2  # Info
    W = 3  # Warning
    E = 4  # Error
    T = 5  # Test

    F = 10  # Off


@dataclass
class record_t:
    ts: float = 0
    seq: int = 0
    level: int = level_t.N
    pid: int = -1
    tid: int = -1
    file: str = ""
    lineno: int = -1
    func: str = ""
    message: str = ""

    def __str__(self) -> str:
        st = time.gmtime(self.ts)
        μs = int(math.modf(self.ts)[0] * 1_000_000)

        text = (
            f"[{st.tm_year:04d}{st.tm_mon:02d}{st.tm_mday:02d}.{st.tm_hour:02d}{st.tm_min:02d}{st.tm_sec:02d}.{μs:06d} {self.seq:d}]"
            f"[{self.pid}:{self.tid}]"
            f"[{os.path.basename(self.file)}:{self.lineno} {self.func} {level_t(self.level).name}]"
            " "
            f"{self.message}"
            "\n"
        )

        # text = "[20000101 000000.000 0][0 0][main.py:0 main D]hello world\n"

        return text


def get_frame(back: int = 0) -> types.FrameType | None:
    frame = inspect.currentframe()
    for i in range(back + 1):
        if frame is not None and frame.f_back is not None:
            frame = frame.f_back
        else:
            frame = None
            break

    return frame


class mlogger:
    """迷你日志，用于库调试自己使用，请使用正式的logger"""

    seq_lock = threading.Lock()
    seq = 0

    def __new__(cls, *args, **kwargs):
        raise TypeError("禁止实例化")

    @classmethod
    def get_seq(cls) -> int:
        if cls.seq_lock.acquire(timeout=0.1):
            cls.seq += 1
            cls.seq_lock.release()

        return cls.seq

    @classmethod
    def debug(cls, message=""):
        if ep.debug == 0:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=cls.get_seq(),
            level=level_t.D,
            pid=os.getpid(),
            tid=threading.get_ident(),
            file="",
            lineno=0,
            func="",
            message=message,
        )

        if frame:
            record.file = frame.f_code.co_filename
            record.lineno = frame.f_lineno
            record.func = frame.f_code.co_qualname

        sys.stdout.write(str(record))


class logger_t:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(logger_t, cls).__new__(cls, *args, **kwargs)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.seq = 0
        self.seq_lock = threading.Lock()

        self.rotate_last_time = 0
        self.rotate_last_seq = 0

        self.level = level_t.D if ep.debug else level_t.I
        self.dir = "./log"
        self.prefix = "ep"
        self.log_size = 1024 * 1024 * 10
        self.log_count = 10

        self.logf = None
        self.logft = None

        atexit.register(self.log_exit)

        self.log_open()

        self.log_terminate = 0
        self.logq = queue.Queue(maxsize=1000 * 1000)
        # self.logq = queue.Queue()
        self.log_thread = threading.Thread(target=self.eplog_worker, name="eplog", daemon=True)
        self.log_thread.start()

        # mlogger.debug("")

    # @classmethod
    # def get_instance(cls) -> logger_t:
    #     if not cls._instance:
    #         with cls._lock:
    #             if not cls._instance:
    #                 cls._instance = logger()
    #     return cls._instance

    def get_seq(self) -> int:
        if self.seq_lock.acquire(timeout=0.01):
            self.seq += 1
            self.seq_lock.release()

        return self.seq

    def log_open(self):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        try:
            self.logf = open(os.path.join(self.dir, f"{self.prefix}.0.log"), "ab", buffering=0)
        except OSError:
            self.logf = None

        if ep.debug:
            try:
                self.logft = open(os.path.join(self.dir, f"{self.prefix}.t.log"), "ab", buffering=0)
            except OSError:
                self.logft = None

    def log_close(self):
        if ep.debug and self.logft is not None:
            self.logft.flush()
            os.fsync(self.logft.fileno())
            self.logft.close()
            self.logft = None

        if self.logf is not None:
            self.logf.flush()
            os.fsync(self.logf.fileno())
            self.logf.close()
            self.logf = None

    def log_exit(self):
        # mlogger.debug("log_exit")
        self.log_terminate = time.monotonic() + 1
        self.log_thread.join()

    def rotate(self):
        if os.path.getsize(os.path.join(self.dir, f"{self.prefix}.0.log")) >= self.log_size:
            self.log_close()

            for i in range(self.log_count - 2, -1, -1):
                logf = os.path.join(self.dir, f"{self.prefix}.{i}.log")
                logf_new = os.path.join(self.dir, f"{self.prefix}.{i + 1}.log")
                if os.path.exists(logf_new):
                    os.remove(logf_new)
                if os.path.exists(logf):
                    os.rename(logf, logf_new)

            self.log_open()

    def eplog_worker(self):
        # mlogger.debug("")
        while True:
            now = time.monotonic()

            if now > self.log_terminate > 0:
                self.rawlog_now(
                    ts=time.time(),
                    seq=self.get_seq(),
                    level=level_t.E,
                    pid=os.getpid(),
                    tid=threading.get_ident(),
                    file=__file__,
                    lineno=0,
                    func=self.eplog_worker.__qualname__,
                    message=f"还有{self.logq.qsize()}条日志未写入",
                )
                break

            if self.seq - self.rotate_last_seq >= 1000 or now - self.rotate_last_time >= 60:
                self.rotate_last_time = now
                self.rotate_last_seq = self.seq
                self.rotate()

            if self.logf is not None:
                try:
                    record = self.logq.get(block=True, timeout=1)
                    self.logf.write(str(record).encode("utf-8"))
                except queue.Empty:
                    pass

        self.log_close()

    def rawlog_now(
        self,
        ts: float = 0,
        seq: int = 0,
        level: int = level_t.N,
        pid: int = 0,
        tid: int = 0,
        file: str = "",
        lineno: int = 0,
        func: str = "",
        message: str = "",
    ):
        if level < self.level:
            return

        record = record_t(
            ts=ts,
            seq=seq,
            level=level,
            pid=pid,
            tid=tid,
            file=file,
            lineno=lineno,
            func=func,
            message=message,
        )

        if self.logf is not None:
            self.logf.write(str(record).encode("utf-8"))

    def output(self, record: record_t):
        try:
            self.logq.put_nowait(record)
        except queue.Full:
            # mlogger.debug(f"日志队列已满，丢弃日志: {record}")
            pass
        except AttributeError:
            pass

    def rawlog(
        self,
        ts: float = 0,
        seq: int = 0,
        level: int = level_t.N,
        pid: int = 0,
        tid: int = 0,
        file: str = "",
        lineno: int = 0,
        func: str = "",
        message: str = "",
    ):
        if level < self.level:
            return

        record = record_t(
            ts=ts,
            seq=seq,
            level=level,
            pid=pid,
            tid=tid,
            file=file,
            lineno=lineno,
            func=func,
            message=message,
        )
        self.output(record)

    def debug(self, message: str = ""):
        if self.level > level_t.D:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.D,
            pid=os.getpid(),
            tid=threading.get_ident(),
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

    def info(self, message: str = ""):
        if self.level > level_t.I:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.I,
            pid=os.getpid(),
            tid=threading.get_ident(),
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

    def warning(self, message: str = ""):
        if self.level > level_t.W:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.W,
            pid=os.getpid(),
            tid=threading.get_ident(),
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

    def error(self, message: str = ""):
        if self.level > level_t.E:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.E,
            pid=os.getpid(),
            tid=threading.get_ident(),
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

    def test(self, message: str = ""):
        if self.level > level_t.T:
            return

        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=self.get_seq(),
            level=level_t.T,
            pid=os.getpid(),
            tid=threading.get_ident(),
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

        if ep.debug and self.logft is not None:
            self.logft.write(str(record).encode("utf-8"))


eplog = logger_t()
