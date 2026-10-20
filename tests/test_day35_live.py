"""用真实 SDK 与内存 HTTP 服务验证 Day 35 接缝；不读取凭据或联网。"""

import json
from copy import deepcopy

import httpx
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from openai import OpenAI

from weeks.week04_frameworks.demos.day35 import day35_live_model as live
from weeks.week04_frameworks.demos.day35 import day35_support as support
from weeks.week04_frameworks.exercises import day34_graph_exercises as core
from weeks.week04_frameworks.exercises import (
    day35_persistent_review_exercises as lesson,
)


def _install_mock_client(monkeypatch, handler) -> None:
    """只替换配置和 HTTP 传输；保留 SDK 的请求编码、响应解析及异常包装。"""
    monkeypatch.setattr(
        live,
        "_load_settings",
        lambda: (
            "fixed-test-key-with-no-real-value",
            "https://example.invalid/v1",
            "test-model",
        ),
    )

    def make_client(**kwargs) -> OpenAI:
        assert kwargs["max_retries"] == 0
        return OpenAI(
            **kwargs,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )

    monkeypatch.setattr(live, "OpenAI", make_client)


def _response(message: dict, *, usage: dict | None) -> httpx.Response:
    """构造服务端响应，让真实 SDK 将原生 JSON 解包成 ChatCompletion。"""
    return httpx.Response(
        200,
        json={
            "id": "test-completion",
            "object": "chat.completion",
            "created": 0,
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": "tool_calls"
                    if message.get("tool_calls")
                    else "stop",
                }
            ],
            "usage": usage,
        },
    )


def _tool_call(name: str, arguments: dict, call_id: str) -> dict:
    """只制作服务器的点单，执行仍经过学员的工具节点。"""
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }
        ],
    }


def _initial(tmp_path, quote_id: str) -> dict:
    """准备真实入口的图状态，所有写入都落在 pytest 专属临时目录。"""
    state = core.make_initial(
        "蓝湾便签买 8 本多少钱？请说明单价出处。",
        scenario="live",
        overrides={"call_limit_seconds": 30.0, "token_limit": 20000},
    )
    state.update(
        quote_id=quote_id,
        approved=False,
        action_count=0,
        outbox_db=str(tmp_path / "outbox.sqlite"),
    )
    return state


