"""Day54 前置 A2c：亲手创建 Task 并等待它。

动作 read_notice 由 AI 提供，检查入口也已搭好；两题已实现。
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day54.day54_task_checks import check_cases


async def read_notice(place: str) -> dict[str, str]:
    """AI 提供的动作：等 0.15 秒，返回 {"place": 地点, "notice": "按时闭馆"}。"""
    await asyncio.sleep(0.15)
    return {"place": place, "notice": "按时闭馆"}


def start_task(place: str) -> asyncio.Task:
    """把 read_notice(place) 包成 Task 并立即返回，不等待它完成。"""
    return asyncio.create_task(read_notice(place))


async def run_two() -> list[dict[str, str]]:
    """同时启动“二楼”“三楼”两个任务，按启动顺序返回两份结果。"""
    answer = []
    task1 = start_task("二楼")
    task2 = start_task("三楼")
    answer1 = await task1
    answer2 = await task2
    answer.append(answer1)
    answer.append(answer2)
    return answer


def run_exercise(run_dir: Path) -> None:
    """把本模块的两道题交给检查入口，保存实际结果；无需修改。"""
    asyncio.run(check_cases(sys.modules[__name__], run_dir))


def main() -> None:
    """保存本轮控制台、配置、源码摘要和检查 JSON。"""
    run_logged(
        "task_exercise",
        run_exercise,
        {"model_calls": 0, "http_requests": 0, "case_count": 2},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day54/outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
