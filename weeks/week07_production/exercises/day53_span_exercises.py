"""Day53 C：只给一个外部动作加标准追踪，保留原结果与异常。

完整接口见 demos/day53/day53_学习路线.md；SDK 与四组验收由 AI 提供。
观察统一写 demos/day53/day53_记录.md，不在这里重复作答。
"""

import sys
from collections.abc import Callable
from pathlib import Path

from opentelemetry.trace import Span, Status, StatusCode, Tracer

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day53.day53_stage_checks import check_stage_cases


def trace_stage(
    tracer: Tracer,
    request_id: str,
    stage: str,
    action: Callable[[], dict[str, object]],
) -> dict[str, object]:
    """为外部动作记录标准 span，正常返回原结果，失败记录类型并传出原异常。"""
    span: Span
    with tracer.start_as_current_span(
        stage,
        attributes={"request_id": request_id, "stage": stage},
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            result = action()
        except Exception as error:
            span.set_attribute("error_type", type(error).__name__)
            span.set_status(Status(StatusCode.ERROR))
            raise
        span.set_status(Status(StatusCode.OK))
    return result


def run_exercise(run_dir: Path) -> None:
    """将学员函数交给已准备好的四组检查，保存实际结果；无需修改。"""
    check_stage_cases(trace_stage, run_dir)


def main() -> None:
    """自动保存控制台、配置、源码摘要和每组真实 SDK 输出。"""
    run_logged(
        "span_exercise",
        run_exercise,
        {"model_calls": 0, "case_count": 4, "otel_sdk": "1.45.2"},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day53/outputs",
        origin_env="DAY53_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
