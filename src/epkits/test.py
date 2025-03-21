__all__ = ["testsuit_base_t", "skip", "run_all_tests"]

import time
import os
import multiprocessing
import threading
import random
import inspect
import pathlib
import json
from functools import wraps

from abc import ABC, abstractmethod
from typing import final, Any, Self, Callable, override, get_type_hints
import types

from .core import exception_t
from .level import level_t
from .record import record_t
from .logger import logger
from .zero import get_frame

test_summary = {
    "all": {
        "duration": 0,
        "start_time": 0,
        "end_time": 0,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skiped": 0,
    },
    "order": {
        "total": 0,
    },
    "testcases": {},
}


class test_exception_t(exception_t):
    pass


class check_err(test_exception_t):
    pass


def skip(condition: bool = True) -> Callable[[Any], Any]:
    def decorator(target: Any) -> Any:
        if condition:
            setattr(target, "_skip", True)
        return target

    return decorator


class testsuit_base_t(ABC):
    _testsuit_classes: list[type[Self]] = []

    def env_up(self) -> int:
        return 0

    def env_down(self) -> int:
        return 0

    @final
    def __init_subclass__(cls, **kwargs) -> None:
        if not issubclass(cls, testsuit_base_t):
            logger.test(f"testsuit_t 必须是 testsuit_base_t 的子类，{cls.__name__} 不是")
            raise TypeError("testsuit_t 必须是 testsuit_base_t 的子类")

        if not (cls.__name__.startswith("test_") and cls.__name__.endswith("_t")):
            logger.test(f"testsuit_t 类名必须是 test_xxxx_t 格式，{cls.__name__} 不是")
            raise TypeError("testsuit_t 类名必须是 test_xxxx_t 格式")
        super().__init_subclass__(**kwargs)

        testsuit_base_t._testsuit_classes.append(cls)

        cls._testmethods = []
        # 只要子类的test_开头的方法，不包括孙子类的test_开头的方法
        for attr_name, attr in cls.__dict__.items():
            if attr_name.startswith("test_") and inspect.isfunction(attr):
                cls._testmethods.append(attr)

    @final
    def __init__(self) -> None:
        self.name = "<None>@<None>.<None>"
        self.testmethod: Callable[[], None]

    @final
    def __str__(self) -> str:
        return f"{self.name}"

    @final
    def __repr__(self) -> str:
        return f"testcase({self.name})"

    @final
    def skip(self) -> None:
        setattr(self, "_skip", True)

    @final
    def check_eq(self, exp_ret: Any) -> "check_base_t":
        check = check_eq_t(self, exp_ret)
        return check


class check_base_t(ABC):
    @override
    @abstractmethod
    def __init__(self, testcase: testsuit_base_t) -> None:
        self._testcase = testcase

        self.exp_ret: Any = None

        self.ret: Any = None
        self.err: int = 0

    @abstractmethod
    def __enter__(self) -> Self:
        return self

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: types.TracebackType | None,
    ) -> bool | None:
        return True


class check_eq_t(check_base_t):
    @override
    def __init__(self, testcase: testsuit_base_t, exp_ret: Any) -> None:
        super().__init__(testcase)
        self.exp_ret = exp_ret

    @override
    def __enter__(self) -> Self:
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: types.TracebackType | None,
    ) -> bool | None:
        frame = get_frame(1)

        record = record_t(
            ts=time.time(),
            seq=logger.get_seq(level_t.T),
            level=level_t.T,
            nid=logger.get_nid(),
            nname=logger.get_nname(),
            pid=os.getpid(),
            pname=multiprocessing.current_process().name,
            tid=threading.get_ident(),
            tname=threading.current_thread().name,
            file="",
            lineno=0,
            func="",
            message="",
        )

        if frame:
            record.file = pathlib.PurePath(frame.f_code.co_filename).as_posix()
            record.lineno = frame.f_lineno
            record.func = frame.f_code.co_qualname

        if exc_type is not None:
            if exc_traceback:
                tb_lineno = exc_traceback.tb_lineno
            else:
                tb_lineno = 0
            self.err = 1
            record.message = f'核对失败: 发生异常({os.path.basename(record.file)}:{tb_lineno}) = {exc_type.__name__}("{exc_value}")'
        elif self.ret != self.exp_ret:
            self.err = 1
            record.message = f"核对失败: 期待返回 = {self.exp_ret}, 实际返回 = {self.ret}"
        else:
            self.err = 0
            record.message = f"核对通过: 期待返回 = {self.exp_ret}, 实际返回 = {self.ret}"

        logger.rawlog(**record.__dict__)

        if self.err:
            raise check_err()
        return True


