# demo/main.py

import sys
import os

import logging

# 将 src 目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import threading
import time

import epkits as ep

ep.debug = 1


def worker(n: int):
    eplog = ep.logger_t()
    for i in range(n):
        eplog.info(f"测试日志, i = {i}")
        time.sleep(0.001)


if __name__ == "__main__":
    eplog = ep.logger_t()

    n = 1000
    m = 100
    start = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(n,), daemon=True) for _ in range(m)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    end = time.perf_counter()
    elapse_ms = (end - start) * 1000
    print(
        f"总耗时: {elapse_ms:.03f}ms, 平均耗时: {elapse_ms / (n*m):.06f}ms, qps: {(n*m) / elapse_ms * 1000:.0f}"
    )
