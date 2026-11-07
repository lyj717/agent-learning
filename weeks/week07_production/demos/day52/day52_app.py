"""Day52 已知运行背景：为已验收的 Day51 应用提供三个离线回调。

这里只搭旧问答的人工环境，不实现 SSE，不调用模型或读取密钥。
"""

import json

from fastapi import FastAPI
from langchain_core.documents import Document

from weeks.week07_production.demos.shared.service_functions import create_chat_app


def make_app() -> FastAPI:
    """创建旧会话应用；回调均已实现，学生本次不重写业务。"""

    def retrieve(question: str) -> list[Document]:
        """人工检索：无资料返回空列表，其他问题返回一条公开教具证据。"""
        if question == "无资料":
            return []
        return [
            Document(
                id="public.md#L1-L1",
                page_content="请到二楼取书。",
                metadata={"source": "public.md", "line_start": 1, "line_end": 1},
            )
        ]

    def request(messages: list[dict[str, str]]) -> dict:
        """人工请求：接旧消息列表，返回符合旧校验器的原始文本与结束原因。"""
        return {
            "raw_text": json.dumps(
                {
                    "status": "answered",
                    "answer": "请到二楼取书。",
                    "cited_ids": ["public.md#L1-L1"],
                },
                ensure_ascii=False,
            ),
            "finish_reason": "stop",
        }

    def emit(event: dict) -> None:
        """把旧阶段事件写入子进程输出，由运行环境保存到 server.log。"""
        print("旧问答阶段：", json.dumps(event, ensure_ascii=False), flush=True)

    return create_chat_app(retrieve, request, emit)
