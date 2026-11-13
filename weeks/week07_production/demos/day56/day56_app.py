"""Day56 B2：把 serve_question 接成真实 HTTP 服务，并把 span 写成 JSONL。

运行方式（由梯度脚本自动启动，也可手动）：
    python day56_app.py --serve --port 8003
"""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from langchain_core.documents import Document
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace import format_span_id, format_trace_id

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.shared.rag_functions import answer_with_trace
from weeks.week07_production.demos.shared.service_functions import ChatRequest
from weeks.week07_production.exercises.day54_rate_limit_exercises import WindowLimiter
from weeks.week07_production.exercises.day55_error_exercises import error_response
from weeks.week07_production.exercises.day56_integration_exercises import serve_question

SPANS_PATH = Path(
    os.environ.get(
        "DAY56_SPANS",
        Path(__file__).resolve().parent / "outputs" / "spans.jsonl",
    )
)
SPANS_PATH.parent.mkdir(parents=True, exist_ok=True)


class JsonlExporter(SpanExporter):
    """把每个结束的 span 追加写入 JSONL，供事后按 request_id 查。"""

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """写一行一个 span；返回成功。"""
        with SPANS_PATH.open("a", encoding="utf-8") as file:
            for span in spans:
                context = span.context
                row = {
                    "name": span.name,
                    "trace_id": format_trace_id(context.trace_id),
                    "span_id": format_span_id(context.span_id),
                    "parent_span_id": (
                        format_span_id(span.parent.span_id) if span.parent else None
                    ),
                    "attributes": dict(span.attributes or {}),
                    "status": span.status.status_code.name,
                    "start_ms": round(span.start_time / 1_000_000, 3),
                    "end_ms": round(span.end_time / 1_000_000, 3),
                    "elapsed_ms": round(
                        (span.end_time - span.start_time) / 1_000_000, 3
                    ),
                }
                file.write(json.dumps(row, ensure_ascii=False) + "\n")
        return SpanExportResult.SUCCESS


PROVIDER = TracerProvider(
    resource=Resource({"service.name": "agent-learning-day56"}),
    shutdown_on_exit=False,
)
PROVIDER.add_span_processor(SimpleSpanProcessor(JsonlExporter()))
TRACER = PROVIDER.get_tracer("agent_learning.day56")

app = FastAPI()
LIMITER = WindowLimiter(2, 0.5)
SEMAPHORE = asyncio.Semaphore(2)
HISTORY: dict[str, list[dict]] = {}


def retrieve(question: str) -> list[Document]:
    """人工检索：无资料返回空，其他返回一条公开证据。"""
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
    """人工请求：按问题标记模拟超时、连接失败与参数错误。"""
    question = messages[-1]["content"] if messages else ""
    if "超时" in question:
        raise TimeoutError("人工上游超时")
    if "连接失败" in question:
        raise ConnectionError("人工上游连接失败")
    if "参数错误" in question:
        raise ValueError("人工参数错误")
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
    """把旧阶段事件打到标准输出，由 server.log 保存。"""
    print("旧问答阶段：", json.dumps(event, ensure_ascii=False), flush=True)


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查：async def，不受线程池排队影响。"""
    return {"status": "ok", "mode": "offline"}


@app.post("/ask")
async def ask(payload: ChatRequest) -> JSONResponse:
    """校验 → serve_question → 写历史；失败统一映射后返回。"""
    question = payload.question.strip()
    session_id = payload.session_id.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能只有空白")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能只有空白")
    request_id = uuid4().hex
    try:
        checked = await serve_question(
            LIMITER,
            SEMAPHORE,
            TRACER,
            request_id,
            lambda: answer_with_trace(question, retrieve, request, emit),
        )
    except Exception as error:  # noqa: BLE001 - 边界统一映射后返回。
        status, body = error_response(error, request_id)
        return JSONResponse(status_code=status, content=body)
    HISTORY.setdefault(session_id, []).append({"question": question, **checked})
    return JSONResponse(
        status_code=200,
        content={"session_id": session_id, "request_id": request_id, **checked},
    )


@app.get("/sessions/{session_id}/history")
async def history(session_id: str) -> dict:
    """返回该会话已成功的轮次。"""
    return {"session_id": session_id, "turns": HISTORY.get(session_id, [])}


def serve(port: int) -> None:
    """启动真实本机服务。"""
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def main() -> None:
    """支持 --serve；默认入口保存一次自检日志。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8003)
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
        return
    run_logged(
        "day56_app",
        lambda run_dir: print("用梯度脚本启动服务：day56_gradient.py"),
        {"model_calls": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY56_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
