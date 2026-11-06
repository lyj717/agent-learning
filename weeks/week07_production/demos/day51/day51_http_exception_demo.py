"""Day51A：独立认识 HTTPException 怎样由框架变成带错误状态码的响应。

对照返回一个含 detail 的普通字典，避免把 JSON 内容误当 HTTP 状态。
"""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def demonstrate_http_exception(run_dir: Path) -> None:
    """比较相同说明文字放在普通返回值和 HTTPException 中的响应。"""
    print("问答服务有时需要主动拒绝请求；本例只教怎样明确表达 HTTP 失败。")
    print("学完能在练习 B 区分框架校验失败与业务规则拒绝。")
    print("\n一、是什么：HTTPException 是 FastAPI 能识别并转换成 HTTP 响应的异常。")
    print("为什么：返回一个写着错误的字典，默认状态码仍可能是 200。")
    print("场景：通知尚未发布，接口需要返回 404 和公开说明。")
    print("\n二、导入与签名")
    print("from fastapi import HTTPException")
    print("HTTPException(status_code, detail=None, headers=None) 构造异常对象。")
    print("status_code 必填整数；本例明确传 404；detail 可选，本例传公开字符串。")
    print(
        "headers 可选，本例不传；用 raise 抛出，框架返回对应状态码和 {'detail':说明}。"
    )
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    def return_notice() -> dict:
        """普通返回字典，未指定特殊响应状态码。"""
        return {"detail": "通知尚未发布"}

    def reject_notice() -> dict:
        """主动以公开 404 响应结束本次处理。"""
        print("  【进入路由函数，随后抛 HTTPException】")
        # HTTPException：status_code 选 HTTP 状态，detail 是允许公开的响应说明。
        raise HTTPException(status_code=404, detail="通知尚未发布")

    app.add_api_route("/plain-notice", endpoint=return_notice, methods=["GET"])
    app.add_api_route("/missing-notice", endpoint=reject_notice, methods=["GET"])
    print("\n三、对照输出")
    with TestClient(app) as client:
        plain = client.get("/plain-notice")
        rejected = client.get("/missing-notice")
    print("普通 return 字典：", plain.status_code, plain.json(), "；期望 200。")
    print(
        "raise HTTPException：", rejected.status_code, rejected.json(), "；期望 404。"
    )
    print("\n四、注意什么")
    print("两份响应体文字相同，状态码不同；客户端要同时看外层状态和正文。")
    print("HTTPException 抛出后，当前函数正常返回路径停止，由框架生成错误响应。")
    print("不要把内部异常原文或密钥直接放进 detail，沿用 Day50 的日志/公开信息边界。")
    print("本次只解释业务主动拒绝；请求体不合格的 422 已在上一份独立演示说明。")
    print("本轮留证目录：", run_dir)


def main() -> None:
    """保存本次 HTTP 错误表达对照。"""
    run_logged(
        "http_exception_demo",
        demonstrate_http_exception,
        {"transport": "testclient_in_process", "model_calls": 0},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY51_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
