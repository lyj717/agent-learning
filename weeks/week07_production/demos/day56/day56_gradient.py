"""Day56 B2：启动服务，跑 1/5/10 并发梯度，并抓一次失败请求的 trace。

运行：python weeks/week07_production/demos/day56/day56_gradient.py
服务由本脚本启动和停止，输出保存在 demos/day56/outputs 的新目录。
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day52.day52_runtime import running_server

WORKER = Path(__file__).resolve().parent / "day56_app.py"
LEVELS = [1, 5, 10]


async def one_request(client: httpx.AsyncClient, base_url: str, question: str) -> dict:
    """发一次请求，记录状态、耗时和请求编号。"""
    started = time.perf_counter()
    response = await client.post(
        f"{base_url}/ask", json={"session_id": "demo", "question": question}
    )
    elapsed = round((time.perf_counter() - started) * 1000, 1)
    body: dict[str, Any] = response.json()
    return {
        "status": response.status_code,
        "elapsed_ms": elapsed,
        "request_id": body.get("request_id"),
        "detail": body.get("detail"),
    }


async def run_level(base_url: str, level: int) -> dict:
    """同一档并发：同时发 level 个请求。"""
    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        started = time.perf_counter()
        results = await asyncio.gather(
            *(one_request(client, base_url, "地点") for _ in range(level))
        )
        total = round((time.perf_counter() - started) * 1000, 1)
    latencies = sorted(item["elapsed_ms"] for item in results)
    return {
        "level": level,
        "total_ms": total,
        "max_ms": latencies[-1],
        "min_ms": latencies[0],
        "statuses": [item["status"] for item in results],
    }


def read_failure_trace(spans_path: Path, request_id: str) -> dict:
    """从 JSONL 里按 request_id 找出这次失败的所有 span。"""
    rows = [
        json.loads(line)
        for line in spans_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matched = [row for row in rows if row["attributes"].get("request_id") == request_id]
    roots = [row for row in matched if row["name"] == "request"]
    answers = [row for row in matched if row["name"] == "answer"]
    return {
        "span_count": len(matched),
        "roots": len(roots),
        "answers": len(answers),
        "trace_ids": sorted({row["trace_id"] for row in matched}),
        "names": [row["name"] for row in matched],
        "answer_status": [row["status"] for row in answers],
        "answer_elapsed_ms": [row["elapsed_ms"] for row in answers],
        "root_elapsed_ms": [row["elapsed_ms"] for row in roots],
    }


async def scenario(base_url: str, spans_path: Path) -> dict:
    """三档梯度 + 一次失败请求，返回全部结果。"""
    levels = [await run_level(base_url, level) for level in LEVELS]
    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        failure = await one_request(client, base_url, "超时")
    trace = read_failure_trace(spans_path, failure["request_id"] or "")
    return {"levels": levels, "failure": failure, "failure_trace": trace}


def run(run_dir: Path) -> None:
    """启动服务、跑场景、保存 JSON。"""
    spans_path = run_dir / "spans.jsonl"
    os.environ["DAY56_SPANS"] = str(spans_path)
    with running_server(WORKER, run_dir) as base_url:
        data = asyncio.run(scenario(base_url, spans_path))
    (run_dir / "gradient.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("\n并发梯度：")
    for level in data["levels"]:
        print(
            f"  {level['level']:>2} 档：总耗时 {level['total_ms']}ms，"
            f"最大 {level['max_ms']}ms，最小 {level['min_ms']}ms，"
            f"状态 {level['statuses']}"
        )
    failure = data["failure"]
    trace = data["failure_trace"]
    print(
        f"\n失败请求：状态 {failure['status']}，detail={failure['detail']}，"
        f"request_id={failure['request_id']}"
    )
    print(
        f"  对应 span：共 {trace['span_count']} 个，根 {trace['roots']}，"
        f"answer {trace['answers']}，trace 数 {len(trace['trace_ids'])}"
    )
    print(f"  answer 状态={trace['answer_status']}，耗时={trace['answer_elapsed_ms']}")
    print(f"  request 耗时={trace['root_elapsed_ms']}")


def main() -> None:
    """跑一次梯度并保存运行记录。"""
    run_logged(
        "day56_gradient",
        run,
        {"levels": LEVELS, "model_calls": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY56_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
