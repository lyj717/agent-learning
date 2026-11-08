"""Day53 B1：为一个 span 追加可公开的属性；不包含阶段包装器的参考实现。

从 demonstrate 读起；本例自己配置本地 SDK，不依赖 A 的运行结果。
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
    """先给公开标签，再追加实际数量，核对保存后的字段。"""
    print("阶段目标：为服务留下可查的 trace。本节给某一段补充可公开的标签和数量。")
    print("学完能把业务 request_id、阶段名等写到属性中，后面用于定位一条失败记录。")
    print("\n一、是什么：attributes 是 span 上的键值字段，作用类似一张记录卡的栏目。")
    print("为什么需要：只有编号还不知道它对应哪个业务请求、这一段处理了多少资料。")
    print("场景：人工资料选择器从两个编号中选出一个，只记录数量，不记录资料正文。")
    print("\n二、名字从哪里来、怎样调用")
    print("local_tracing 是已提供的运行环境，with 的 as tracer 接到创建 span 的工具。")
    print("创建 span 时可选 attributes={字符串键: 值}；不传时就是没有这些自定义属性。")
    print(
        "span.set_attribute(key, value)：必填字段名和字段值，修改当前对象，返回 None。"
    )
    print("本课只用 str/int/bool 三种基础值；每个属性只记一项定位信息。")
    print("同一个 key 再设置会更新该字段；这些操作都应在 span 结束前完成。")
    print("\n三、代码与实际值：先记请求编号和候选数量，再补选择数量")
    with local_tracing(run_dir) as tracer:
        print("运行环境已提供 tracer；下面才开始创建业务 span。")
        # attributes：创建时附上的自定义键值；字段名不会自动影响 trace_id 或父子关系。
        with tracer.start_as_current_span(
            "choose_notice",
            attributes={"request_id": "notice-demo-01", "candidate_count": 2},
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            candidates = ["rule-2", "rule-9"]
            selected = candidates[:1]
            # set_attribute(字段名, 值)：给本段追加一个属性，返回 None。
            returned = span.set_attribute("selected_count", len(selected))
            span.set_attribute("used_fallback", False)
            print("输入候选编号：", candidates, "；实际选中：", selected)
            print(
                "set_attribute 返回：", returned, "；它没有返回新的 span 或业务结果。"
            )

    raw = json.loads((run_dir / "otel_spans.json").read_text(encoding="utf-8"))
    attributes = raw[0]["attributes"]
    for key in ["request_id", "candidate_count", "selected_count", "used_fallback"]:
        print(f"实际 attributes[{key!r}] = {attributes[key]!r}")
    assert attributes == {
        "request_id": "notice-demo-01",
        "candidate_count": 2,
        "selected_count": 1,
        "used_fallback": False,
    }
    print("\n四、注意边界")
    print("request_id 是你附上的业务字段；trace_id 是 SDK 的轨迹编号，二者各有用途。")
    print("写相同 request_id 不会自动合并两条 trace，也不会改变直接上级。")
    print(
        "只记录定位所需的公开字段；不要把问题正文、答案、密钥或完整返回字典塞进属性。"
    )
    print(
        "本轮使用人工数据、真实本地 SDK，模型调用 0 次；实际属性已写入 otel_spans.json。"
    )


def main() -> None:
    """为本次演示保存独立日志与来源。"""
    run_logged(
        "span_attributes_demo",
        demonstrate,
        {"model_calls": 0, "otel_sdk": "1.45.2"},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY53_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
