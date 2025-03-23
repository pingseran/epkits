# demo/test.py

import sys
import os


# 将 src 目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import epkits as ep

ep.enable_debug()


@ep.reg_process_events_handle
def process_events() -> None:
    pass


def twosum(a: int, b: int) -> int:
    # raise ValueError("故意抛出异常")
    return a + b


class test_twosum_t(ep.testsuit_base_t):
    def test_twosum_positive(self) -> None:
        with self.check_eq(4) as check:
            check.ret = twosum(1, 2)

    def test_twosum_negative(self) -> None:
        with self.check_exc(ValueError) as check:
            check.ret = twosum(-1, -1)

        with self.check_eq(-2) as check:
            check.ret = twosum(-1, -1)


class test_2_t(ep.testsuit_base_t):
    def test_2(self) -> None:
        pass

    def test_1(self) -> None:
        pass


class test_1_t(ep.testsuit_base_t):
    def test_2(self) -> None:
        pass

    def test_1(self) -> None:
        pass


if __name__ == "__main__":
    exit_code = ep.run_all_tests()
    exit(exit_code)
