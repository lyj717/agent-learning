"""Day53 B2：区分记录结束、成功或失败标记、Python 异常传出。

直接演示固定片段的状态，不预先实现接收外部 action 的练习函数。
本例自带本地 SDK 和人工业务，不依赖另一份演示的结果。
"""

import json
import sys
from pathlib import Path

# Status 表示状态对象，StatusCode 提供 UNSET、OK、ERROR 三个状态值。
from opentelemetry.trace import Status, StatusCode

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day53.day53_trace_runtime import local_tracing


def demonstrate(run_dir: Path) -> None:
    """对照默认状态、显式成功和安全失败，查看实际 SDK 字段。"""
    print("阶段目标：从一次失败请求找到具体工作段。本节学习给段标状态。")
    print("学完能区分记录结束与处理成功；练习会用这些 API 标记外部动作的执行结果。")
    print(
        "\n一、是什么：status 是 span 的结果标记，不是 Python 的返回值或 HTTP 状态码。"
    )
    print("为什么需要：一段执行完了，排查者还需要知道这次处理是否失败。")
    print("场景：先对照未标状态和显式成功，再让一段固定数据转换抛出 ValueError。")
    print("\n二、导入与接口")
    print("from opentelemetry.trace import Status, StatusCode")
    print(
        "Status(StatusCode.OK)：构造显式成功的状态；ERROR 表示失败，UNSET 是默认未标。"
    )
    print("span.set_status(Status(...))：传入状态对象，修改该 span，返回 None。")
    print("Status 还可选传 description，但本课不传，避免把异常消息保存进去。")
    print("UNSET 不等于失败；本课关闭了自动异常标记，因此也不能靠 UNSET 证明业务成功。")
    print("只在确定结果时设置 OK 或 ERROR；不要开始工作就先标 OK。")
    print("状态在段结束前设置；设置状态不会结束 span，也不会让程序抛出或吞掉异常。")

    with local_tracing(run_dir) as tracer:
        print("\n三、对照：两个正常结束的段，一个未标，另一个显式标 OK")
        with tracer.start_as_current_span(
            "default_result", record_exception=False, set_status_on_exception=False
        ):
            print("默认段：执行普通工作，不设置结果标记。")
        with tracer.start_as_current_span(
            "marked_result", record_exception=False, set_status_on_exception=False
        ) as marked_span:
            # set_status(状态对象)：记录结果；StatusCode.OK 是显式成功。
            returned = marked_span.set_status(Status(StatusCode.OK))
            print("显式成功段：set_status 返回", returned)

        print("\n四、失败：原异常要传给调用方，span 只保存异常类型")
        print("这是人工失败，不访问服务商；消息里即使有私密文字，也不写入 span。")
        original = ValueError("人工数据转换失败；这里只演示异常消息不能自动入记录")
        try:
            with tracer.start_as_current_span(
                "convert_count", record_exception=False, set_status_on_exception=False
            ) as failed_span:
                try:
                    raise original
                except Exception as error:
                    failed_span.set_attribute("error_type", type(error).__name__)
                    failed_span.set_status(Status(StatusCode.ERROR))
                    print("段内：已标 ERROR，接着用裸 raise 把当前原异常继续抛出。")
                    raise
        except ValueError as received:
            print("段外调用方：收到的是原异常对象：", received is original)
            print("段外调用方：失败段仍在记录：", failed_span.is_recording())

    raw = json.loads((run_dir / "otel_spans.json").read_text(encoding="utf-8"))
    by_name = {row["name"]: row for row in raw}
    for row in raw:
        print(
            f"实际 {row['name']}：status={row['status']['status_code']}；"
            f"error_type={row['attributes'].get('error_type')}；events={len(row['events'])}"
        )
    assert by_name["default_result"]["status"]["status_code"] == "UNSET"
    assert by_name["marked_result"]["status"]["status_code"] == "OK"
    failure = by_name["convert_count"]
    assert failure["status"]["status_code"] == "ERROR"
    assert failure["attributes"] == {"error_type": "ValueError"}
    assert not failure["events"] and not failure["status"].get("description")
    print("\n五、注意：本课用字段白名单控制记录内容。")
    print("两项异常开关 False 会关闭自动异常事件和自动状态描述，但不会阻止异常传出。")
    print("不要额外调用 record_exception(error)，它会记录异常消息和堆栈。")
    print("不用 str(error) 作属性或状态描述，也不把错误改成一个假成功的返回值。")
    print(
        "业务状态如 no_context 与追踪状态 OK/ERROR 是两套概念；正常返回也可能没有正文。"
    )
    print("三段都已结束，但结果标记不同；详细 status、attributes、events 已保存。")


def main() -> None:
    """保存本次演示的原始 SDK 记录与日志。"""
    run_logged(
        "span_status_demo",
        demonstrate,
        {
            "model_calls": 0,
            "otel_sdk": "1.45.2",
            "automatic_exception_recording": False,
        },
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY53_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
