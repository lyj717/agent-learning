"""Day 33 整合演示：人工确认、检查点、恢复与动作去重。

各个知识点演示读完后，再读这一份完整业务图：review → 获准后 publish → END。
本文件自带图定义；只复用幂等演示中已经讲清接口的 record_once。
先运行一次，等 Python 退出后，再加 --resume 运行一次。
"""

import sys
from pathlib import Path
from typing import Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt

from weeks.week04_frameworks.demos.day33.day33_idempotency_demo import record_once

# resolve() 把脚本旁数据库的路径转成绝对路径，不受终端工作目录影响。
# 使用新文件名，与旧版教具可能留下的检查点分开；不会删除旧文件。
DB_PATH = Path(__file__).with_name("day33_integrated_review.sqlite").resolve()
CONFIG = {"configurable": {"thread_id": "day33-integrated-notice"}}
ACTION_LOG: list[str] = []


class NoticeState(TypedDict):
    """这次整合业务需要保存的公告与审核状态。"""

    notice_id: str
    text: str
    approved: bool
    action_count: int


def main() -> None:
    """先暂停，再由第二个进程恢复并执行模拟动作。"""
    # sys.argv[1:] 是脚本参数列表；这里只接受空列表或一个 --resume。
    args = sys.argv[1:]
    if args not in ([], ["--resume"]):
        raise SystemExit("用法：先不加参数运行，再加 --resume 运行")

    print("=== 1. 本次把哪些知识接起来 ===")
    print("interrupt 提出审核请求；文件检查点保存会话；Command(resume=True) 送回批准。")
    print("审核节点恢复后返回 approved，条件边再决定是否进入模拟发布节点。")

    print("\n=== 2. 为什么分成两个节点 ===")
    print("review 只负责等待决定；获准后 publish 才调用已学过的 record_once。")

    print("\n=== 3. 场景 ===")
    print(f"数据库：{DB_PATH}")
    print(f"会话：{CONFIG['configurable']['thread_id']}")
    print("公告 notice-42：云杉耳机维修说明。发布只改本进程列表，不连接外部系统。")

    print("\n=== 4. 完整流程的真实输出 ===")
    # Day 32 的保存器：两个进程分别打开同一文件，并用同一 thread_id 找回状态。
    with SqliteSaver.from_conn_string(str(DB_PATH)) as saver:
        graph = build_graph(saver)
        # 这里才整合 snapshot.next：它表示接下来有待执行的节点名称。
        before = graph.get_state(CONFIG)
        if not args:
            if before.next:
                print(f"已有等待节点 {before.next}；直接加 --resume 运行即可。")
                return
            initial: NoticeState = {
                "notice_id": "notice-42",
                "text": "云杉耳机维修说明",
                "approved": False,
                "action_count": 0,
            }
            paused = graph.invoke(initial, CONFIG)
            print(f"4.1 给人的审核请求：{paused['__interrupt__'][0].value}")
            print(
                f"4.2 等待节点={graph.get_state(CONFIG).next}；模拟发布次数={len(ACTION_LOG)}"
            )
            print("4.3 本次进程结束。人在教学中批准后，另起一次运行：")
            print(
                "    .venv\\Scripts\\python.exe -B "
                "weeks\\week04_frameworks\\demos\\day33\\day33_checkpoint_resume_demo.py --resume"
            )
        else:
            if before.next != ("review",):
                print("没有等待中的 review；请先不加参数运行一次。")
                return
            # --resume 在这个教具里代表人已批准，True 作为 interrupt 的返回值。
            final = graph.invoke(Command(resume=True), CONFIG)
            print(
                f"4.1 approved={final['approved']}，"
                f"状态保存的 action_count={final['action_count']}"
            )
            print(f"4.2 完成后 next={graph.get_state(CONFIG).next}")
            # 与幂等知识点相同：真正模拟再请求一次，检查效果是否新增。
            added = record_once(final["notice_id"], ACTION_LOG)
            print(
                f"4.3 同编号再请求：新增={added}；本进程模拟发布次数={len(ACTION_LOG)}"
            )

    print("\n=== 5. 这个教具的边界 ===")
    print("SQLite 持久保存的是图状态；ACTION_LOG 只模拟本进程里的外部动作。")
    print("真实外部动作仍需持久的业务编号去重；不能把本列表当成跨进程防重实现。")


def review_notice(state: NoticeState) -> dict:
    """只提出审核请求，恢复后把人的布尔决定写入状态。"""
    print("    进入 review 节点。")
    decision = interrupt(
        {
            "question": "允许发布吗？",
            "notice_id": state["notice_id"],
            "text": state["text"],
        }
    )
    return {"approved": decision is True}


def choose_next(state: NoticeState) -> Literal["publish", "stop"]:
    """复用 Day 30 的条件选路，获准才执行动作。"""
    return "publish" if state["approved"] else "stop"


def publish_notice(state: NoticeState) -> dict:
    """复用幂等知识点中的函数，模拟按业务编号记录动作。"""
    added = record_once(state["notice_id"], ACTION_LOG)
    print(f"    publish：本次新增动作={added}，动作数={len(ACTION_LOG)}")
    return {"action_count": len(ACTION_LOG)}


def build_graph(checkpointer: SqliteSaver) -> CompiledStateGraph:
    """把审核、条件边、模拟动作与保存器接成一张完整图。"""
    builder = StateGraph(NoticeState)
    builder.add_node("review", review_notice)
    builder.add_node("publish", publish_notice)
    builder.add_edge(START, "review")
    builder.add_conditional_edges(
        "review", choose_next, {"publish": "publish", "stop": END}
    )
    builder.add_edge("publish", END)
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    main()
