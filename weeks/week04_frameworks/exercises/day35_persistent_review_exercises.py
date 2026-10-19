"""Day 35：保存报价进度，人工确认后防重记录到本地模拟发件箱。"""

import sys
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt

from weeks.week04_frameworks.demos.day35 import day35_support as support


def review_quote(state: support.QuoteState) -> dict:
    """暂停审核报价草稿，将人的决定写入 approved。"""
    decision = interrupt(
        {
            "question": "确认把这份报价记录到本地模拟发件箱吗？",
            "quote_id": state["quote_id"],
            "draft": state["answer"],
        }
    )
    return {"approved": decision == "allow"}


def route_after_model(state: support.QuoteState) -> Literal["tools", "review", "end"]:
    """根据模型停止原因选择工具、审核或结束。"""
    if state["stop_reason"] is None:
        return "tools"
    elif state["stop_reason"] == "final_answer":
        return "review"
    return "end"


def build_quote_graph(checkpointer: SqliteSaver) -> CompiledStateGraph:
    """连接报价与审核节点，并安装调用者给定的检查点保存器。"""
    builder = StateGraph(support.QuoteState)
    builder.add_node("model", support.model_node)
    builder.add_node("tools", support.tools_node)
    builder.add_node("check", support.check_limits)
    builder.add_node("review", review_quote)
    builder.add_node("publish", support.publish_quote)
    builder.add_edge(START, "model")
    builder.add_conditional_edges(
        "model", route_after_model, {"tools": "tools", "review": "review", "end": END}
    )
    builder.add_conditional_edges(
        "review", support.route_after_review, {"publish": "publish", "end": END}
    )
    builder.add_edge("tools", "check")
    builder.add_conditional_edges(
        "check", support.route_after_limits, {"model": "model", "end": END}
    )
    builder.add_edge("publish", END)
    return builder.compile(checkpointer=checkpointer)


def main() -> None:
    """使用给定入口启动、查看或恢复当前练习的图。"""
    support.run_cli(build_quote_graph)


if __name__ == "__main__":
    main()


# === 开工短复习：先不看旧答案，用几句话回答 ===
# 换一个从未用过的 ticket-id，能否读到旧会话？thread_id 和消息 id 各标识什么？
# quote_id 是今天新介绍的业务字段，先看独立演示，不属于这道旧知识复习题。
# 我的回答：
#   读不到旧对话，thread_od标识对话，消息id标识消息自身
# === 现象与原因：只答逻辑，不要求抄具体值或输出 ===
# 1. 退出 Python 再批准恢复，为什么不会重新生成草稿、重跑模型和工具？
#    恢复入口为什么不重新提交最初的 messages、steps、usages？
# 我的回答：
#   被检查点保存下来了，下一次运行会从检查点开始
#   检查点会保存之前的状态
# 2. 为什么模型已有 final_answer，发件箱却可能为空？检查点与业务编号分别解决什么问题？
# 我的回答：
#   final_answer 只表示模型已经生成报价草稿，发件箱需要人工审核通过才能添加
#   检查点能保存图的当前状态和执行位置。程序退出后，使用同一个 thread_id，可以继续原来的审核流程
#   业务编号标识同一次报价发布操作。数据库配合唯一约束，用它防止重试时把同一笔报价保存成多条记录。
# 3. compare 的两种实现能给出相同结果，谁分别管理状态和下一步？
#    结合这次改动，说一个你更愿意用框架的场景、一个直接写普通函数就够的场景。
# 我的回答：
#   手写版由代码直接维护列表和变量，靠 for 循环、if 判断、函数调用和 return 控制流程
#   LangGraph版由节点返回更新字典，LangGraph按字段规则把更新合入当前状态，普通边指定路线，条件路由返回下一站标签，再由LangGraph执行对应节点
#   流程短，顺序明确，流程控制很少的时候用手写版；需要管理多阶段状态、暂停和恢复时用框架
