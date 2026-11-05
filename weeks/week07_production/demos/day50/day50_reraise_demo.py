"""Day50：独立比较 raise 与 raise error 的异常回溯，为日志后继续抛错准备。"""

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def fail_at_source() -> None:
    """在固定位置制造教学异常；不读取真实文件。"""
    raise FileNotFoundError("AI_demo_missing")


def keep_original_trace() -> None:
    """捕获后用裸 raise，沿用当前异常回溯。"""
    try:
        fail_at_source()
    except FileNotFoundError:
        print("  已捕获异常，先打印这条记录，再用 raise 继续抛。")
        raise


def add_raise_site() -> None:
    """故意用具名重抛，对比额外出现的当前行。"""
    try:
        fail_at_source()
    except FileNotFoundError as error:
        print("  已捕获异常，先打印这条记录，再用 raise error 继续抛。")
        raise error  # noqa: TRY201 - 故意与裸 raise 对照，不是推荐写法。


def show_trace(error: FileNotFoundError) -> None:
    """逐行显示异常经过的函数和源码，不把回溯当成事件字段。"""
    print("异常类型：", type(error).__name__)
    # extract_tb(异常的 __traceback__)：返回按调用顺序排列的回溯帧摘要。
    # 每项有函数名 name、行号 lineno 和对应源码 line。
    for frame in traceback.extract_tb(error.__traceback__):
        print(f"  {frame.name} 第 {frame.lineno} 行：{frame.line}")


def demonstrate_reraise(run_dir: Path) -> None:
    """在相同出错源下分别打印两种重抛方式的完整短调用路径。"""
    print("\n一、是什么：异常回溯是报错时附带的‘经过哪些函数、哪些行’的记录。")
    print("Week07 要根据失败日志定位问题；A 记完错误后，调用方仍应收到异常及出错位置。")
    print("为什么：只知道 FileNotFoundError 还不够，排错还要知道它从哪里发生。")
    print("场景：一个具体动作报错，外层记录后继续抛给调用方；这里用人工异常独立演示。")
    print("\n二、代码：两条路径都调用 fail_at_source()，那里才是最初出错的位置。")
    print("except 内单独写 raise：继续抛当前异常；需要当前有正在处理的异常。")
    print("except 内写 raise error：显式在当前行再抛这个异常，会把该行加入回溯。")

    print("\n第一条路径：keep_original_trace 中使用 raise")
    try:
        keep_original_trace()
    except FileNotFoundError as error:
        show_trace(error)

    print("\n第二条路径：add_raise_site 中使用 raise error")
    try:
        add_raise_site()
    except FileNotFoundError as error:
        show_trace(error)

    print("\n三、注意：第二条路径会多出 add_raise_site 的 raise error 那一行。")
    print("两种写法抛的都是捕获到的异常，不会因为写 error 就变成一个新异常。")
    print("这里额外的是回溯位置，不是说业务动作又执行了一次。")
    print("仅记录后继续抛出时，A 用裸 raise；新建异常、替换异常是其他用途。")
    print("本演示显示回溯供你理解；A 的 events.jsonl 仍只记 error_type，不写回溯原文。")
    print("演示输出目录：", run_dir)


def main() -> None:
    """沿用运行留证，提供独立可重复的语法对照。"""
    print("Day50 前置答疑：看清日志之后继续抛错时，raise 与 raise error 差在哪里。")
    print("源码先看三个短函数 fail_at_source、keep_original_trace、add_raise_site。")
    # run_logged 为已有运行环境：将本次目录传给 demonstrate_reraise，保存控制台。
    run_logged(
        "reraise_demo",
        demonstrate_reraise,
        {"mode": "offline_teaching"},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY50_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
