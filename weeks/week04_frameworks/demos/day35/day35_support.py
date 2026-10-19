"""Day 35 做题接口：完整状态 → 可直接使用的节点 → 运行入口。

做 A、B 看 QuoteState；做 C 看下面六个节点/路由接口的说明。
统一写 support.函数名，参数与返回值就在本文件，不用追读旧文件。
直接运行本文件只打印手册；SQL、命令行和检查输出由 day35_runtime.py 管理。
"""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from langchain_core.messages import AnyMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from weeks.week04_frameworks.demos.day35 import day35_runtime as _runtime
from weeks.week04_frameworks.exercises import day34_graph_exercises as _day34


class QuoteState(TypedDict):
    """图中完整的状态字段；原来的九项与今天新增四项都列在这里。

    这是字典的字段说明，不是自动填好的数据。首次输入由运行入口准备，
    后续由图应用节点返回的更新；节点和路由收到的 state 都是当前状态字典。
    """

    # Day 34 已有的字段：名称、类型与消息合并规则均保持原样。
    messages: Annotated[list[AnyMessage], add_messages]  # 只返回新消息，图负责合并。
    trace: list[dict]  # request/tool/final/stop 事件；普通列表需自行保留旧项。
    usages: list[dict | None]  # 每次收到响应的用量；没有响应不新增。
    steps: int  # 已尝试的模型请求次数。
    answer: str | None  # 模型生成的报价草稿；有草稿不代表已经发布。
    stop_reason: str | None  # 无停止原因为 None；模型完成为 final_answer。
    scenario: str  # 离线模型的教学情境，本课首次输入用 normal。
    limits: dict  # Day 34 的预算、次数和超时等限制。
    started_at: float  # 首次任务计时起点；本课审核恢复后不再请求模型。

    # Day 35 新增的字段。
    quote_id: str  # 一次报价发布的业务编号，如 offer-001；用于数据库防重。
    approved: bool  # 人是否批准发布；首次为 False，A 题负责更新。
    action_count: int  # 此业务编号实际保存的记录数，首次为 0，发布后为 1。
    outbox_db: str  # 本地模拟发件箱的数据库路径，由运行入口准备。


def model_node(state: QuoteState) -> dict:
    """C 可直接用：复用 Day 34 的一次模型请求，不是新模型实现。

    输入：图传入完整 state；读取消息、计时、限制、情境和旧计数等字段。
    返回：messages、trace、usages、steps、answer、stop_reason 六项更新。
    模型完成时 answer 是草稿、stop_reason='final_answer'；工具点单时原因是 None。
    请求前到期和请求中超时的行为沿用你已完成的 Day 34。
    """
    return _day34.model_node(state)


def tools_node(state: QuoteState) -> dict:
    """C 可直接用：执行最新模型回复中的整批点单，沿用 Day 34。

    输入：完整 state；使用最新 assistant 消息、旧 trace、steps 和权限限制。
    返回：{'messages': 本批工具观察列表, 'trace': 旧轨迹加本批工具事件}。
    不增加模型请求次数；它只执行模型点单，不负责报价发布。
    """
    return _day34.tools_node(state)


def check_limits(state: QuoteState) -> dict:
    """C 可直接用：工具全部回填后，检查能否继续请求模型。

    输入：完整 state，使用 trace、usages、steps 和 limits。
    返回：{'stop_reason': 原因或 None, 'trace': 保留旧项后的轨迹}。
    顺序沿用 Day 34：无进展重复 → 预算 → 最大请求次数；停止时新增一条 stop。
    """
    return _day34.check_limits(state)


def route_after_limits(state: QuoteState) -> Literal["model", "end"]:
    """C 可直接用：读取停止检查后的 state，返回下一站的标签。

    stop_reason 为 None 返回 'model'，否则返回 'end'。
    只读取已有状态，不发模型请求、不执行工具，也不返回状态更新字典。
    """
    return _day34.route_after_limits(state)


def route_after_review(state: QuoteState) -> Literal["publish", "end"]:
    """C 可直接用：读取 A 更新后的 approved，批准返回 'publish'，拒绝返回 'end'。

    输入是完整 state；返回一个路线标签，不新增消息、轨迹或请求计数。
    """
    return "publish" if state["approved"] else "end"


def publish_quote(state: QuoteState) -> dict:
    """C 可直接用：给定本地动作工具，把已批准的草稿记入模拟发件箱。

    输入：完整 state；使用 approved、answer、quote_id、outbox_db 四项。
    返回：{'action_count': 1}。相同编号与草稿重试不会新增第二条记录；
    同编号却换了草稿会报错，新业务应换编号。未批准或没有草稿也会报错。
    不更新 messages、trace、usages 或 steps；只写本地 SQLite，不发送消息。
    SQL 机制已在独立演示讲过，做题时直接把此函数作为节点使用。
    """
    return _runtime.publish_quote(state)


def run_cli(build_graph: Callable[[SqliteSaver], CompiledStateGraph]) -> None:
    """main 已用好：接收你的建图函数，准备保存器并按命令行运行。

    传函数本身，如 run_cli(build_quote_graph)；这里负责把 saver 传给它。
    start 首次输入；status 只读状态；resume 交回 allow/deny；compare 对照旧实现。
    本函数没有返回值，结果直接打印；数据库路径与所有命令保持原样。
    """
    _runtime.run_cli(build_graph)


# 旧接口兼容区：保留此前教具可访问的名字；新练习直接用上面的 support.函数名。
core = _day34
handwritten = _runtime.handwritten
DAY_DIR = _runtime.DAY_DIR
DEFAULT_DB = _runtime.DEFAULT_DB
DEFAULT_OUTBOX = _runtime.DEFAULT_OUTBOX
QUESTION = _runtime.QUESTION
outbox_count = _runtime.outbox_count
print_snapshot = _runtime.print_snapshot
compare_core = _runtime.compare_core
data_path = _runtime.data_path


def main() -> None:
    """直接运行时打印做题手册，不执行节点或学员图，也不创建数据库。"""
    print("=== Day 35 做题只查这里 ===")
    print("A：看 QuoteState 的 answer / quote_id / approved，写你自己的 review_quote。")
    print("B：看 QuoteState 的 stop_reason，写你自己的 route_after_model。")
    print("C：使用下面六个现成接口，接入你自己写的两个函数并建图。")
    print("\nQuoteState 已列出全部十三项字段，没有藏在父类型中的字段。")
    for function in (
        model_node,
        tools_node,
        check_limits,
        route_after_limits,
        route_after_review,
        publish_quote,
    ):
        # __name__ 是函数名，__doc__ 是它的 docstring；这里只把接口说明打印出来。
        print(f"\n--- support.{function.__name__}(state) ---")
        print(function.__doc__)
    print("\n=== 运行参数怎么对应 ===")
    print("--ticket-id d35-allow：把 d35-allow 放到 config 的 thread_id，用来找会话。")
    print("--quote-id offer-001：给本次业务发布取编号，用来防止重复保存。")
    print("start / status / resume / compare 的完整命令见本周 README。")
    print("后台 SQL、参数解析与输出放在 day35_runtime.py，由 AI 维护。")


if __name__ == "__main__":
    main()
