"""Day61 检查器：把学员的检查函数分别跑在正常版与故障版上。

正常版（DAY61_VARIANT=good）应不抛异常；故障版（bad）应抛 AssertionError。
只负责执行与留证，不替学员写断言。
"""

import os
from collections.abc import Callable

import pytest

VARIABLE = "DAY61_VARIANT"


def _run_once(check: Callable[[], None], variant: str) -> tuple[str, str]:
    """在指定变体下跑一次，返回（状态, 说明）。"""
    previous = os.environ.get(VARIABLE)
    os.environ[VARIABLE] = variant
    try:
        check()
    except NotImplementedError:
        raise
    except (AssertionError, pytest.fail.Exception) as error:
        return "assert", str(error)
    except Exception as error:  # noqa: BLE001 - 记录检查自身的异常。
        return "error", f"{type(error).__name__}: {error}"
    else:
        return "pass", ""
    finally:
        if previous is None:
            os.environ.pop(VARIABLE, None)
        else:
            os.environ[VARIABLE] = previous


def run_checks(checks: list[tuple[str, Callable[[], None]]]) -> None:
    """逐项跑正常版与故障版，打印结果并在不一致时统一报错。"""
    print("来源：Day61 教具；不调用模型。")
    failures = 0
    for number, (name, check) in enumerate(checks, start=1):
        good_status, good_detail = _run_once(check, "good")
        bad_status, bad_detail = _run_once(check, "bad")
        good_ok = good_status == "pass"
        bad_ok = bad_status == "assert"
        print(f"\n检查 {number}｜{name}")
        print(
            f"  正常版：{good_status}" + (f"（{good_detail}）" if good_detail else "")
        )
        print(f"  故障版：{bad_status}" + (f"（{bad_detail}）" if bad_detail else ""))
        print(f"  正常版无异常={good_ok}；故障版被抓住={bad_ok}")
        failures += int(not good_ok) + int(not bad_ok)
    total = len(checks)
    print(f"\n汇总：{total * 2 - failures}/{total * 2} 项符合预期")
    if failures:
        raise AssertionError("有检查未通过或被故障版绕过，详见上方")