def test_sdk_messages_round_trip_and_reopened_review_never_requests(
    monkeypatch, tmp_path
) -> None:
    """核对两轮点单的完整历史；重开图后的批准、拒绝与重复恢复都不发请求。"""
    requests = []

    def server(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        messages = body["messages"]
        assert messages[0] == {"role": "system", "content": live.SYSTEM_MESSAGE}
        assert {tool["function"]["name"] for tool in body["tools"]} == {
            "search_notes",
            "calculator",
        }
        assistant_count = sum(item["role"] == "assistant" for item in messages)
        if assistant_count == 0:
            assert [item["role"] for item in messages] == ["system", "user"]
            reply = _tool_call(
                "search_notes", {"keyword": "蓝湾便签", "limit": 2}, "sdk-search"
            )
        elif assistant_count == 1:
            assert [item["role"] for item in messages] == [
                "system",
                "user",
                "assistant",
                "tool",
            ]
            assert messages[2]["tool_calls"][0]["id"] == "sdk-search"
            assert messages[3]["tool_call_id"] == "sdk-search"
            hits = json.loads(messages[3]["content"])
            assert any(
                hit["source"] == "catalog.txt"
                and hit["line"] == 2
                and "11" in hit["text"]
                for hit in hits
            )
            reply = _tool_call("calculator", {"expression": "11 * 8"}, "sdk-calc")
        else:
            assert assistant_count == 2
            assert [item["role"] for item in messages] == [
                "system",
                "user",
                "assistant",
                "tool",
                "assistant",
                "tool",
            ]
            assert messages[4]["tool_calls"][0]["id"] == "sdk-calc"
            assert messages[5]["tool_call_id"] == "sdk-calc"
            assert json.loads(messages[5]["content"]) == 88
            reply = {
                "role": "assistant",
                "content": "8 本共 88 元，单价来源 catalog.txt:2。",
            }
        return _response(
            reply,
            usage={
                "prompt_tokens": 100 + assistant_count,
                "completion_tokens": 10,
                "total_tokens": 110 + assistant_count,
            },
        )

    _install_mock_client(monkeypatch, server)
    configs = {
        "allow": {"configurable": {"thread_id": "sdk-allow"}},
        "deny": {"configurable": {"thread_id": "sdk-deny"}},
    }
    db_path = str(tmp_path / "checkpoints.sqlite")
    before = {}
    with SqliteSaver.from_conn_string(db_path) as saver:
        graph = lesson.build_quote_graph(saver)
        for decision, config in configs.items():
            graph.invoke(_initial(tmp_path, f"quote-{decision}"), config=config)
            snapshot = graph.get_state(config)
            assert snapshot.next == ("review",)
            assert snapshot.values["steps"] == 3
            assert snapshot.values["usages"] == [
                {"prompt_tokens": 100 + index, "completion_tokens": 10}
                for index in range(3)
            ]
            assert snapshot.values["action_count"] == 0
            before[decision] = deepcopy(snapshot.values)
    assert len(requests) == 6

    def forbidden_client(**kwargs) -> None:
        raise AssertionError("恢复审核或重复恢复不应创建模型客户端")

    monkeypatch.setattr(live, "OpenAI", forbidden_client)
    with SqliteSaver.from_conn_string(db_path) as saver:
        graph = lesson.build_quote_graph(saver)
        for decision, config in configs.items():
            graph.invoke(Command(resume=decision), config=config)
            snapshot = graph.get_state(config)
            assert snapshot.next == ()
            assert snapshot.values["approved"] is (decision == "allow")
            assert snapshot.values["action_count"] == int(decision == "allow")
            for field in ("messages", "trace", "steps", "usages", "answer"):
                assert snapshot.values[field] == before[decision][field]
        graph.invoke(Command(resume="allow"), config=configs["allow"])
        assert support.outbox_count(tmp_path / "outbox.sqlite", "quote-allow") == 1
        assert support.outbox_count(tmp_path / "outbox.sqlite", "quote-deny") == 0
    assert len(requests) == 6


def test_sdk_timeout_records_attempt_without_inventing_usage(
    monkeypatch, tmp_path
) -> None:
    """实际 SDK 的 HTTP 超时经适配器进入旧节点的 call_timeout 分支。"""
    attempts = []

    def server(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        raise httpx.ReadTimeout("mock timeout", request=request)

    _install_mock_client(monkeypatch, server)
    state = _initial(tmp_path, "timeout-quote")
    state["steps"] = 1
    state["usages"] = [{"prompt_tokens": 7, "completion_tokens": 1}]
    original = deepcopy(state)
    update = support.model_node(state)
    assert len(attempts) == 1
    assert update["steps"] == 2
    assert update["stop_reason"] == "call_timeout"
    assert update["usages"] == original["usages"]
    assert update["messages"] == []
    assert update["trace"][-2:] == [
        {"step": 2, "event": "request", "finish_reason": None, "usage": None},
        {"step": 2, "event": "stop", "reason": "call_timeout"},
    ]
    assert state == original


def test_response_without_usage_still_fills_tool_before_stopping(
    monkeypatch, tmp_path
) -> None:
    """收到无 usage 的真实形状响应时记 None，回填本轮工具后以 usage_unknown 停止。"""
    requests = []

    def server(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert len(requests) == 1
        return _response(
            _tool_call("calculator", {"expression": "11 * 8"}, "no-usage-call"),
            usage=None,
        )

    _install_mock_client(monkeypatch, server)
    config = {"configurable": {"thread_id": "missing-usage"}}
    with SqliteSaver.from_conn_string(str(tmp_path / "no-usage.sqlite")) as saver:
        graph = lesson.build_quote_graph(saver)
        graph.invoke(_initial(tmp_path, "no-usage-quote"), config=config)
        snapshot = graph.get_state(config)
    assert snapshot.next == ()
    assert snapshot.values["steps"] == 1
    assert snapshot.values["usages"] == [None]
    assert snapshot.values["stop_reason"] == "usage_unknown"
    assert [message.type for message in snapshot.values["messages"]] == [
        "human",
        "ai",
        "tool",
    ]
    assert snapshot.values["messages"][-1].tool_call_id == "no-usage-call"
    assert snapshot.values["trace"][-2]["event"] == "tool"
    assert snapshot.values["trace"][-1]["reason"] == "usage_unknown"
    assert not (tmp_path / "outbox.sqlite").exists()
