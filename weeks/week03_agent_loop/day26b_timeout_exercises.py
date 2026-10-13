"""Day 26B 前半小练习：先算剩余时间，再处理固定慢工具的单次超时。"""

import subprocess
import sys
from pathlib import Path

WORKER = Path(__file__).resolve().with_name("day26b_timeout_worker.py")


def remaining_seconds(started_at: float, now: float, task_limit: float) -> float:
    """计算任务剩余秒数，到期后返回 0。"""
    elapsed = now - started_at
    return max(task_limit - elapsed, 0.0)


def plan_next_call(
    started_at: float, now: float, task_limit: float, call_limit: float
) -> dict:
    """按任务剩余时间决定下一次调用的上限与停止原因。"""
    elapsed = now - started_at
    remaining = remaining_seconds(started_at, now, task_limit)
    if remaining == 0.0:
        next_timeout = None
        stop_reason = "task_timeout"
    else:
        next_timeout = min(call_limit, remaining)
        stop_reason = None
    return {
        "elapsed": elapsed,
        "remaining": remaining,
        "next_timeout": next_timeout,
        "stop_reason": stop_reason,
    }


def run_slow_tool(delay_seconds: float, timeout_seconds: float) -> dict:
    """调用固定慢工具，返回正常观察或单次超时状态。"""
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


def main() -> None:
    """逐题打印实际结果与期望结果；做到哪题就先核对哪题。"""
    print("=== A1：任务剩余秒数 ===")
    for now, expected in [(14.5, 0.5), (15.0, 0.0), (16.0, 0.0)]:
        actual = remaining_seconds(10.0, now, 5.0)
        print(f"检查时间 {now}：实际 {actual}；期望 {expected}")

    print("\n=== A2：下一次调用前的决定 ===")
    for label, now, expected_timeout, expected_reason in [
        ("时间充足", 13.0, 1.0, None),
        ("只剩半秒", 14.5, 0.5, None),
        ("总时限已到", 15.0, None, "task_timeout"),
    ]:
        actual = plan_next_call(10.0, now, 5.0, 1.0)
        print(
            f"{label}：已用 {actual['elapsed']}；剩余 {actual['remaining']}；"
            f"下次上限 {actual['next_timeout']}（期望 {expected_timeout}）；"
            f"停止原因 {actual['stop_reason']}（期望 {expected_reason}）"
        )

    print("\n=== B：单次慢工具 ===")
    for delay, timeout, expected in [
        (0.02, 0.5, "completed"),
        (0.3, 0.05, "call_timeout"),
    ]:
        actual = run_slow_tool(delay, timeout)
        print(
            f"工具等待 {delay}、调用上限 {timeout}：状态 {actual['status']}"
            f"（期望 {expected}）；观察 {actual['observation']}"
        )


if __name__ == "__main__":
    main()


# 现象与原因（学员运行并填写）
# 1. A2 的“只剩半秒”为什么不能给下一次工具完整的 1 秒？
# 答：只剩余0.5的余额了，超过0.5就到上限了，只能给0.5s
# 2. A2 的“总时限已到”和 B 的“单次慢工具超时”分别在哪个位置发现？
# 答：A2： if remaining == 0.0:
#         next_timeout = None
#         stop_reason = "task_timeout"
#   B: except subprocess.TimeoutExpired:
#         return {"status": "call_timeout", "observation": None}
# 3. 只在循环开始处检查任务总时限，为什么不能让已经阻塞的调用立刻结束？
# 答：循环开始处的检查只决定能否开始；程序阻塞时，只能靠调用自己的超时机制结束等待
# 4. 第二次慢工具的实际运行时间是否一定恰好为 0.05 秒？你观察到什么？
# 答：不一定恰好为0.05秒，实际经过时间不保证正好等于设定的秒数,实际0.062秒
