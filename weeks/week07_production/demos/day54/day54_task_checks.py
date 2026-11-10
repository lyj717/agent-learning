"""Day54 前置 A2c 的运行背景：检查 Task 是否被创建、两个任务是否真的并发。

完整接口在两道题旁；学员不需要读这里才能开工。
不含参考实现，不请求模型、HTTP 或外部服务。
"""

import asyncio
import json
from pathlib import Path
from typing import Any


async def check_start_task(module: Any) -> dict[str, object]:
    """检查 start_task：返回 Task、当时未完成、await 后拿到正确字典。"""
    started = asyncio.get_running_loop().time()
    task = module.start_task("二楼")
    is_task = isinstance(task, asyncio.Task)
    done_now = task.done() if is_task else None
    result: dict[str, str] | None = None
    error: str | None = None
    try:
        result = await asyncio.wait_for(task, timeout=1.0)
    except Exception as exc:  # noqa: BLE001 - 检查器记录全部失败，业务函数照常写。
        error = f"{type(exc).__name__}: {exc}"
    elapsed = asyncio.get_running_loop().time() - started
    expected = {"place": "二楼", "notice": "按时闭馆"}
    passed = all(
        [
            is_task,
            done_now is False,
            result == expected,
            error is None,
            elapsed < 0.5,
        ]
    )
    row = {
        "case": "start_task",
        "passed": passed,
        "is_task": is_task,
        "done_immediately": done_now,
        "result": result,
        "error": error,
        "elapsed": round(elapsed, 4),
    }
    print("\nstart_task：", "通过" if passed else "未通过")
    print(f"  type 是 Task={is_task}；刚返回时 done()={done_now}（期望 False）")
    print(f"  await 后拿到={result}；期望={expected}")
    print(f"  耗时={elapsed:.3f}s；错误={error}")
    return row


async def check_run_two(module: Any) -> dict[str, object]:
    """检查 run_two：结果按启动顺序、两份都完成、耗时接近并发。"""
    started = asyncio.get_running_loop().time()
    results: list[dict[str, str]] | None = None
    error: str | None = None
    try:
        results = await asyncio.wait_for(module.run_two(), timeout=2.0)
    except Exception as exc:  # noqa: BLE001 - 同上。
        error = f"{type(exc).__name__}: {exc}"
    elapsed = asyncio.get_running_loop().time() - started
    expected = [
        {"place": "二楼", "notice": "按时闭馆"},
        {"place": "三楼", "notice": "按时闭馆"},
    ]
    concurrent = elapsed < 0.25
    passed = all([results == expected, error is None, concurrent])
    row = {
        "case": "run_two",
        "passed": passed,
        "results": results,
        "error": error,
        "elapsed": round(elapsed, 4),
    }
    print("\nrun_two：", "通过" if passed else "未通过")
    print(f"  返回={results}；期望={expected}")
    print(f"  耗时={elapsed:.3f}s；并发应 < 0.25s（串行约 0.3s）；错误={error}")
    return row


async def check_cases(module: Any, run_dir: Path) -> None:
    """汇总两题；失败也保存 JSON，然后明确报未通过。"""
    rows = [await check_start_task(module), await check_run_two(module)]
    passed_count = sum(row["passed"] for row in rows)
    (run_dir / "task_checks.json").write_text(
        json.dumps(
            {"passed": passed_count, "total": 2, "cases": rows},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n本次 {passed_count}/2，模型与 HTTP 调用均为 0；实际结果已保存。")
    assert passed_count == 2, "Task 练习还有未通过项，请对照上面的实际与期望"
