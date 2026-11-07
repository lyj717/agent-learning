"""Day52：通过真实 HTTP 接收人工 SSE 事件并判断最终结果。

read_answer_stream 为学员实现；人工服务、检查和运行留证入口由 AI 提供。
接口与运行命令见 day52_学习路线.md，观察原稿见 day52_记录.md。
"""

import argparse
import json
import sys
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import uvicorn

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day52.day52_runtime import running_server
from weeks.week07_production.demos.day52.day52_stream_support import (
    iter_sse_events,
    make_stream_app,
)

READ_TIMEOUT = 0.5


def read_answer_stream(
    base_url: str, mode: str, stop_after: int | None = None
) -> dict[str, str | None]:
    """读取流式回答，保留已收文本并返回终止状态与错误类型。"""
    text = ""
    try:
        with httpx.stream(
            "GET",
            f"{base_url}/answer/{mode}",
            timeout=READ_TIMEOUT,
            trust_env=False,
        ) as response:
            response.raise_for_status()
            rows = []
            count = 0
            for event in iter_sse_events(response.iter_lines()):
                text = "".join(rows)
                if event["event"] == "delta":
                    rows.append(event["data"]["text"])
                    text = "".join(rows)
                    if event["data"]["text"]:
                        count += 1
                    if stop_after is not None and count >= stop_after:
                        text = "".join(rows)
                        return {
                            "state": "interrupted",
                            "text": text,
                            "error_type": None,
                        }
                else:
                    if event["event"] == "done":
                        return {"state": "completed", "text": text, "error_type": None}
                    if event["event"] == "error":
                        return {
                            "state": "error",
                            "text": text,
                            "error_type": event["data"]["error_type"],
                        }
                    if event["event"] == "progress":
                        pass
            return {"state": "incomplete", "text": text, "error_type": None}
    except httpx.ReadTimeout as e:
        return {"state": "error", "text": text, "error_type": type(e).__name__}


# 以下为 AI 提供的人工服务、检查与运行入口。
CASES = [
    {
        "case": "normal",
        "label": "正常完成（含 progress 和空 delta）",
        "mode": "normal",
        "stop_after": None,
        "expected": {
            "state": "completed",
            "text": "请到二楼取书。",
            "error_type": None,
        },
    },
    {
        "case": "error",
        "label": "服务端给出 error 事件",
        "mode": "error",
        "stop_after": None,
        "expected": {"state": "error", "text": "请", "error_type": "TimeoutError"},
    },
    {
        "case": "truncated",
        "label": "HTTP 正常结束但缺少 done/error",
        "mode": "truncated",
        "stop_after": None,
        "expected": {"state": "incomplete", "text": "请", "error_type": None},
    },
    {
        "case": "interrupt",
        "label": "第二个非空 delta 后主动停止，尚未读取 done",
        "mode": "normal",
        "stop_after": 2,
        "expected": {
            "state": "interrupted",
            "text": "请到二楼取书。",
            "error_type": None,
        },
    },
    {
        "case": "timeout",
        "label": "已读到一段，等后续时本地超时",
        "mode": "slow",
        "stop_after": None,
        "expected": {"state": "error", "text": "请", "error_type": "ReadTimeout"},
    },
]


def run_checks(run_dir: Path, selected: str = "all") -> None:
    """实际启动人工服务、调用学员函数并保存全轮检查，不填写学员观察。"""
    cases = [case for case in CASES if selected in {"all", case["case"]}]
    reports = []
    responses: list[httpx.Response] = []
    original_stream = httpx.stream

    # contextmanager：把本轮响应交给检查器观察，正常退出或抛错都走原来的关闭流程。
    @contextmanager
    def observed_stream(*args: Any, **kwargs: Any) -> Iterator[httpx.Response]:
        """只记录真实响应对象，仍使用原 HTTPX 的网络实现。"""
        with original_stream(*args, **kwargs) as response:
            responses.append(response)
            yield response

    with running_server(Path(__file__).resolve(), run_dir) as base_url:
        for case in cases:
            responses.clear()
            print("\n检查：", case["label"])
            try:
                # patch(名字, 替身)：仅本次调用期间记录响应，用于核对关闭，不替代网络。
                with patch("httpx.stream", observed_stream):
                    actual = read_answer_stream(
                        base_url, case["mode"], case["stop_after"]
                    )
            except NotImplementedError:
                raise
            except Exception as error:  # noqa: BLE001 - 检查器收集全部失败，业务函数仍须按题面处理。
                actual = {"raised_type": type(error).__name__, "message": str(error)}
                # print_exc：把实际异常栈写到本轮控制台和日志，帮助定位未处理的异常。
                traceback.print_exc()
            closed = bool(responses) and all(
                response.is_closed for response in responses
            )
            statuses = [response.status_code for response in responses]
            requested = (
                len(responses) == 1
                and responses[0].request.method == "GET"
                and responses[0].request.url.path == f"/answer/{case['mode']}"
            )
            # 先记下是否关闭，再清理错误实现遗留的响应，避免干扰后面的检查。
            for response in responses:
                if not response.is_closed:
                    response.close()
            health = httpx.get(
                base_url + "/health", timeout=3, trust_env=False
            ).status_code
            passed = (
                actual == case["expected"]
                and requested
                and closed
                and statuses == [200]
                and health == 200
            )
            print("实际：", actual)
            print("期望：", case["expected"])
            print("请求次数：", len(responses), "；本次响应已关闭：", closed)
            print("HTTP 状态：", statuses, "；服务器仍可访问：", health)
            print("结果：", "通过" if passed else "未通过")
            reports.append(
                {
                    "case": case["case"],
                    "mode": case["mode"],
                    "stop_after": case["stop_after"],
                    "actual": actual,
                    "expected": case["expected"],
                    "request_count": len(responses),
                    "response_statuses": statuses,
                    "response_closed": closed,
                    "server_health_status": health,
                    "passed": passed,
                }
            )
    passed_count = sum(report["passed"] for report in reports)
    result = {"passed": passed_count, "total": len(reports), "cases": reports}
    (run_dir / "checks.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n共 {passed_count}/{len(reports)} 组通过；这是人工服务，不是模型实验。")
    if passed_count != len(reports):
        raise AssertionError("本轮存在未通过项，完整实际/期望结果已保存到 checks.json")


def serve(port: int) -> None:
    """AI 运行背景：启动题面已提供的人工事件服务。"""
    uvicorn.run(
        make_stream_app(),
        host="127.0.0.1",
        port=port,
        access_log=False,
        log_level="warning",
    )


def main() -> None:
    """支持单情境检查；内部 --serve 分支不执行学员函数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case", choices=["all", *(case["case"] for case in CASES)], default="all"
    )
    parser.add_argument("--serve", action="store_true", help="内部服务入口")
    parser.add_argument("--port", type=int, default=8000, help="内部服务端口")
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
        return

    def execute(run_dir: Path) -> None:
        """自动保存本轮实际输出和配置，不改写学员记录。"""
        run_checks(run_dir, args.case)

    run_logged(
        "stream_exercise",
        execute,
        {"case": args.case, "model_calls": 0, "read_timeout_s": READ_TIMEOUT},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day52/outputs",
        origin_env="DAY52_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
