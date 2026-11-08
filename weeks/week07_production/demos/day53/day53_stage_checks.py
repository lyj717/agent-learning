"""Day53 C 的 AI 验收背景：准备四个离线动作和外层段，保存实际与期望。

学员只需按练习函数旁的完整接口写 trace_stage，不需要读这里才能做题。
本文件没有 trace_stage 的实现，不调用模型、HTTP 或真实凭据。
"""

import json
from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path

from opentelemetry import trace

from weeks.week07_production.demos.day53.day53_trace_runtime import local_tracing


def prepare_action(
    result: dict[str, object] | None,
    original: Exception | None,
    calls: list[None],
    contexts: list[trace.SpanContext],
) -> Callable[[], dict[str, object]]:
    """为单个案例固定输入；返回无参数离线动作，不含学员应实现的追踪逻辑。"""

    def action() -> dict[str, object]:
        """计一次调用并返回原结果，或抛出预先准备的原异常。"""
        calls.append(None)
        contexts.append(trace.get_current_span().get_span_context())
        if original is not None:
            raise original
        assert result is not None
        return result

    return action


def check_stage_cases(
    function: Callable[
        [trace.Tracer, str, str, Callable[[], dict[str, object]]], dict[str, object]
    ],
    run_dir: Path,
) -> None:
    """调用待验收函数，核对行为和实际 SDK 字段，失败也保存四组结果。

    function 是学员已写或尚未写完的 trace_stage；run_dir 是本轮独立日志目录。
    返回 None；任一组不符时最后抛 AssertionError，检查结果已提前写入 JSON。
    动作的返回对象、异常对象和活动 span 在内存核对，不把敏感消息打印到日志。
    """
    cases = [
        (
            "ok_child",
            "format_notice",
            True,
            None,
            {"answer": "二楼", "citations": ["rule-2"]},
        ),
        ("empty_child", "lookup_notice", True, None, {"answer": "", "citations": []}),
        ("timeout_child", "retrieve", True, TimeoutError, None),
        ("invalid_root", "validate", False, ValueError, None),
    ]
    checks = []
    print("只需实现 trace_stage；下面显示各组实际与期望，不需要读验收器做题。")
    for case_name, stage, with_parent, error_class, result in cases:
        case_dir = run_dir / case_name
        case_dir.mkdir()
        request_id = f"case-{case_name}"
        private_marker = f"SIMULATED_CREDENTIAL_{case_name}"
        original = error_class(private_marker) if error_class else None
        calls = []
        action_contexts = []
        action = prepare_action(result, original, calls, action_contexts)
        returned = None
        received = None
        with local_tracing(case_dir) as tracer:
            # nullcontext：无父段案例的空 with 环境，不创建任何 span。
            parent_manager = (
                tracer.start_as_current_span(
                    "request_work",
                    record_exception=False,
                    set_status_on_exception=False,
                )
                if with_parent
                else nullcontext()
            )
            with parent_manager:
                before = trace.get_current_span().get_span_context()

                try:
                    returned = function(tracer, request_id, stage, action)
                except Exception as error:  # noqa: BLE001 -- 验收器接收并核对任意普通异常。
                    received = error
                restored = trace.get_current_span().get_span_context() == before

        raw_text = (case_dir / "otel_spans.json").read_text(encoding="utf-8")
        raw = json.loads(raw_text)
        summary = json.loads(
            (case_dir / "trace_summary.json").read_text(encoding="utf-8")
        )
        stage_rows = [row for row in raw if row["name"] == stage]
        row = stage_rows[0] if len(stage_rows) == 1 else None
        stage_summary = next((r for r in summary["rows"] if r["name"] == stage), None)
        expected_status = "ERROR" if original else "OK"
        expected_attributes = {"request_id": request_id, "stage": stage}
        if original:
            expected_attributes["error_type"] = type(original).__name__
        expected_parent = trace.format_span_id(before.span_id) if with_parent else None
        behavior_ok = (
            received is original
            if original
            else received is None and returned is result
        )
        active_ok = bool(
            stage_summary
            and len(action_contexts) == 1
            and trace.format_span_id(action_contexts[0].span_id)
            == stage_summary["span_id"]
        )
        parent_ok = bool(
            stage_summary
            and stage_summary["parent_span_id"] == expected_parent
            and (
                not with_parent
                or stage_summary["trace_id"] == trace.format_trace_id(before.trace_id)
            )
        )
        fields_ok = bool(
            row
            and row["attributes"] == expected_attributes
            and row["status"]["status_code"] == expected_status
            and not row["status"].get("description")
            and not row["events"]
            and private_marker not in raw_text
        )
        field_checks = {
            "attributes_match": bool(row and row["attributes"] == expected_attributes),
            "status_matches": bool(
                row and row["status"]["status_code"] == expected_status
            ),
            "description_empty": bool(row and not row["status"].get("description")),
            "events_empty": bool(row and not row["events"]),
            "sensitive_marker_absent": private_marker not in raw_text,
        }
        missing_attributes = sorted(
            set(expected_attributes) - set(row["attributes"] if row else {})
        )
        extra_attribute_count = len(
            set(row["attributes"] if row else {}) - set(expected_attributes)
        )
        passed = all(
            [
                len(calls) == 1,
                behavior_ok,
                restored,
                active_ok,
                parent_ok,
                fields_ok,
                len(raw) == (2 if with_parent else 1),
            ]
        )
        actual = {
            "case": case_name,
            "passed": passed,
            "action_calls": len(calls),
            "same_result_or_exception": behavior_ok,
            "received_error_type": type(received).__name__ if received else None,
            "status": row["status"]["status_code"] if row else None,
            "error_type": row["attributes"].get("error_type") if row else None,
            "parent_span_id": stage_summary["parent_span_id"]
            if stage_summary
            else None,
            "current_restored": restored,
            "action_inside_stage": active_ok,
            "parent_matches": parent_ok,
            "safe_fields_match": fields_ok,
            "field_checks": field_checks,
            "missing_attributes": missing_attributes,
            "extra_attribute_count": extra_attribute_count,
            "span_count": len(raw),
        }
        checks.append(actual)
        print(f"\n{case_name}：{'通过' if passed else '未通过'}")
        print(
            f"实际 action={len(calls)} 次；status={actual['status']}；"
            f"error_type={actual['error_type']}；原对象保持={behavior_ok}"
        )
        print(f"实际传出异常类型：{actual['received_error_type']}（不打印消息）")
        print(
            f"期望 action=1 次；status={expected_status}；"
            f"error_type={type(original).__name__ if original else None}；原对象保持=True"
        )
        print(
            f"实际：当前段恢复={restored}；动作在阶段段内={active_ok}；"
            f"父段匹配={parent_ok}；字段和无泄漏检查={fields_ok}"
        )
        if not fields_ok:
            print(
                f"  拆开看：属性符合={field_checks['attributes_match']}；"
                f"状态符合={field_checks['status_matches']}；"
                f"未写状态描述={field_checks['description_empty']}；"
                f"未写异常事件={field_checks['events_empty']}；"
                f"模拟敏感标记未写入={field_checks['sensitive_marker_absent']}"
            )
            print(
                f"  缺少题目要求的属性：{missing_attributes}；"
                f"多余属性个数：{extra_attribute_count}（不打印字段内容）"
            )

    passed_count = sum(row["passed"] for row in checks)
    (run_dir / "exercise_checks.json").write_text(
        json.dumps(
            {"passed": passed_count, "total": 4, "cases": checks},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n本次 {passed_count}/4；实际 span 和结果已保存；模型调用 0 次。")
    assert passed_count == 4, "阶段追踪还有未通过项，请按上面的实际/期望订正"
