"""Day 29：把候选资料变成带来源的简报，练习状态更新与节点连接。

直接运行默认对照 A；运行配置的脚本形参填 --part b 可对照 B。
用 --part warmup 可重看短检查第 2 题的实际输出。
所有候选资料与分数都是固定教学数据，不代表真实检索或模型评分。
"""

import argparse
from copy import deepcopy
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

# === 开工短检查：先闭卷写，约 10 分钟；不会的如实留着，AI 按缺口补 ===
# 1. 模型发出 id=lookup_7 的工具调用后，本地工具返回了资料。
#    下一次模型请求前应新增哪两种消息？哪个字段把点单与观察连起来？
#    若 allow_code=False，而模型仍点了 run_code，谁决定能不能执行？
# 我的回答：
#   新增一条模型的点单和一条观察消息  tool_call_id
#   程序决定能不能执行
# 2. 下面两次 collect_call 的返回值各是什么？* 与 ** 在定义和调用处各做什么？
#    collect_call 的函数体只有 return args, kwargs。
#    collect_call("查库存", 2, timeout=0.5)
#    collect_call(*["查库存", 2], **{"timeout": 0.5})
# 我的预测：
#   "查库存”,"timeout=0.5"
#   "查库存,查库存",""timeout"=0,5,"timeout"=0,5"
# 运行 --part warmup 后核对（保留原预测；需要时另写订正）：
#   直接传参： (('查库存', 2), {'timeout': 0.5})
#   解包传参： (('查库存', 2), {'timeout': 0.5})
# 我的订正（定义处、调用处的 * 与 ** 分别做什么；为什么结果相同）：
#   定义时，*args 把收到的位置参数收成一个元组；**kwargs 把收到的带名字的参数收成一个字典。
#   调用时，*列表 把列表元素拆成位置参数；**字典 把字典里的键和值拆成带名字的参数。
# 3. 连接暂时中断、请求过于频繁、密钥无效、请求缺必填参数：
#    哪些可以有限重试？哪些应先修改配置或请求？不能对所有错误一直重试，为什么？
#    如需核对旧代码：week01_llm_api/chat_cli/llm.py 的异常分类与重试函数。
# 我的回答：
#   连接暂时中断,请求过于频繁可以有限重试，密钥无效，请求缺必填参数应先修改配置或请求
#   并不能所有错误都是重试能解决的，如密钥无效，重试再多遍都没用


class ReviewState(TypedDict):
    """主程序提供全部初始字段，两个节点按各自职责返回部分更新。"""

    question: str
    candidates: list[dict]  # 每条固定含 source: str、text: str、score: float
    min_score: float
    hits: list[dict]
    report: str
    trace: list[str]


def select_sources(state: ReviewState) -> dict:
    """按分数门槛筛选候选资料，返回命中与轨迹的更新。"""
    hits = []
    for candidate in state["candidates"]:
        if candidate["score"] >= state["min_score"]:
            hits.append(candidate)
    trace = state["trace"] + ["筛选资料"]
    return {"hits": hits, "trace": trace}


def build_review_graph() -> CompiledStateGraph:
    """连接筛选与简报节点，返回编译好的固定流程图。"""
    builder = StateGraph(ReviewState)
    builder.add_node("render", render_report)
    builder.add_node("select", select_sources)
    builder.add_edge(START, "select")
    builder.add_edge("select", "render")
    builder.add_edge("render", END)
    return builder.compile()


def render_report(state: ReviewState) -> dict:
    """AI 提供的下游节点：把已有 hits 的出处列成简报，返回报告与轨迹。"""
    sources = [hit["source"] for hit in state["hits"]]
    report = "可用出处：" + "、".join(sources) if sources else "未找到可用资料"
    print(f"  render 节点实际读到的出处：{sources}")
    return {"report": report, "trace": state["trace"] + ["生成简报"]}


def collect_call(*args: object, **kwargs: object) -> tuple[tuple, dict]:
    """短检查的核对工具：原样返回收到的位置参数与关键字参数。"""
    return args, kwargs


