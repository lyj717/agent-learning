"""Day 41 补充：认识作为参数传入的请求函数，以及它的四键返回结构。

为 RAG 整合中“消息交给谁发送、从返回值哪里取得正文”做准备。
仅使用明确写好的 AI 教学响应，不联网，不调用真实模型，不实现 B 的整合逻辑。
从仓库根目录运行：
.venv/Scripts/python.exe -B -X utf8 weeks/week05_rag/demos/day41/day41_request_fn_demo.py
"""

import json
from collections.abc import Callable


def teaching_request(messages: list[dict[str, str]]) -> dict:
    """教学请求函数：接收消息列表，返回手工四键响应，不执行真实请求。

    messages 是必填的 list[dict[str, str]]，每条消息有 role、content。
    返回 dict，恰有 raw_text（str）、finish_reason（str）、usage（此处为 None）、
    model（str）四键；所有值都由 AI 为演示手工指定，不是模型输出或真实用量。
    """
    print(f"  教学函数收到了 {len(messages)} 条消息。")
    for message in messages:
        print(f"  role={message['role']}；content={message['content']}")

    teaching_reply = {
        "status": "insufficient",
        "answer": "这是手工教学回复，仅用于观察接口返回结构。",
        "cited_ids": [],
    }
    return {
        # dumps(字典, ensure_ascii=False)：转成 JSON 字符串，并保留可读中文。
        "raw_text": json.dumps(teaching_reply, ensure_ascii=False),
        "finish_reason": "stop",
        "usage": None,
        "model": "ai-teaching-only",
    }


def observe_request(request_fn: Callable[[list[dict[str, str]]], dict]) -> None:
    """调用传入的请求函数，逐项观察返回值；只打印，返回 None。

    request_fn 是必填参数，接收消息列表并返回四键字典。
    Callable 来自 collections.abc，用类型注解说明“此处接收一个可调用的对象”；
    它不会替你创建函数，也不会自动发送请求。
    """
    messages = [
        {"role": "system", "content": "这是函数传参教学，不是真实问答。"},
        {"role": "user", "content": "请展示约定的四键返回结构。"},
    ]

    print("  关键调用：response = request_fn(messages)")
    response = request_fn(messages)

    print(f"\n  response 类型：{type(response).__name__}；恰有四键：{list(response)}")
    print(f"  raw_text：类型={type(response['raw_text']).__name__}，保存回复正文文本")
    print(f"    {response['raw_text']}")
    print(f"  finish_reason={response['finish_reason']!r}：本次手工指定的结束原因")
    print(f"  usage={response['usage']!r}：本演示未请求模型，没有真实 token 用量")
    print(f"  model={response['model']!r}：标明这是教学响应")
    print("  raw_text 内部还有 status、answer、cited_ids 三键，但它本身仍是字符串。")
    print(
        "  check_grounded_reply 的 raw_text 参数需要这段字符串，不接收整个 response。"
    )


def main() -> None:
    """按用途、概念、场景、调用和边界展示请求函数参数，返回 None。"""
    print("本周目标：做带出处的自有资料问答。")
    print("本演示只讲请求函数怎样传入、怎样调用、返回值怎样读取。")
    print("学完应能在 Day 41 B 中调用提供的请求入口，并分清完整响应与回复正文。")
    print("本次全部是 AI 手工教学消息与响应，不联网，不算学员真实问答记录。")

    print("\n1. 这是什么")
    print("request_fn 是一个参数名，这个参数的值是调用方交给你的请求函数。")
    print("它不是需要另外 import 的库函数；在函数体内照常写 request_fn(messages)。")

    print("\n2. 为什么需要")
    print("同一段问答代码可以接收不同的请求入口，保持相同的输入与返回格式。")
    print("检查时传入教学替身；真实运行时传入已有的真实请求函数。")

    print("\n3. 具体场景")
    print("Day 41 --part b 使用教学替身；ask/batch 加 --live 时使用真实请求入口。")
    print("B 的 messages 来自 build_grounded_messages；这里只手工造两条消息观察接口。")

    print("\n4. 代码与结果")
    print(
        "observe_request(request_fn=teaching_request)：把函数交给参数，不在这里调用它。"
    )
    print("注意传的是 teaching_request，不是 teaching_request(messages) 的返回字典。")
    observe_request(request_fn=teaching_request)

    print("\n5. 注意什么")
    print("Day 41 B 仅在有候选、所有候选出处检查通过后发起回答请求。")
    print("发起前记请求次数；收到后保留完整 response，结束原因与正文分别检查。")
    print("请求可能抛异常；没有收到回复时不能编造 response 或 token 用量。")
    print("模型回复通过格式和引用编号检查后，是否被原文支持仍须人工核对。")


if __name__ == "__main__":
    main()
