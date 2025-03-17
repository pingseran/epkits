# demo/main.py

import sys
import os


# 将 src 目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import threading
import time


import epkits as ep

ep.debug = 1

sys.path.append(".")


def worker(n: int):
    for i in range(n):
        ep.logger.info(
            f"测试日志, i = {i:06d}"
            " "
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
            "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
        )
        time.sleep(0.001)


if __name__ == "__main__":

    n = 1000
    m = 16
    start = time.perf_counter()
    threads = [
        threading.Thread(target=worker, args=(n,), name=f"worker-{i:03d}", daemon=True)
        for i in range(m)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    end = time.perf_counter()
    elapse_ms = (end - start) * 1000
    print(
        f"总耗时: {elapse_ms:.03f}ms, 平均耗时: {elapse_ms / (n*m):.06f}ms, qps: {(n*m) / elapse_ms * 1000:.0f}"
    )
