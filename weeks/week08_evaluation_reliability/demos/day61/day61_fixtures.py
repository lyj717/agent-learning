"""Day61 教具：五类失败模式的「正常版 / 故障版」，由环境变量切换。

默认 good；设置 DAY61_VARIANT=bad 后，每个函数表现出一种真实故障：
循环不设上限、未知工具照样执行、引用编造编号、格式不校验、越权工具放行。
学员的检查函数要能在 bad 下失败、在 good 下通过；检查器负责两种变体。
"""

import json
import os

SANDBOX = "notes"


class ToolError(Exception):
    """工具不存在或参数不合法。"""


class FormatError(Exception):
    """回答不是约定的 JSON 结构。"""


def _bad() -> bool:
    """当前是否运行故障版；每次调用时读取，方便检查器切换。"""
    return os.environ.get("DAY61_VARIANT") == "bad"


def run_agent_loop(max_steps: int = 5) -> dict[str, int | str]:
    """跑一个最小 Agent 循环，返回步数与结束状态。

    max_steps 是允许的最大步数。正常版最多走 max_steps 步；
    故障版会多走 4 步，模拟「没有把上限接进循环」。
    """
    if _bad():
        return {"steps": max_steps + 4, "status": "done"}
    steps = min(3, max_steps)
    status = "done" if steps < max_steps else "limit"
    return {"steps": steps, "status": status}


def dispatch_tool(name: str, arguments: dict) -> dict[str, str]:
    """按白名单执行工具；正常版拒绝未知工具，故障版照样执行。"""
    allowed = {"calculator": {"expression"}}
    if name not in allowed:
        if _bad():
            return {"result": "unknown tool executed"}
        raise ToolError(f"未知工具：{name}")
    if set(arguments) != allowed[name]:
        raise ToolError(f"参数不符合 {name} 的接口")
    return {"result": "ok"}


def answer_with_citations(question: str) -> dict[str, object]:
    """返回一份带引用的回答；故障版会引用一个不存在的编号。"""
    evidence_ids = ["notes/python-notes.md#L40-L42", "notes/python-notes.md#L41-L43"]
    if _bad():
        cited_ids = ["notes/python-notes.md#L99-L100"]
    else:
        cited_ids = ["notes/python-notes.md#L40-L42"]
    return {
        "question": question,
        "status": "answered",
        "answer": "示例回答",
        "cited_ids": cited_ids,
        "evidence_ids": evidence_ids,
    }


def parse_answer(raw: str) -> dict[str, object]:
    """解析回答 JSON；正常版校验三个键，故障版只做 json.loads。"""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        if _bad():
            raise
        raise FormatError(f"不是合法 JSON：{error}") from error
    if _bad():
        return data
    if not isinstance(data, dict) or set(data) != {
        "status",
        "answer",
        "cited_ids",
    }:
        raise FormatError("键必须恰好是 status、answer、cited_ids")
    if data["status"] not in {"answered", "insufficient"}:
        raise FormatError("status 不合法")
    if not isinstance(data["answer"], str):
        raise FormatError("answer 不是字符串")
    if not isinstance(data["cited_ids"], list) or any(
        not isinstance(item, str) for item in data["cited_ids"]
    ):
        raise FormatError("cited_ids 不是字符串列表")
    return data


def authorize_tool(tool: str, path: str) -> bool:
    """只允许读取 sandbox 内的文件；故障版对删除与路径穿越全部放行。"""
    if _bad():
        return True
    if tool != "read_file":
        raise PermissionError(f"不允许的工具：{tool}")
    normalized = os.path.normpath(path)
    if normalized.startswith("..") or not normalized.startswith(SANDBOX):
        raise PermissionError(f"路径越界：{path}")
    return True
