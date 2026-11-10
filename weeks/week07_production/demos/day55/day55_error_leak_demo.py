"""Day55 A1：对外错误只给公开字段，内部异常不泄露。

从 demonstrate_async 读起。本例用人工异常，不访问模型、HTTP 或真实密钥。
它只回答一个问题：内部异常怎样变成对外的错误响应，哪些内容绝不能出去。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

# 人工标记，只用于演示“泄露”长什么样；不是真实密钥。
FAKE_SECRET = "sk-live-DEMO-123456"
FAKE_PATH = "/srv/app/knowledge/private.md"


def naive_response(exc: BaseException) -> dict[str, str]:
    """错误示范：把异常消息原样交给客户端。"""
    return {"detail": str(exc)}


def safe_response(exc: BaseException, request_id: str) -> tuple[int, dict[str, str]]:
    """正确形状：按异常类别给状态码和固定文案，只带公开编号。"""
    if isinstance(exc, TimeoutError):
        return 504, {"detail": "上游超时", "request_id": request_id}
    if isinstance(exc, ConnectionError):
        return 502, {"detail": "上游连接失败", "request_id": request_id}
    if isinstance(exc, ValueError):
        return 400, {"detail": "请求不合法", "request_id": request_id}
    return 500, {"detail": "内部错误", "request_id": request_id}


def demonstrate(run_dir: Path) -> None:
    """对比泄露版和安全版的响应，打印映射表与边界。"""
    print(
        "Week07 要把 Agent 变成服务。服务失败时，客户端能看到什么、看不到什么，是本节的内容。"
    )
    print("本节只回答：内部异常怎样翻译成对外错误，以及哪些东西绝不能跟着出去。")

    print("\n一、错误示范：把异常消息原样返回")
    error = RuntimeError(f"读取 {FAKE_PATH} 失败，key={FAKE_SECRET}")
    print(f"  内部异常类型：{type(error).__name__}")
    print(f"  直接返回：{naive_response(error)}")
    print("  文件名、路径、密钥片段全泄露了；客户端还知道了内部实现细节。")

    print("\n二、正确形状：按类别映射，只给公开字段")
    mapping = [
        (TimeoutError("超时"), 504, "上游超时"),
        (ConnectionError("连不上"), 502, "上游连接失败"),
        (ValueError("参数不对"), 400, "请求不合法"),
        (RuntimeError("内部故障"), 500, "内部错误"),
    ]
    for exc, status, detail in mapping:
        code, body = safe_response(exc, "req-demo-001")
        print(f"  {type(exc).__name__:<16} → {code} {body}")

    print("\n三、验证泄露：把敏感标记放进各种异常，安全版都不该带出去")
    probes = [
        RuntimeError(f"key={FAKE_SECRET}"),
        TimeoutError(f"读取 {FAKE_PATH} 超时"),
        ConnectionError(f"连接失败 {FAKE_SECRET}"),
    ]
    leaks = []
    for exc in probes:
        _, body = safe_response(exc, "req-demo-002")
        text = json.dumps(body, ensure_ascii=False)
        if FAKE_SECRET in text or FAKE_PATH in text:
            leaks.append(text)
        print(f"  {type(exc).__name__} → {body}")
    print(f"  泄露检查：{'发现泄露' if leaks else '没有泄露'}")

    print("\n四、映射与边界")
    print("  504 上游超时、502 上游连接失败、400 请求不合法、其余 500 内部错误。")
    print("  502/504 表示“我们依赖的上游出问题”，不是我们自己算错；500 是未预期故障。")
    print("  request_id 保留给客户端报障与日志对账，它本身不泄露业务内容。")
    print(
        "  日志里可以记 request_id 和异常类型，但不要把消息、密钥、完整路径原样写进去。"
    )
    print("  本节只做失败响应；提示词注入、工具越权、输出过滤不在这一题里解决。")

    assert FAKE_SECRET not in json.dumps(safe_response(error, "req-demo-001"))
    assert FAKE_PATH not in json.dumps(safe_response(error, "req-demo-001"))
    (run_dir / "error_leak.json").write_text(
        json.dumps(
            {
                "naive": naive_response(error),
                "safe": safe_response(error, "req-demo-001"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """保存本轮讲解、两种响应与来源。"""
    run_logged(
        "error_leak_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY55_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
