"""Day55 A1：把内部异常翻译成对外错误响应，且不泄露敏感信息。

入口提供异常与 request_id，检查器逐组打印实际与期望。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day55.day55_error_checks import check_cases


def error_response(exc: BaseException, request_id: str) -> tuple[int, dict[str, str]]:
    """按异常类别返回状态码与公开正文，不泄露内部信息。"""
    if isinstance(exc, TimeoutError):
        return 504, {"detail": "上游超时", "request_id": request_id}
    if isinstance(exc, ConnectionError):
        return 502, {"detail": "上游连接失败", "request_id": request_id}
    if isinstance(exc, ValueError):
        return 400, {"detail": "请求不合法", "request_id": request_id}
    return 500, {"detail": "内部错误", "request_id": request_id}


def run_exercise(run_dir: Path) -> None:
    """把学员的错误响应函数交给五组检查，保存实际结果；无需修改。"""
    check_cases(error_response, run_dir)


def main() -> None:
    """保存本轮控制台、配置、源码摘要和检查 JSON。"""
    run_logged(
        "error_exercise",
        run_exercise,
        {"model_calls": 0, "http_requests": 0, "case_count": 5},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day55/outputs",
        origin_env="DAY55_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
