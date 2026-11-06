"""Day51A：独立认识 JSON 请求体怎样校验成 Pydantic 对象，再交给路由函数。

不实现问答或会话；本例只制作标签预览，展示 422 与业务函数执行的先后关系。
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


class LabelRequest(BaseModel):
    """本例请求体：严格字符串标签、严格整数份数，拒绝额外字段。"""

    # ConfigDict(extra="forbid")：配置模型拒绝未声明字段，沿用之前的严格校验。
    model_config = ConfigDict(extra="forbid")
    # Field：声明约束；strict=True 不接受靠类型转换才匹配的输入。
    label: str = Field(min_length=1, strict=True)
    copies: int = Field(default=1, ge=1, le=2, strict=True)


def demonstrate_body(run_dir: Path) -> None:
    """比较校验前被拒绝与进入路由函数的人工 JSON 请求。"""
    print("服务不能直接信任客户端的数据；本例为后续问答入口的请求校验准备。")
    print("学完能分清：JSON 字段、Pydantic 对象和路由函数参数分别是什么。")
    print("\n一、是什么：请求体是客户端提交的数据，FastAPI 可以先用模型校验它。")
    print("为什么：缺字段、类型或范围不对时，业务逻辑不应该继续处理。")
    print("场景：客户端提交 label 与 copies，服务返回标签预览。")
    print("\n二、签名和数据路径")
    print("导入 BaseModel、ConfigDict、Field，模型字段与旧 Pydantic 练习一致。")
    print(
        "preview_label(payload: LabelRequest)：payload 由 FastAPI 提供，不由你手动传。"
    )
    print("HTTP 请求体先校验成 LabelRequest 实例，再执行 preview_label(payload)。")
    print("JSON 顶层字段是 label/copies，不需要再包一个名为 payload 的字段。")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    calls: list[str] = []

    def preview_label(payload: LabelRequest) -> dict:
        """接收框架已校验的对象，返回预览字典。"""
        calls.append("preview_label")
        print("  【进入路由函数】payload 类型：", type(payload).__name__)
        return {"preview": payload.label * payload.copies, "copies": payload.copies}

    app.add_api_route("/labels", endpoint=preview_label, methods=["POST"])
    cases = [
        ("正常 JSON", {"label": "待归还", "copies": 2}, 200),
        ("省略可选字段 copies", {"label": "待归还"}, 200),
        ("copies 是字符串", {"label": "待归还", "copies": "2"}, 422),
        ("缺少必填 label", {"copies": 1}, 422),
        ("多出字段", {"label": "待归还", "debug": True}, 422),
        ("只有空格但长度大于零", {"label": "  "}, 200),
    ]
    print("\n三、逐组对照")
    with TestClient(app) as client:
        for label, payload, expected in cases:
            before = len(calls)
            print("\n案例：", label, "；发送的 JSON：", payload)
            # post(path, json=字典)：序列化 JSON 后交给应用，不直接把字典当函数参数。
            response = client.post("/labels", json=payload)
            body = response.json()
            print("状态码实际/期望：", response.status_code, "/", expected)
            print("本次进入路由函数的次数：", len(calls) - before)
            if response.status_code == 200:
                print("预览 repr：", repr(body["preview"]), "；份数：", body["copies"])
            else:
                first = body["detail"][0]
                print("首个错误位置：", first["loc"], "；错误类型：", first["type"])
    print("\n四、注意什么")
    print(
        "422 由框架在调用业务函数之前产生；不需要在路由里捕获 ValidationError 再拼响应。"
    )
    print("min_length=1 只检查字符数；两个空格也有长度，所以本例会进入路由。")
    print("是否允许只有空格是额外的业务规则，练习 B 需要你亲自处理。")
    print("这里 payload 是模型实例，取字段用 payload.label；客户端拿到的是 JSON 响应。")
    print("本轮留证目录：", run_dir)


def main() -> None:
    """保存本例请求体与路由执行次数的实际对照。"""
    run_logged(
        "body_demo",
        demonstrate_body,
        {"transport": "testclient_in_process", "model_calls": 0},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY51_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
