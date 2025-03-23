__all__ = ["filelock_t"]

import os
import time
import sys
import io
import types
from typing import Self

if os.name == "nt":
    import msvcrt
else:
    import fcntl


class filelock_t:
    """跨平台的文件锁，支持 with 语句"""

    def __init__(
        self, file_path: str, timeout: float | None = None, check_interval: float = 0.1
    ) -> None:
        """
        :param file_path: 锁文件路径
        :param timeout: 获取锁的超时时间（秒），None 表示无限等待
        :param check_interval: 轮询检查间隔
        """

        self.file_path: str = file_path
        self.timeout = timeout
        self.check_interval: float = check_interval
        self.file: io.TextIOWrapper | None = None

    def acquire(self, blocking: bool = True) -> bool:
        """尝试获取文件锁，支持阻塞模式"""
        start_time = time.monotonic()
        self.file = open(self.file_path, "w")
        while True:
            try:
                if os.name == "nt":
                    msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)  # Windows 非阻塞锁
                else:
                    fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)  # Linux/macOS 非阻塞锁
                return True  # 获取锁成功
            except (BlockingIOError, OSError):  # 文件被锁定
                if not blocking:
                    self.file.close()
                    self.file = None
                    return False
                if self.timeout is not None and time.monotonic() - start_time > self.timeout:
                    self.file.close()
                    self.file = None
                    raise TimeoutError("获取文件锁超时")
                time.sleep(self.check_interval)  # 等待后重试

    def release(self) -> None:
        """释放文件锁"""
        if self.file:
            try:
                if os.name == "nt":
                    msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)  # Windows 释放锁
                else:
                    fcntl.flock(self.file, fcntl.LOCK_UN)  # Linux/macOS 释放锁
            finally:
                self.file.close()
                self.file = None
                os.remove(self.file_path)  # 删除锁文件

    def __enter__(self) -> Self:
        """支持 with 语句"""
        self.acquire(blocking=True)  # 默认阻塞等待锁
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: types.TracebackType | None,
    ) -> None:
        """退出 with 语句时释放锁"""
        self.release()
