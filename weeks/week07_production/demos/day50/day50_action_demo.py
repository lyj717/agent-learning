"""Day50 前置答疑：看清 action 是调用方传来的函数，为阶段包装练习准备。

只演示函数赋值、传参和调用；不实现计时、事件或问答整合。
"""

import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def read_notice() -> str:
    """独立教学动作：打印执行标记，返回一条人工通知。"""
    print("    【read_notice 的函数体现在才执行】")
    return "借阅室今天 18 点关闭。"


def run_task(action: Callable[[], str]) -> str:
    """接收一个无参数、返回 str 的函数，调用后原样返回它的结果。"""
    print("    进入 run_task；参数 action 接到的是调用方传来的函数。")
    print("    现在执行：result = action()")
    result = action()
    print("    action() 已执行完，run_task 收到返回值：", result)
    return result


def demonstrate_action(run_dir: Path) -> None:
    """逐步显示把函数交出去与提前执行函数的差别，不读取外部资料。"""
    print("\n先回到 Day45 已经写过的场景：sorted(pairs, key=排序函数)")
    pairs = [("说明页", 0.2), ("操作页", 0.8)]

    def rank_key(pair: tuple[str, float]) -> tuple[float, str]:
        """沿用 Day45 的排序规则，打印被 sorted 调用的时机。"""
        print(f"    【sorted 现在调用 rank_key】收到 {pair}")
        return -pair[1], pair[0]

    print("已给出的片段分数：", pairs)
    print(
        "原来写过 key=lambda pair: (-pair[1], pair[0])；这里给同样规则起名 rank_key。"
    )
    print("执行：ordered = sorted(pairs, key=rank_key)")
    # sorted(数据, key=函数)：内部把每个元素交给 key，按 key 的返回值排序。
    ordered = sorted(pairs, key=rank_key)
    print("sorted 返回排序结果：", ordered)
    print("这时你是 sorted 的使用者：你提供 key 函数，调用它的代码在 sorted 内部。")
    print(
        "今天 A 换了一个角色：你写 trace_call 这个工具，接收并调用别人提供的 action。"
    )
    print("两者都接收函数；key(元素) 需要一个参数，A 的 action() 不需要参数。")

    print("\n一、是什么：action 是普通参数名，这次用来接收一个函数。")
    print(
        "为什么：检索、生成等不同动作都要记录过程；包装器接收动作，才不用写死具体业务。"
    )
    print("场景：先用‘读取人工通知’认识函数传参，再回 A 给任意动作补日志。")
    print("本例通知是 AI 教具；没有读真实文件或调用模型。")

    print("\n二、接口与写法")
    print("Callable 从 collections.abc 导入，描述‘可以被调用的对象’。")
    print("Callable[[], str]：调用时不传参数，返回 str；[] 指无参数，不是返回空列表。")
    print("A 的 Callable[[], Any]：同样无参数，但可以返回任意类型。")
    print("action 不是关键字或库函数，不需要另行 import；调用方决定交给它哪个函数。")

    print("\n三、先把函数交给变量，不加括号：action = read_notice")
    action = read_notice
    # callable(对象)：返回 bool，判断它能否像函数一样被调用；不会执行该对象。
    print("callable(action)：", callable(action))
    print("上面没有出现函数体执行标记，因为这里只是把函数交给了 action。")

    print("\n四、现在加括号，真正执行：result = action()")
    result = action()
    print("执行后的 result：", result)
    print("result 的类型：", type(result).__name__)
    print("此时 action 仍指向函数，result 才是调用它得到的字符串。")

    print("\n五、函数也能当参数传：run_task(read_notice)")
    print("括号外先看到 read_notice 没带 ()；具体执行交给 run_task 内的 action()。")
    returned = run_task(read_notice)
    print("run_task 最后返回：", returned)
    print("调用关系：run_task 接到 read_notice → action() 执行它 → 拿到通知字符串。")

    print("\n六、对照：加了括号再赋值，交出去的就变成执行结果")
    print("执行：already_done = read_notice()")
    already_done = read_notice()
    print("already_done：", already_done)
    print("callable(already_done)：", callable(already_done))
    print("它已经是字符串，不能当作 run_task 需要的函数再调用。")
    print(
        "所以传函数写 run_task(read_notice)；写 run_task(read_notice()) 会先把动作做完。"
    )

    print("\n七、回到 A")
    print(
        "A 的测试工具已经定义好 action 并作为参数传入；你不用再实现一个固定的 action 函数。"
    )
    print(
        "trace_call 里面调用 action()，就是执行这次传入的动作；stage 只负责给阶段起标签。"
    )
    print(
        "本例动作返回 str，A 的动作还可能返回 None/False 或抛异常，不能把结果类型写死。"
    )
    print("动作交给别人、由别人在需要时调用，通常称为‘回调函数’。")
    print("注意：本文件只讲函数传参；日志、计时、成功与失败处理仍由你在 A 中实现。")
    print("\n八、为 B 补一块前置：有参数的函数，怎样交给只接收无参数动作的工具")

    def make_notice(reader: str) -> str:
        """接收读者名字，返回一条人工通知；这是需要参数的具体函数。"""
        print(f"    【make_notice 执行】收到 reader={reader}")
        return f"{reader}，借阅室今天 18 点关闭。"

    def ready_notice() -> str:
        """提前确定 reader，供外部用无参数方式调用。"""
        return make_notice("小林")

    print("具体函数的调用式是 make_notice('小林')，它需要一个参数。")
    print("工具 run_task 内只会调用 action()，不会替动作猜该传什么参数。")
    print("上面的 ready_notice 不接参数，在函数体里调用 make_notice('小林')。")
    print("执行：run_task(ready_notice)，传进去的仍是函数本身，没有提前执行。")
    fixed_result = run_task(ready_notice)
    print("取得结果：", fixed_result)
    print("B 中回调的所需参数写在题面；由业务代码确定参数，再交给 A 执行。")
    print("本例只讲固定一个参数，不给出检索/消息/生成/校验的整合答案。")
    print("本轮演示留证目录：", run_dir)


def main() -> None:
    """先说明阶段用途，再用已有留证环境运行独立回调演示。"""
    print("Week07 要给每次请求的各阶段留日志；A 需要接收并执行‘本阶段要做的动作’。")
    print("本演示讲 action 从哪来、何时执行、返回值去哪，学完再回 trace_call。")
    print(
        "源码先看 demonstrate_action 开头的 sorted 对照，再看 read_notice 与 run_task。"
    )
    run_logged(
        "action_demo",
        demonstrate_action,
        {"mode": "offline_teaching"},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY50_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
