"""Day53 A：认识真实 OpenTelemetry span 的生命周期、编号和父子关系。

从 demonstrate 读起；它直接展示关键 API，没有完整 RAG 或练习参考实现。
本例自带本地追踪环境，不依赖先跑另一份演示，不请求模型或启动 HTTP 服务。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day53.day53_trace_runtime import local_tracing


def demonstrate(run_dir: Path) -> None:
    """先认各对象，再对照嵌套和独立创建；输入目录由运行入口准备。"""
    print("本周要让 Agent 服务的一次处理过程能被查清：经历哪些阶段、哪里失败。")
    print("Day50 已手工写阶段事件；今天开始用一种标准工具表达整次过程与各阶段。")
    print(
        "本演示只负责 trace/span、with 的生命周期和父子编号，后段练习再记属性与失败。"
    )
    print("学完应能看一条阶段记录，找出它属于哪次过程、直接上级是谁。")

    print("\n一、是什么：把一次完整处理看成一条 trace（轨迹）。")
    print("其中一个有开始、结束的工作片段叫 span；整次处理本身也可有一个外层 span。")
    print("为什么需要：既能按编号找齐同一次处理，也能看出哪个阶段包含哪个阶段。")
    print("场景：为图书馆通知制作一张卡片，内部先读取规则，再呈现卡片。")
    print("本例文字固定，只观察记录关系，不代表模型回答或真实业务服务。")

    print("\n二、谁提供什么、调用后拿到什么")
    print("OpenTelemetry 是这里选用的追踪工具；Python 中可简称 OTel。")
    print("本机 API/SDK 均为 1.45.2，已配置本地保存，不需要另一份密钥。")
    print(
        "local_tracing 从同目录运行环境导入，进入 with 后把已准备好的 tracer 交给你。"
    )
    print(
        "tracer 是创建记录段的工具；span 是其中某一段；trace 是这些段共同组成的轨迹。"
    )
    print(
        "运行环境已做好：provider 提供工具，processor 接收结束记录，exporter 暂存记录。"
    )
    print("现在只认识它们的用途，先不用重写这三项配置。")
    print("\n本节关键调用：")
    print('  with tracer.start_as_current_span("阶段名",')
    print("          record_exception=False, set_status_on_exception=False) as span:")
    print("      在这里执行这一段工作")
    print("阶段名必填，是你给记录起的名字，不会自动调用同名函数。")
    print(
        "进入 with：创建并开始一个 span，同时把它设为当前工作段；as span 接到这个对象。"
    )
    print("在它内部新建的段，默认以当前段为直接上级；退出后当前段恢复为先前的上级。")
    print("退出 with：自动结束本段记录。end_on_exit 默认 True，本例保持默认。")
    print(
        "两个异常开关默认 True；本课显式 False，避免 SDK 自动保存异常消息或自动标状态。"
    )
    print("怎样手工标安全的失败信息留到后段；本节没有失败业务。")
    print("其他可选参数如 attributes、context 本节不用；这里没有传回调函数。")
    print(
        "get_span_context() 不用参数，返回本段的编号信息，可读取 trace_id 和 span_id。"
    )
    print("is_recording() 不用参数，返回 bool；本课全量记录，段内 True，结束后 False。")
    print(
        "trace_id 标记所属整条轨迹；span_id 标记这一段；parent_span_id 指向直接上级。"
    )
    print("最外层没有上级，保存时 parent_span_id 为 None；不用记住编号的具体数字。")

    with local_tracing(run_dir) as tracer:
        print("\n三、嵌套：在一个整次处理里记录两个阶段")
        # start_as_current_span：创建并激活工作段；进入 with 得到 Span，退出结束。
        with tracer.start_as_current_span(
            "notice_job", record_exception=False, set_status_on_exception=False
        ) as job_span:
            # get_span_context：取得 SDK 自动给出的编号信息，不需要手工生成 ID。
            job_context = job_span.get_span_context()
            print("进入 notice_job，还在记录：", job_span.is_recording())
            with tracer.start_as_current_span(
                "read_rule", record_exception=False, set_status_on_exception=False
            ) as rule_span:
                rule = "每次最多借五本书。"
                print("读取规则：", rule)
                print(
                    "read_rule 与 notice_job 的 trace_id 相同：",
                    rule_span.get_span_context().trace_id == job_context.trace_id,
                )
            print("read_rule 已结束，继续在 notice_job 中创建下一段。")
            with tracer.start_as_current_span(
                "render_card", record_exception=False, set_status_on_exception=False
            ):
                print("呈现卡片：借阅提示——" + rule)
        print("离开 notice_job，还在记录：", job_span.is_recording())
        print("注意：外层包含两个阶段；第二阶段是第一个阶段的兄弟，不是它的子段。")

        print("\n四、独立：同一 tracer 先后创建两个段，中间没有外层段")
        print("外层 local_tracing 的 with 只准备工具，没有创建父 span。")
        print("notice_job 已结束；当前没有父 span，第一段因此开启一条新 trace。")
        with tracer.start_as_current_span(
            "standalone_first", record_exception=False, set_status_on_exception=False
        ):
            print("执行第一份独立工作。")
        print("第一段已退出，当前仍没有父 span；第二段会开启另一条 trace。")
        with tracer.start_as_current_span(
            "standalone_second", record_exception=False, set_status_on_exception=False
        ):
            print("执行第二份独立工作。")
        print("两段都来自同一个 tracer；退出后看实际 trace_id 与直接上级。")

    summary = json.loads((run_dir / "trace_summary.json").read_text(encoding="utf-8"))
    by_name = {row["name"]: row for row in summary["rows"]}
    job = by_name["notice_job"]
    for name in ["read_rule", "render_card"]:
        assert by_name[name]["trace_id"] == job["trace_id"]
        assert by_name[name]["parent_span_id"] == job["span_id"]
    for name in ["notice_job", "standalone_first", "standalone_second"]:
        assert by_name[name]["parent_span_id"] is None
    assert summary["span_count"] == 5 and summary["trace_count"] == 3
    assert summary["root_count"] == 3
    assert len({row["span_id"] for row in summary["rows"]}) == 5
    print("\n五、核对与边界")
    print("实际父子关系、三条轨迹与五个不同的 span 编号已核对。")
    print("输出按结束顺序：子段会先于外层段结束，不表示子段先开始。")
    print(
        "每段毫秒数是 SDK 本轮实测，会变化；外层包含子段，不应把它们简单相加当总耗时。"
    )
    print("结束一个 span 后，tracer 仍能创建下一段；它们的生命周期不同。")
    print("这里的 trace_id 由 SDK 创建，不等于之前自己生成的业务 request_id。")
    print("后续可把 request_id 作为属性关联；本节尚未接旧 RAG、HTTP 或跨进程传播。")
    print(
        "otel_spans.json 保留 SDK 实际全字段，trace_summary.json 只摘出本节关联字段。"
    )


def main() -> None:
    """自动保存本轮输出、配置和来源，失败也保留日志。"""
    run_logged(
        "trace_span_demo",
        demonstrate,
        {"model_calls": 0, "export": "in_memory_then_local_json", "otel_sdk": "1.45.2"},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day53/outputs",
        origin_env="DAY53_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
