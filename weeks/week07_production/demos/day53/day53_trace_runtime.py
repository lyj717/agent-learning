"""Day53 的本地追踪运行环境，由 AI 提供，不含学员练习答案。

local_tracing(run_dir)：在 with 内提供真实 OpenTelemetry Tracer；退出时保存本轮记录。
配置、收集与文件保存是运行背景，先读各演示的 demonstrate，不要求重写这里。
SDK 记录保存在内存，随后写入本地 JSON，不连接服务商、追踪平台或 Collector。
"""

import json
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_ON


def save_spans(run_dir: Path, spans: Sequence[ReadableSpan]) -> None:
    """保存实际 SDK 记录和便于初学者阅读的字段，不填写学员观察。

    run_dir 是本轮已经存在的独立输出目录；spans 是 SDK 已结束的 span 序列。
    返回 None，写出 otel_spans.json（SDK 全字段）和 trace_summary.json（关联字段）。
    保留 SDK 交出记录的顺序，即结束顺序；不把它冒充开始顺序。
    """
    rows = []
    raw_spans = []
    for span in spans:
        context = span.context
        if context is None or span.start_time is None or span.end_time is None:
            raise RuntimeError("本课应只收到已经开始、结束且有编号的 span")
        # to_json：SDK 将一条实际记录转为 JSON 文本；loads 后收进本轮 JSON 列表。
        raw_spans.append(json.loads(span.to_json()))
        rows.append(
            {
                "name": span.name,
                # format_*_id：将 SDK 的整数编号转为固定长度的十六进制字符串。
                "trace_id": trace.format_trace_id(context.trace_id),
                "span_id": trace.format_span_id(context.span_id),
                "parent_span_id": (
                    trace.format_span_id(span.parent.span_id) if span.parent else None
                ),
                "ended": True,
                "elapsed_ms": (span.end_time - span.start_time) / 1_000_000,
            }
        )
    summary = {
        "span_count": len(rows),
        "trace_count": len({row["trace_id"] for row in rows}),
        "root_count": sum(row["parent_span_id"] is None for row in rows),
        "rows": rows,
    }
    for name, data in [
        ("otel_spans.json", raw_spans),
        ("trace_summary.json", summary),
    ]:
        (run_dir / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print("\nSDK 已交出的记录（按结束先后排列）：")
    for row in rows:
        print(f"  name={row['name']}；elapsed_ms={row['elapsed_ms']:.3f}")
        print(f"    trace_id={row['trace_id']}")
        print(f"    span_id={row['span_id']}；parent_span_id={row['parent_span_id']}")
    print(
        f"共 {summary['span_count']} 个 span、{summary['trace_count']} 条 trace、"
        f"{summary['root_count']} 个根 span；详细字段已保存。"
    )


@contextmanager
def local_tracing(run_dir: Path) -> Iterator[trace.Tracer]:
    """进入时提供已经配置好的 Tracer，退出时保存记录并关闭本轮 SDK。

    run_dir（Path，必填）：run_logged 已创建的本轮目录，学员不手工填写或新建。
    用法：with local_tracing(run_dir) as tracer:，tracer 是工具对象，不是函数或结果。
    本环境使用真实 SDK、全量记录、进程内保存；不覆盖全局 TracerProvider。
    with 内创建的各 span 仍须用各自的 with 结束；本函数不代创建业务 span。
    退出时即使调用方抛异常也尝试保存已有记录，原异常继续传出。
    """
    # Resource：本轮应用的公开标签；直接构造，避免读取环境里的资源属性。
    provider = TracerProvider(
        resource=Resource({"service.name": "agent-learning-day53"}),
        sampler=ALWAYS_ON,
        shutdown_on_exit=False,
    )
    # InMemorySpanExporter：SDK 官方提供的内存保存器，不向外发送数据。
    exporter = InMemorySpanExporter()
    # SimpleSpanProcessor：每个 span 结束时立即交给上面的保存器。
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # get_tracer(固定工具名)：从本轮 provider 取得创建 span 的工具对象。
    tracer = provider.get_tracer("agent_learning.day53")
    try:
        yield tracer
    finally:
        try:
            provider.force_flush()  # 完成本轮待交出的记录，不建立网络连接。
            save_spans(run_dir, exporter.get_finished_spans())
        finally:
            provider.shutdown()  # 释放本轮 SDK 资源，不影响其他演示的 provider。
