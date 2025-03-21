__all__ = ["logger_server"]

import atexit
import os
import sys
import time
import threading
import queue

from .record import record_t
from .mlogger import mlogger


class logger_server_t:
    def __init__(self) -> None:
        self.rotate_last_time = 0

        self.dir = "./log"
        self.prefix = "ep"
        self.log_size = 1024 * 1024 * 10
        self.log_count = 10

        self.log_file = None
        self.log_quick_file = None

        self.log_queue = queue.Queue(maxsize=1000 * 1000)
        self.log_quick_queue = queue.Queue(maxsize=1000 * 1000)

        self.log_thread_stop = 0
        self.log_thread = threading.Thread(target=self.worker, name="eplog", daemon=True)
        self.log_thread.start()

        atexit.register(self.exit)

    def handle(self, record: record_t, *, quick: bool = False) -> None:
        if quick:
            try:
                self.log_quick_queue.put_nowait(record)
            except queue.Full:
                pass
            except AttributeError:
                pass
        else:
            try:
                self.log_queue.put_nowait(record)
            except queue.Full:
                pass
            except AttributeError:
                pass

    def open(self) -> None:
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        try:
            self.log_quick_file = open(
                os.path.join(self.dir, f"{self.prefix}.quick.log"), "ab", buffering=0
            )
            self.log_quick_file.write("\n\n\n\n\n\n\n\n\n\n".encode())
        except OSError:
            self.log_quick_file = None

        try:
            self.log_file = open(os.path.join(self.dir, f"{self.prefix}.0.log"), "ab", buffering=0)
            self.log_file.write("\n\n\n\n\n\n\n\n\n\n".encode())
        except OSError:
            self.log_file = None

    def close(self) -> None:
        if self.log_quick_file is not None:
            log_quick_file = self.log_quick_file
            self.log_quick_file = None
            log_quick_file.flush()
            os.fsync(log_quick_file.fileno())
            log_quick_file.close()

        if self.log_file is not None:
            log_file = self.log_file
            self.log_file = None
            log_file.flush()
            os.fsync(log_file.fileno())
            log_file.close()

    def exit(self) -> None:
        self.log_thread_stop = time.monotonic() + 1
        self.log_thread.join()

    def rotate(self) -> None:
        if os.path.getsize(os.path.join(self.dir, f"{self.prefix}.0.log")) >= self.log_size:
            self.close()

            for i in range(self.log_count - 2, -1, -1):
                log_file = os.path.join(self.dir, f"{self.prefix}.{i}.log")
                log_file_new = os.path.join(self.dir, f"{self.prefix}.{i + 1}.log")
                if os.path.exists(log_file_new):
                    os.remove(log_file_new)
                if os.path.exists(log_file):
                    os.rename(log_file, log_file_new)

            self.open()

    def worker(self) -> None:
        self.open()

        while True:
            now = time.monotonic()

            if now > self.log_thread_stop > 0:
                break

            if now - self.rotate_last_time >= 60:
                self.rotate_last_time = now
                self.rotate()

            while not self.log_quick_queue.empty():
                if self.log_quick_file is not None:
                    record = self.log_quick_queue.get_nowait()
                    self.log_quick_file.write(str(record).encode())

            while not self.log_queue.empty():
                if self.log_file is not None:
                    record = self.log_queue.get_nowait()
                    self.log_file.write(str(record).encode())
            else:
                if self.log_file is not None:
                    try:
                        record = self.log_queue.get(block=True, timeout=1)
                        self.log_file.write(str(record).encode())
                    except queue.Empty:
                        pass

        self.close()


logger_server = logger_server_t()
