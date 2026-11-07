"""已验收的 HTTP 服务组件，供 Day52 及后续复用。

索引：ChatRequest、create_chat_app，实际实现原样集中自 Day51B。
Day52 启动环境复用这两项，不重写会话历史；原练习保留学习记录。
新 SSE 逻辑不在这里预填。三项回调接口另见 rag_functions.py。
"""

from collections.abc import Callable

from fastapi import FastAPI, HTTPException
from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict, Field

from weeks.week07_production.demos.shared.rag_functions import answer_with_trace


class ChatRequest(BaseModel):
    """严格接收会话编号与问题的问答请求。"""

    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(strict=True, min_length=1)
    question: str = Field(strict=True, min_length=1)


def create_chat_app(
    retrieve_fn: Callable[[str], list[Document]],
    request_fn: Callable[[list[dict[str, str]]], dict],
    emit: Callable[[dict], None],
) -> FastAPI:
    """创建拥有独立会话历史的问答应用（原 Day51B，保留学员逻辑）。

    三个参数都必填，均为外部已经实现的函数，只由旧 answer_with_trace 调用：
    retrieve_fn(question:str) -> list[Document]，一次检索，空列表表示无资料；
    request_fn(messages:list[dict[str,str]]) -> dict，提供 raw_text 和 finish_reason；
    emit(event:dict) -> None，保存路径由调用方固定，约定它本身不抛异常。
    完整数据结构、调用次数与异常见 rag_functions.py 中 answer_with_trace。

    返回新的 FastAPI 应用，含 GET /health、POST /ask、
    GET /sessions/{session_id}/history；同一应用按清理后的编号分组保留历史，
    新应用另有空历史。正常问答响应含 session_id、request_id、checked；
    历史项含 question、request_id、checked，无资料正常保存 checked=None。
    空白输入 400，模型拒绝 422；旧问答异常继续抛出，不追加历史。
    本组件没有身份鉴权、持久化或多轮模型上下文。
    """
    app = FastAPI()
    histories: dict[str, list[dict]] = {}

    def common_get() -> dict:
        return {"status": "ok", "mode": "offline"}

    def common_post(request: ChatRequest) -> dict:
        question = request.question.strip()
        session_id = request.session_id.strip()
        if not question:
            raise HTTPException(status_code=400, detail="question 不能只有空白")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id 不能只有空白")
        check = answer_with_trace(
            question=question, request_fn=request_fn, retrieve_fn=retrieve_fn, emit=emit
        )
        if session_id not in histories:
            histories[session_id] = []
        histories[session_id].append(
            {
                "question": question,
                **check,
            }
        )
        return {
            "session_id": session_id,
            **check,
        }

    def history_set(session_id: str) -> dict:
        session_id = session_id.strip()
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id 不能只有空白")
        return {
            "session_id": session_id,
            "turns": histories.get(session_id, []),
        }

    app.add_api_route(path="/health", endpoint=common_get, methods=["GET"])
    app.add_api_route(path="/ask", endpoint=common_post, methods=["POST"])
    app.add_api_route(
        path="/sessions/{session_id}/history", endpoint=history_set, methods=["GET"]
    )
    return app
