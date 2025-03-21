# demo/test.py

import sys
import os


# 将 src 目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import epkits as ep

ep.enable_debug()


def twosum(a: int, b: int) -> int:
    raise ValueError("故意抛出异常")
    return a + b


class test_twosum_t(ep.testsuit_base_t):
    def env_up(self) -> int:
        return 1

    def env_down(self) -> int:
        return 1

    def test_twosum_positive(self) -> None:
        with self.check_eq(4) as check:
            check.ret = twosum(1, 2)

    def test_twosum_negative(self) -> None:
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
    exit_code = ep.run_all_tests(sys.argv)
    exit(exit_code)
