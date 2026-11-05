"""Day50：给 RAG 的检索→消息→生成→校验路径记录可关联的阶段日志。

离线对照入口支持 --part a/b。运行记录与接口说明见 demos/day50/，旧函数见 demos/shared/。
"""

import argparse
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 以下两项是 AI 维护的留证与验收工具；做题无需阅读它们的内部实现。
from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day50.day50_checks import run_a, run_b
from weeks.week07_production.demos.shared.rag_functions import (
    build_grounded_messages,
    check_grounded_reply,
)


def trace_call(
    request_id: str,
    stage: str,
    action: Callable[[], Any],
    emit: Callable[[dict], None],
) -> Any:
    """执行无参数动作，记录阶段事件与耗时，原样返回结果或继续抛出异常。"""
    emit(
        {
            "request_id": request_id,
            "stage": stage,
            "state": "start",
        }
    )
    start_time = time.perf_counter()
    try:
        result = action()
    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        emit(
            {
                "request_id": request_id,
                "stage": stage,
                "state": "error",
                "elapsed_ms": elapsed_ms,
                "error_type": type(error).__name__,
            }
        )
        raise
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    emit(
        {
            "request_id": request_id,
            "stage": stage,
            "state": "ok",
            "elapsed_ms": elapsed_ms,
        }
    )
    return result


def answer_with_trace(
    question: str,
    retrieve_fn: Callable[[str], list[Document]],
    request_fn: Callable[[list[dict[str, str]]], dict],
    emit: Callable[[dict], None],
) -> dict:
    """为一次检索、消息准备、生成和校验记录同一请求 ID 的阶段日志。"""
    request_id = uuid4().hex

    def retrieve_action() -> Any:
        return retrieve_fn(question)

    evidence = trace_call(
        request_id=request_id, stage="retrieve", action=retrieve_action, emit=emit
    )
    if not evidence:
        return {"request_id": request_id, "checked": None}

    def prepare_action() -> Any:
        return build_grounded_messages(question=question, evidence=evidence)

    messages = trace_call(
        request_id=request_id, stage="prepare", action=prepare_action, emit=emit
    )

    def generate_action() -> Any:
        return request_fn(messages)

    answer = trace_call(
        request_id=request_id, stage="generate", action=generate_action, emit=emit
    )

    def validate_action() -> Any:
        if answer["finish_reason"] != "stop":
            raise ValueError
        raw_text = answer["raw_text"]
        return check_grounded_reply(raw_text=raw_text, evidence=evidence)

    checked = trace_call(
        request_id=request_id,
        stage="validate",
        action=validate_action,
        emit=emit,
    )
    return {"request_id": request_id, "checked": checked}


# 以下是 AI 维护的运行入口；直接用 --part a/b 运行，无需把这里的调用链当作题目阅读。
def main() -> None:
    """按题保存本轮配置、对照输出、事件及异常，失败也留证。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b"], default="a")
    args = parser.parse_args()

    def execute(run_dir: Path) -> None:
        """运行 AI 人工对照，不加载模型、读旧样本或请求服务商。"""
        if args.part == "a":
            run_a(trace_call, run_dir)
        else:
            run_b(answer_with_trace, run_dir)

    run_logged(
        args.part,
        execute,
        {"mode": "offline_callbacks", "model_calls": 0},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day50/outputs",
        origin_env="DAY50_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