def main() -> None:
    """按所选题目打印输入、实际结果、期望结果及原输入是否被修改。"""
    # ArgumentParser：建立参数解析器；--part 选择 warmup、a、b，默认只运行 a。
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("warmup", "a", "b"), default="a")
    part = parser.parse_args().part
    if part == "warmup":
        print("先在顶部写预测，再核对。以下函数只展示 Python 参数，不请求模型。")
        print("直接传参：", collect_call("查库存", 2, timeout=0.5))
        call_args = ["查库存", 2]
        call_options = {"timeout": 0.5}
        print("解包传参：", collect_call(*call_args, **call_options))
        return

    candidates = [
        {"source": "catalog.txt:2", "text": "云杉卡纸每包 9 元", "score": 0.9},
        {"source": "stock.txt:5", "text": "云杉卡纸还有 12 包", "score": 0.6},
        {"source": "old.txt:1", "text": "旧目录未列出该商品", "score": 0.2},
    ]
    cases = [
        ("包括刚好达到门槛的资料", 0.6, ["catalog.txt:2", "stock.txt:5"]),
        ("提高门槛", 0.8, ["catalog.txt:2"]),
        ("全部低于门槛", 0.95, []),
    ]
    graph = build_review_graph() if part == "b" else None
    for label, threshold, expected_sources in cases:
        initial: ReviewState = {
            "question": "云杉卡纸的价格与库存有哪些资料可用？",
            "candidates": candidates,
            "min_score": threshold,
            "hits": [{"source": "旧结果", "text": "上次资料", "score": 1.0}],
            "report": "上次报告",
            "trace": ["收到候选"],
        }
        # deepcopy(对象)：复制嵌套字典与列表，避免比较时双方指向同一个列表。
        # 这是主程序的检查工具；select_sources 不需要用它。
        before = deepcopy(initial)
        print(f"\n=== {label}：min_score={threshold} ===")
        print("候选的出处与分数：", [(x["source"], x["score"]) for x in candidates])
        print(f"期望出处：{expected_sources}")
        if graph is None:
            result = select_sources(initial)
            print(f"实际返回键：{sorted(result)}；期望：['hits', 'trace']")
            expected_trace = ["收到候选", "筛选资料"]
        else:
            # invoke(初始状态)：运行图，返回合并完成的状态字典。
            result = graph.invoke(initial)
            expected_trace = ["收到候选", "筛选资料", "生成简报"]
            expected_report = (
                "可用出处：" + "、".join(expected_sources)
                if expected_sources
                else "未找到可用资料"
            )
            print(f"实际报告：{result['report']}；期望：{expected_report}")
            print(f"问题保留：{result['question'] == before['question']}；期望：True")
            print(
                f"候选保留：{result['candidates'] == before['candidates']}；期望：True"
            )
        print(f"实际出处：{[hit['source'] for hit in result['hits']]}")
        print(f"实际轨迹：{result['trace']}；期望：{expected_trace}")
        print(f"原输入未修改：{initial == before}；期望：True")


if __name__ == "__main__":
    main()

# === 现象与原因：自己运行后填；本日没有另外一份记录 md ===
# 1. min_score 从 0.6 改为 0.8，哪条资料消失？0.6 那次为何仍包含它？
# 我的回答：
#   'stock.txt:5'消失了，因为这条资料的分数为0.6
# 2. 无命中时，为什么输入里的「旧结果」「上次报告」没有变成本次输出？
#    select_sources 没返回 question，最终状态为什么仍有它？
# 我的回答：
#   因为返回的hits开始是一个空列表，如果无命中就会返回[]，select_sources 返回的新 hits 替换了状态中的旧 hits
#   上次报告被render节点改写了
#   因为question并没有被修改，没有被修改的字段最终状态和初始状态是一样的
# 3. render 先注册，却后执行，实际输出中的哪两处能证明？
#    临时只把边改为 START → render → select → END，预测并运行，随后恢复。
#    简报与最终 hits 是否一致？仅看到输入未修改，能否证明流程正确？
# 我的预测：轨迹：'收到候选', '生成简报', '筛选资料' render 节点实际读到的出处：['旧结果']
# 我的实际观察与解释：'收到候选', '生成简报', '筛选资料' render 节点实际读到的出处：['旧结果']
#   先render会导致trace错乱，并且在select之前render就会把旧结果带出来
# 我的补充（报告与最终 hits 是否一致；输入不变能否证明流程正确）：
#   不一致，不能证明流程正确
# 4. 把本次状态、两个节点、连接顺序对应回 Day 27：
#    messages / trace 应放在哪，模型调用与本地工具执行各像哪种节点，
#    原来 if 决定继续或结束的部分还需要增加什么？按你现在的理解写。
# 我的回答：
#   messages/trace应该作为状态，模型调用可以设置为model节点，工具调用可以设置为tool节点
#   需要增加给节点的边
# AI 教学订正（2026-10-15）：上面题目的“按结果选择下一站”涉及 Day 30 的条件边，
# Day 29 只验收状态放在哪里、两个节点分别负责什么；此处不要求学员补写选路答案。
