"""Day 35 后台运行环境，由 AI 维护。

做练习只需查看 day35_support.py；本文件负责数据库写入、命令行与检查输出。
没有学员待实现的节点或业务图，也不会在导入时打开数据库。
"""

import argparse
import sqlite3
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, StateSnapshot
from openai import OpenAIError

from weeks.week03_agent_loop.demos.day28.day28_live_check import print_trace
from weeks.week03_agent_loop.exercises import day27_integrated_exercises as handwritten
from weeks.week04_frameworks.exercises import day34_graph_exercises as core

DAY_DIR = Path(__file__).resolve().parent
DEFAULT_DB = DAY_DIR / "day35_checkpoints.sqlite"
DEFAULT_OUTBOX = DAY_DIR / "day35_outbox.sqlite"
LIVE_DB = DAY_DIR / "day35_live_checkpoints.sqlite"
LIVE_OUTBOX = DAY_DIR / "day35_live_outbox.sqlite"
LIVE_LIMITS = {
    "call_limit_seconds": 50.0,
    "task_limit_seconds": 180.0,
    "token_limit": 20000,
}
QUESTION = "蓝湾便签买 8 本多少钱？请说明单价出处。"


def publish_quote(state: dict) -> dict:
    """固定本地工具：记录 quote_id 与草稿，只返回 {'action_count': 此编号记录数}。

    输入是完整 QuoteState，由图传入；此时须已有非空 answer 且 approved=True。
    不更新 messages、trace、steps 或 usages；它不是模型点单的又一条 tool 观察。
    相同业务编号重试只保留一条；若编号被用于不同草稿则报错，避免误当成同一业务。
    SQL 防重机制见当天独立演示；本工具不调用邮件、发货或转账服务。
    """
    if not state["approved"] or not state["answer"]:
        raise ValueError("只有已批准且有草稿的报价才能记录")
    path = Path(state["outbox_db"])
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    try:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS quote_outbox "
            "(quote_id TEXT PRIMARY KEY, draft TEXT NOT NULL)"
        )
        # 参数占位符与唯一键防重在独立演示中讲解；这里只提供固定动作工具。
        cursor = connection.execute(
            "INSERT OR IGNORE INTO quote_outbox (quote_id, draft) VALUES (?, ?)",
            (state["quote_id"], state["answer"]),
        )
        saved = connection.execute(
            "SELECT draft FROM quote_outbox WHERE quote_id = ?", (state["quote_id"],)
        ).fetchone()
        if saved[0] != state["answer"]:
            raise ValueError("此 quote_id 已绑定另一份草稿；新业务请用新的 quote_id")
        connection.commit()
        print(f"  本地模拟发件箱本次新增={cursor.rowcount}；此业务编号已有 1 条记录")
    finally:
        connection.close()
    return {"action_count": 1}


def outbox_count(path: Path, quote_id: str) -> int:
    """检查环境只读查询此业务编号的实际记录数；尚无文件时返回 0。"""
    if not path.exists():
        return 0
    connection = sqlite3.connect(str(path))
    try:
        row = connection.execute(
            "SELECT COUNT(*) FROM quote_outbox WHERE quote_id = ?", (quote_id,)
        ).fetchone()
        return row[0]
    finally:
        connection.close()


def print_snapshot(snapshot: StateSnapshot) -> None:
    """打印可核对的会话状态与发件箱数量，不生成学员观察或结论。"""
    if not snapshot.values:
        print("此 thread_id 没有旧状态；没有读取别的会话。")
        return
    state = snapshot.values
    roles = [message.type for message in state["messages"]]
    tools = [event["tool"] for event in state["trace"] if event["event"] == "tool"]
    print(f"  下一站 next={snapshot.next}；暂停时应是 ('review',)，结束时应是 ()")
    print(f"  草稿={state['answer']}；模型停止原因={state['stop_reason']}")
    print(f"  steps={state['steps']}；消息角色={roles}；已完成的工具={tools}")
    print(f"  已收到响应的用量记录数={len(state['usages'])}")
    print(f"  approved={state['approved']}；图内 action_count={state['action_count']}")
    if state["scenario"] == "live":
        summary = core.support.summarize_usage(
            state["usages"], price=core.support.TEACHING_PRICE
        )
        print(f"  真实响应 token 汇总={summary}")
        print("  token 来自实际响应；known_cost_yuan 仍按教学假价估算，不是实际账单。")
        print_trace(state["trace"])
    actual_count = outbox_count(Path(state["outbox_db"]), state["quote_id"])
    print(f"  发件箱此 quote_id 的实际记录数={actual_count}")
    for task in snapshot.tasks:
        for paused in task.interrupts:
            print(f"  待确认内容={paused.value}")


