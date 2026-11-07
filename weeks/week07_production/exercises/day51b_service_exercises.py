"""Day51B：复用已有问答路径，接 HTTP 与按会话隔离的历史。

--part a 检查请求模型；--part b 检查整合。观察与复验写在 demos/day51b/day51b_记录.md。
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException
from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day51b.day51b_checks import run_a, run_b
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
    """创建拥有独立会话历史的问答应用。"""
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


def main() -> None:
    """保存本轮检查、HTTP 响应与事件；不代写学员实现。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b"], default="a")
    args = parser.parse_args()

    def execute(run_dir: Path) -> None:
        """按参数运行模型或服务的离线检查。"""
        if args.part == "a":
            run_a(ChatRequest, run_dir)
        else:
            run_b(create_chat_app, run_dir)

    run_logged(
        args.part,
        execute,
        {"transport": "testclient_in_process", "model_calls": 0, "phase": "memory"},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day51b/outputs",
        origin_env="DAY51B_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
