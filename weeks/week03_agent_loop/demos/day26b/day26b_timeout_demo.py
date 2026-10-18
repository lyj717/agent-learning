"""Day 26B 前半演示：一次调用的超时与整个 Agent 任务的时限。"""

import subprocess
import sys
import time
from pathlib import Path

WORKER = (Path(__file__).resolve().parent / "day26b_timeout_worker.py").resolve()


def main() -> None:
    """按是什么、为什么、场景、代码、注意的顺序演示两层时限。"""
    print("=== 1. 这是什么 ===")
    print("单次调用超时：某一次工具等太久，就结束这次等待。")
    print("任务总时限：整个 Agent 从开始到现在还能花多少时间。")

    print("\n=== 2. 为什么需要 ===")
    print("只有总时限检查时，若工具正在阻塞，循环暂时没有机会检查时间。")
    print("只有单次调用超时，很多次较短的调用加起来仍可能拖很久。")

    print("\n=== 3. 具体场景 ===")
    print("Agent 要检索资料：任务最多 5 秒，一次检索最多等 1 秒。")
    print("以下时间数字是固定教学情境；随后再运行一个真实的本地慢工具。")

    print("\n=== 4. 看代码对应的结果 ===")
    for label, now in [("时间充足", 13.0), ("只剩半秒", 14.5), ("总时限已到", 15.0)]:
        plan = plan_next_call(10.0, now, 5.0, 1.0)
        print(
            f"{label}：已用 {plan['elapsed']} 秒，剩余 {plan['remaining']} 秒，"
            f"下次最多等 {plan['next_timeout']} 秒，停止原因 {plan['stop_reason']}"
        )
    print("下次最多等 = 单次上限与任务剩余时间中较小的一个。")

    print("\n本地工具第一次很快完成；第二次故意等得比单次上限更久：")
    for delay, timeout in [(0.02, 0.5), (0.3, 0.05)]:
        # monotonic() 只看两次读数的差，适合测持续时间；绝对读数没有日历意义。
        started_at = time.monotonic()
        result = run_slow_tool(delay, timeout)
        elapsed = time.monotonic() - started_at
        print(
            f"工具设定等待 {delay} 秒；单次上限 {timeout} 秒；"
            f"实际经过约 {elapsed:.3f} 秒；结果 {result['status']}；"
            f"观察 {result['observation']}"
        )

    print("\n=== 5. 注意什么 ===")
    print("总时限在调用前检查，只能决定要不要开始下一次调用。")
    print("调用已经开始后，要由该调用自身的超时机制结束等待；超时与任务到期分开记录。")
    print("启动子进程和系统调度也耗时，实际经过时间不保证正好等于设定的秒数。")
    print("这里运行的是仓库里固定的慢工具，不是执行任意模型生成的代码。")


def remaining_seconds(started_at: float, now: float, task_limit: float) -> float:
    """返回任务尚余的秒数；到期或超期都返回 0。"""
    elapsed = now - started_at
    return max(0.0, task_limit - elapsed)


def plan_next_call(
    started_at: float, now: float, task_limit: float, call_limit: float
) -> dict:
    """在下一次调用前，记时间账并决定本次最多能等待多久。"""
    elapsed = now - started_at
    remaining = remaining_seconds(started_at, now, task_limit)
    if remaining == 0:
        return {
            "elapsed": elapsed,
            "remaining": remaining,
            "next_timeout": None,
            "stop_reason": "task_timeout",
        }
    return {
        "elapsed": elapsed,
        "remaining": remaining,
        "next_timeout": min(call_limit, remaining),
        "stop_reason": None,
    }


def run_slow_tool(delay_seconds: float, timeout_seconds: float) -> dict:
    """调用固定的本地慢工具，区分正常观察与单次调用超时。"""
    try:
        # sys.executable 是当前 Python 解释器；-B 避免子程序生成 __pycache__。
        # subprocess.run(参数列表, timeout=秒数) 等待本地程序，超时会抛出 TimeoutExpired。
        finished = subprocess.run(
            [sys.executable, "-B", str(WORKER), str(delay_seconds)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
            check=True,
        )
    except subprocess.TimeoutExpired:
        return {"status": "call_timeout", "observation": None}
    return {"status": "completed", "observation": finished.stdout.strip()}


if __name__ == "__main__":
    main()