def compare_core() -> None:
    """让相同离线输入经过已完成的手写版与框架版，打印实际结果供学员解释。"""
    print("=== 同一教学问题，两种已完成的实现；此处不运行新审核图 ===")
    for label, overrides in [("正常答复", {}), ("请求上限", {"max_steps": 1})]:
        old = handwritten.run_agent(QUESTION, **overrides)
        new = core.run_graph_agent(QUESTION, **overrides)
        print(f"\n{label}：{QUESTION}")
        for key in ("answer", "stop_reason", "steps", "usage"):
            print(
                f"  {key}：手写={old[key]}；框架={new[key]}；相同={old[key] == new[key]}"
            )
    print("相同输出只说明这两组离线契约一致；状态和下一站由谁管理，需要你自己说明。")


def data_path(path: Path) -> Path:
    """相对数据路径以 Day 35 目录为基准，不依赖当前终端目录。"""
    return path if path.is_absolute() else DAY_DIR / path


def run_cli(build_graph: Callable[[SqliteSaver], CompiledStateGraph]) -> None:
    """给定运行环境：start 首次运行，status 只读，resume 恢复，compare 对照旧实现。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=("start", "status", "resume", "compare"), default="start"
    )
    parser.add_argument("--ticket-id", default="quote-01", help="检查点的 thread_id")
    parser.add_argument(
        "--quote-id", help="业务操作编号，仅 start 使用；默认 offer-加会话编号"
    )
    parser.add_argument(
        "--decision", choices=("allow", "deny"), help="resume 时必须提供"
    )
    parser.add_argument("--max-steps", type=int, default=4, help="仅 start 使用")
    parser.add_argument(
        "--live",
        action="store_true",
        help="选择真实模型会话库；仅 start 发请求，最多 max-steps 次",
    )
    parser.add_argument("--db", type=Path, help="检查点文件；真实与离线默认用各自文件")
    parser.add_argument(
        "--outbox", type=Path, help="仅 start 使用；真实与离线默认用各自文件"
    )
    args = parser.parse_args()
    if args.phase == "compare":
        if args.live:
            parser.error("compare 只比较既有离线实现，不使用 --live")
        compare_core()
        return
    if args.phase == "resume" and args.decision is None:
        parser.error("--phase resume 还需 --decision allow 或 deny")
    if args.max_steps < 1:
        parser.error("--max-steps 必须是正整数")

    db_path = data_path(args.db or (LIVE_DB if args.live else DEFAULT_DB))
    outbox_path = data_path(
        args.outbox or (LIVE_OUTBOX if args.live else DEFAULT_OUTBOX)
    )
    config = {"configurable": {"thread_id": args.ticket_id}}
    print(f"检查点文件={db_path}；thread_id={args.ticket_id}")
    if args.phase != "start" and not db_path.exists():
        if args.phase == "resume":
            parser.error("检查点文件不存在，没有可恢复状态；请核对 --db 和会话编号")
        print("检查点文件尚不存在，此 thread_id 没有旧状态；未创建数据库。")
        return
    if args.live and args.phase == "start":
        from weeks.week04_frameworks.demos.day35.day35_live_model import (
            validate_settings,
        )

        try:
            model = validate_settings()
        except RuntimeError as error:
            parser.error(str(error))
        print(f"真实模型={model}；从仓库根 .env 读取已有配置，不打印密钥。")
        print(f"最多 {args.max_steps} 次请求；工具与发布仍只操作本地教学数据。")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Day 32 已学：上下文内使用 saver 和 graph，离开后关闭连接，数据仍在文件中。
    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        graph = build_graph(saver)
        before = graph.get_state(config)
        if args.phase == "start":
            if before.values:
                parser.error(
                    "此会话已有状态；用 status/resume 查看或恢复，新任务请换 ticket-id"
                )
            initial = core.make_initial(
                QUESTION,
                scenario="live" if args.live else "normal",
                overrides={
                    **(LIVE_LIMITS if args.live else {}),
                    "max_steps": args.max_steps,
                },
            )
            initial.update(
                quote_id=args.quote_id or f"offer-{args.ticket_id}",
                approved=False,
                action_count=0,
                outbox_db=str(outbox_path),
            )
            # Day 32 的旧调用形状：首次 input 是状态字段字典。
            try:
                graph.invoke(initial, config=config)
            except OpenAIError as error:
                # 不输出 SDK 的完整请求和配置；只显示异常类型与 HTTP 状态。
                status = getattr(error, "status_code", None)
                parser.exit(
                    1,
                    f"真实模型请求失败：{type(error).__name__}，HTTP 状态={status}。"
                    "请检查网络、模型和额度；修好后用新 ticket-id 重试。\n",
                )
        elif args.phase == "resume":
            if not before.values:
                parser.error("此 thread_id 没有可恢复的状态；请核对文件和会话编号")
            if not before.next:
                print("此会话已结束，不再提交恢复，也不重新启动模型。")
            else:
                if before.next != ("review",):
                    parser.error(
                        "此会话未停在人工审核；不能用 allow/deny 恢复请求，请换新 ticket-id"
                    )
                # Day 33 的旧调用形状：只交回人的决定，不重传问题、消息或初始计数。
                graph.invoke(Command(resume=args.decision), config=config)
        print_snapshot(graph.get_state(config))


if __name__ == "__main__":
    print(__doc__)