testcases: list[testsuit_base_t] = []


def run_all_tests() -> int:
    logger.test(
        """
********************************************************************************
*
*   测试开始
*
********************************************************************************"""
    )

    testsuit_base_t._testsuit_classes.sort(key=lambda testsuit_class: testsuit_class.__name__)

    for testsuit_class in testsuit_base_t._testsuit_classes:
        testsuit_class._testmethods.sort(key=lambda testmethod: testmethod.__name__)

        for testmethod in testsuit_class._testmethods:
            testcase = testsuit_class()
            testcase.testmethod = types.MethodType(testmethod, testcase)
            testcase.name = (
                pathlib.PurePath(inspect.getfile(testmethod)).as_posix()
                + "@"
                + testmethod.__qualname__
            )

            testcases.append(testcase)

    random.shuffle(testcases)
    test_summary["order"]["total"] = len(testcases)
    test_summary["all"]["total"] = len(testcases)

    test_summary["start_time"] = round(time.time(), 3)
    for order, testcase in enumerate(testcases, start=1):
        test_summary["order"][order] = str(testcase)

        test_summary["testcases"][str(testcase)] = {
            "duration": 0,
            "start_time": 0,
            "end_time": 0,
            "status": "",
        }
        testcase_detail = test_summary["testcases"][str(testcase)]
        testcase_detail["start_time"] = round(time.time(), 3)

        if getattr(testcase.__class__, "_skip", False) or getattr(
            testcase.testmethod, "_skip", False
        ):
            testcase_detail["status"] = "skiped"
            test_summary["all"]["skiped"] += 1
            logger.rawlog(
                **record_t(
                    ts=time.time(),
                    seq=logger.get_seq(level_t.T),
                    level=level_t.T,
                    nid=logger.get_nid(),
                    nname=logger.get_nname(),
                    pid=os.getpid(),
                    pname=multiprocessing.current_process().name,
                    tid=threading.get_ident(),
                    tname=threading.current_thread().name,
                    file=pathlib.PurePath(inspect.getfile(testcase.testmethod)).as_posix(),
                    lineno=inspect.getsourcelines(testcase.testmethod)[1],
                    func=testcase.testmethod.__qualname__,
                    message=f"测试用例 跳过: {order:6d} {testcase}",
                ).__dict__
            )
        else:
            logger.rawlog(
                **record_t(
                    ts=time.time(),
                    seq=logger.get_seq(level_t.T),
                    level=level_t.T,
                    nid=logger.get_nid(),
                    nname=logger.get_nname(),
                    pid=os.getpid(),
                    pname=multiprocessing.current_process().name,
                    tid=threading.get_ident(),
                    tname=threading.current_thread().name,
                    file=pathlib.PurePath(inspect.getfile(testcase.testmethod)).as_posix(),
                    lineno=inspect.getsourcelines(testcase.testmethod)[1],
                    func=testcase.testmethod.__qualname__,
                    message=f"测试用例 开始",
                ).__dict__
            )

            try:
                env_up_ret = testcase.env_up()
                if env_up_ret:
                    logger.rawlog(
                        **record_t(
                            ts=time.time(),
                            seq=logger.get_seq(level_t.T),
                            level=level_t.T,
                            nid=logger.get_nid(),
                            nname=logger.get_nname(),
                            pid=os.getpid(),
                            pname=multiprocessing.current_process().name,
                            tid=threading.get_ident(),
                            tname=threading.current_thread().name,
                            file=pathlib.PurePath(inspect.getfile(testcase.testmethod)).as_posix(),
                            lineno=inspect.getsourcelines(testcase.testmethod)[1],
                            func=testcase.testmethod.__qualname__,
                            message=f"环境初始化失败 env_up() = {env_up_ret}",
                        ).__dict__
                    )
                    raise test_exception_t()

                time.sleep(random.random())
                testcase.testmethod()

                env_down_ret = testcase.env_down()
                if env_down_ret:
                    logger.rawlog(
                        **record_t(
                            ts=time.time(),
                            seq=logger.get_seq(level_t.T),
                            level=level_t.T,
                            nid=logger.get_nid(),
                            nname=logger.get_nname(),
                            pid=os.getpid(),
                            pname=multiprocessing.current_process().name,
                            tid=threading.get_ident(),
                            tname=threading.current_thread().name,
                            file=pathlib.PurePath(inspect.getfile(testcase.testmethod)).as_posix(),
                            lineno=inspect.getsourcelines(testcase.testmethod)[1],
                            func=testcase.testmethod.__qualname__,
                            message=f"环境销毁失败 env_down() = {env_down_ret}",
                        ).__dict__
                    )
                    raise test_exception_t()

                testcase_detail["status"] = "passed"
                test_summary["all"]["passed"] += 1
                logger.rawlog(
                    **record_t(
                        ts=time.time(),
                        seq=logger.get_seq(level_t.T),
                        level=level_t.T,
                        nid=logger.get_nid(),
                        nname=logger.get_nname(),
                        pid=os.getpid(),
                        pname=multiprocessing.current_process().name,
                        tid=threading.get_ident(),
                        tname=threading.current_thread().name,
                        file=pathlib.PurePath(inspect.getfile(testcase.testmethod)).as_posix(),
                        lineno=inspect.getsourcelines(testcase.testmethod)[1],
                        func=testcase.testmethod.__qualname__,
                        message=f"测试用例 通过: {order:6d} {testcase}",
                    ).__dict__
                )
            except Exception as e:
                testcase_detail["status"] = "failed"
                test_summary["all"]["failed"] += 1
                logger.rawlog(
                    **record_t(
                        ts=time.time(),
                        seq=logger.get_seq(level_t.T),
                        level=level_t.T,
                        nid=logger.get_nid(),
                        nname=logger.get_nname(),
                        pid=os.getpid(),
                        pname=multiprocessing.current_process().name,
                        tid=threading.get_ident(),
                        tname=threading.current_thread().name,
                        file=pathlib.PurePath(inspect.getfile(testcase.testmethod)).as_posix(),
                        lineno=inspect.getsourcelines(testcase.testmethod)[1],
                        func=testcase.testmethod.__qualname__,
                        message=f"测试用例 失败: {order:6d} {testcase}",
                    ).__dict__
                )
            finally:
                pass

        testcase_detail["end_time"] = round(time.time(), 3)
        testcase_detail["duration"] = round(
            testcase_detail["end_time"] - testcase_detail["start_time"], 3
        )

    test_summary["end_time"] = round(time.time(), 3)
    test_summary["duration"] = round(test_summary["end_time"] - test_summary["start_time"], 3)

    logger.test("\n" + json.dumps(test_summary, ensure_ascii=False, indent=4))

    logger.test(
        f"""
所有测试用例 耗时: {test_summary["duration"]:.03f}
    总计: {test_summary["all"]["total"]:6d}
    跳过: {test_summary["all"]["skiped"]:6d}
    失败: {test_summary["all"]["failed"]:6d}
    通过: {test_summary["all"]["passed"]:6d}
"""
    )

    if test_summary["all"]["failed"]:
        return 1
    return 0
