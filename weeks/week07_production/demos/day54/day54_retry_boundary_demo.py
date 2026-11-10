"""Day54 D1：单独认识重试的次数、异常边界和退避等待。

从 demonstrate_async 读起。本例只有本机人工等待，不访问模型或 HTTP。
它展示两种常见错误做法和正确的判定顺序，不实现练习要交的 call_with_retry。
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

ATTEMPTS = 3
BASE_DELAY = 0.05


class RateLimitedError(Exception):
    """下游限流：可重试。"""


class BadRequestError(Exception):
    """请求参数错误：不可重试。"""


async def retry_everything(action: object, job_id: str) -> dict[str, str]:
    """错误示范 A：不分异常类型，一律重试。"""
    for attempt in range(ATTEMPTS):
        try:
            return await action(job_id)  # type: ignore[misc]
        except Exception:
            if attempt == ATTEMPTS - 1:
                raise
            await asyncio.sleep(BASE_DELAY)
    raise AssertionError("不会走到这里")


async def retry_without_wait(action: object, job_id: str) -> dict[str, str]:
    """错误示范 B：可重试错误立刻重试，不等待。"""
    for attempt in range(ATTEMPTS):
        try:
            return await action(job_id)  # type: ignore[misc]
        except (TimeoutError, RateLimitedError):
            if attempt == ATTEMPTS - 1:
                raise
    raise AssertionError("不会走到这里")


async def demonstrate_async(run_dir: Path) -> None:
    """打印判定表、退避时间表，并实测两种错误做法的调用时刻。"""
    print("Week07 的 Day54 最后一段：把旧重试接进异步服务，并守住次数和异常边界。")
    print("本节只回答：哪些错能重试、试几次、每次等多久；不实现练习函数。")

    print("\n一、哪些错误值得重试")
    print(
        "  可重试：TimeoutError（等待超时）、ConnectionError（连接失败）、RateLimitedError（被限流）"
    )
    print("  不可重试：BadRequestError（参数错）、ValueError 等——重试一百次结果也一样")
    print("  判断顺序：先看是不是可重试；不是就立刻抛；是再看还有没有次数。")

    print(f"\n二、等待时间表（attempts={ATTEMPTS}，base_delay={BASE_DELAY}）")
    moment = 0.0
    schedule = [0.0]
    for attempt in range(1, ATTEMPTS):
        moment += BASE_DELAY * 2 ** (attempt - 1)
        schedule.append(round(moment, 3))
    print(f"  第 1/2/3 次尝试的时刻：{schedule}（秒）")
    print("  即第一次失败后等 0.05 秒，第二次失败后等 0.10 秒，而不是每次都等 0.05。")

    print("\n三、错误示范 A：一律重试")
    calls: list[float] = []
    loop = asyncio.get_running_loop()
    begin = loop.time()

    async def reject(job_id: str) -> dict[str, str]:
        """每次都抛不可重试错误。"""
        calls.append(round(loop.time() - begin, 3))
        raise BadRequestError("参数错误")

    try:
        await retry_everything(reject, "馆藏")
    except BadRequestError:
        print(f"  结果：BadRequestError 被调用了 {len(calls)} 次，时刻={calls}")
        print("  参数错误重试没有意义，还多打了两次下游。")

    print("\n四、错误示范 B：可重试，但不等待")
    slow_calls: list[float] = []
    begin = loop.time()

    async def timeout_once(job_id: str) -> dict[str, str]:
        """每次都抛可重试的超时错误。"""
        slow_calls.append(round(loop.time() - begin, 3))
        raise TimeoutError("超时")

    try:
        await retry_without_wait(timeout_once, "馆藏")
    except TimeoutError:
        print(f"  结果：三次调用时刻={slow_calls}")
        print("  三次几乎同时发出；下游正在过载时，这样做只会把压力叠上去。")

    print("\n五、正确形状（练习里由你写）")
    print("  for 循环取 1..attempts：先 await action；")
    print("  except 里先分可重试/不可重试；不可重试立刻 raise；")
    print("  可重试但已是最后一次也 raise（抛出最后一次的那个异常对象）；")
    print("  其余情况 await asyncio.sleep(base_delay * 2 ** (n - 1)) 后继续。")

    print(
        "\n注意：重试是“同一份逻辑工作再开始一次”，接上窗口限额后，每次尝试都会再占一个开始名额；"
    )
    print(
        "所以一份失败两次再成功的工作，在窗口里记的是 3 次开始。本题不接限额，只记住这个账。"
    )

    assert len(calls) == 3
    (run_dir / "retry_boundary.json").write_text(
        json.dumps(
            {
                "schedule": schedule,
                "retry_everything_calls": len(calls),
                "no_wait_call_times": slow_calls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def demonstrate(run_dir: Path) -> None:
    """从普通脚本启动一次异步主过程。"""
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本轮判定、时刻与来源。"""
    run_logged(
        "retry_boundary_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0, "attempts": ATTEMPTS},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
