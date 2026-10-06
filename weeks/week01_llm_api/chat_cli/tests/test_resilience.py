"""验收测试：Day 12 的三条标准——断网、限流、超长输入都不崩溃。

外加 retry() 的行为：指数退避、不值得重试的错误立刻抛。

跑法（要先 cd 到 chat_cli 目录）：
    cd weeks\\week01_llm_api\\chat_cli
    ..\\..\\..\\.venv\\Scripts\\python.exe -m pytest -v
"""

import io
import sys
from types import SimpleNamespace

import chat_cli
import httpx2
import llm
import openai
import pytest


def _request() -> httpx2.Request:
    """造一个「请求对象」——openai 的异常类要求带上它。"""
    return httpx2.Request("POST", "https://api.deepseek.com/chat/completions")


def connection_error() -> Exception:
    """断网：连不上。"""
    return openai.APIConnectionError(request=_request())


def rate_limit_error() -> Exception:
    """限流：429。"""
    return openai.RateLimitError(
        "rate limited", response=httpx2.Response(429, request=_request()), body=None
    )


def too_long_error() -> Exception:
    """超长输入：400（服务端嫌请求太大）。"""
    return openai.BadRequestError(
        "context length exceeded",
        response=httpx2.Response(400, request=_request()),
        body=None,
    )


@pytest.mark.parametrize(
    "make_error", [connection_error, rate_limit_error, too_long_error]
)
def test_cli_survives_model_failures(monkeypatch, capsys, make_error):
    """三种失败都不该让程序退出；而且失败的那条问句不能留在历史里。"""
    payloads: list[list[dict[str, str]]] = []

    def flaky_stream(messages, **kwargs):
        """第一句失败，后面成功——这样能看出「失败的那句有没有留在历史里」。"""
        payloads.append(messages)
        if len(payloads) == 1:
            raise make_error()
        yield "好的"
        box = kwargs.get("usage_box")
        if box is not None:
            box.append(SimpleNamespace(prompt_tokens=5, completion_tokens=5))

    monkeypatch.setattr(llm, "stream_chat", flaky_stream)
    monkeypatch.setattr(sys, "stdin", io.StringIO("第一句会失败\n第二句\n/exit\n"))

    code = chat_cli.main(["--system", "测试"])
    output = capsys.readouterr().out

    assert code == 0, "模型出错时主程序该正常返回，而不是抛异常退出"
    assert "Traceback" not in output, "不该把一整段报错栈甩给用户"
    assert "再见" in output, "出过错之后循环还该活着，能走到 /exit"
    assert len(payloads) == 2, "两次输入都该真的去请求"
    assert payloads[1] == [
        {"role": "system", "content": "测试"},
        {"role": "user", "content": "第二句"},
    ], "第一句失败了，不该留在历史里被第二句带着一起发"


def test_ctrl_c_exits_cleanly(monkeypatch, capsys):
    """按 Ctrl+C（KeyboardInterrupt）要干净退出，别甩 traceback。"""

    def working_stream(messages, **kwargs):
        yield "好的"
        box = kwargs.get("usage_box")
        if box is not None:
            box.append(SimpleNamespace(prompt_tokens=5, completion_tokens=5))

    calls = {"n": 0}

    def fake_input(prompt=""):
        calls["n"] += 1
        if calls["n"] == 1:
            return "你好"
        raise KeyboardInterrupt

    monkeypatch.setattr(llm, "stream_chat", working_stream)
    monkeypatch.setattr("builtins.input", fake_input)

    try:
        code = chat_cli.main([])
    except KeyboardInterrupt:
        pytest.fail("main 把 KeyboardInterrupt 放出来了：应该打印「再见」再干净退出")
    output = capsys.readouterr().out

    assert code == 0
    assert "Traceback" not in output
    assert "再见" in output


def test_retry_waits_and_then_succeeds():
    """前两次失败、第三次成功：等 1s、2s（允许加抖动，所以给一半的容差）。"""
    delays: list[float] = []
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise connection_error()
        return "成功"

    result = llm.retry(flaky, attempts=3, base_delay=1.0, sleep=delays.append)

    assert result == "成功"
    assert calls["n"] == 3
    assert len(delays) == 2
    assert 0.5 <= delays[0] <= 1.0
    assert 1.0 <= delays[1] <= 2.0


def test_retry_does_not_wait_for_hopeless_errors():
    """密钥错这类重试也没用：试一次就直接抛，一次都不等。"""
    delays: list[float] = []
    calls = {"n": 0}

    def hopeless():
        calls["n"] += 1
        raise openai.AuthenticationError(
            "bad key", response=httpx2.Response(401, request=_request()), body=None
        )

    with pytest.raises(openai.AuthenticationError):
        llm.retry(hopeless, attempts=3, base_delay=1.0, sleep=delays.append)
    assert calls["n"] == 1
    assert delays == []


def test_client_has_timeout_and_no_builtin_retries(monkeypatch):
    """客户端要带超时，并且关掉 SDK 自己的重试（否则两层叠起来是 9 次请求）。"""
    monkeypatch.setenv("LLM_API_KEY", "sk-test-" + "0" * 20)
    client = llm._make_client()
    assert client.max_retries == 0
    assert client.timeout is not None
