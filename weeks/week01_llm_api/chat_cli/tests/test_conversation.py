"""验收测试：对话历史这一层。跑红了就是还没写对。

跑法（要先 cd 到 chat_cli 目录）：
    cd weeks\\week01_llm_api\\chat_cli
    ..\\..\\..\\.venv\\Scripts\\python.exe -m pytest -v
"""

from conversation import Conversation


def test_no_system_starts_empty():
    """不给 system 时，一开始没有任何消息。"""
    conversation = Conversation()
    assert conversation.messages() == []
    assert conversation.turns() == 0


def test_system_comes_first():
    """给了 system，它必须排在第一条。"""
    conversation = Conversation("你只说一句话")
    assert conversation.messages() == [{"role": "system", "content": "你只说一句话"}]


def test_turns_keep_time_order():
    """一轮问答要按 user、assistant 的顺序存进去。"""
    conversation = Conversation("你只说一句话")
    conversation.add_user("杭州多少度")
    conversation.add_assistant("22 度")
    assert conversation.messages() == [
        {"role": "system", "content": "你只说一句话"},
        {"role": "user", "content": "杭州多少度"},
        {"role": "assistant", "content": "22 度"},
    ]
    assert conversation.turns() == 1


def test_clear_keeps_system_but_drops_history():
    """clear 之后历史清空，但 system 人设还在。"""
    conversation = Conversation("你只说一句话")
    conversation.add_user("杭州多少度")
    conversation.add_assistant("22 度")
    conversation.clear()
    assert conversation.messages() == [{"role": "system", "content": "你只说一句话"}]
    assert conversation.turns() == 0


def test_messages_returns_a_copy():
    """messages() 交出来的列表被改，不能动到对话内部的状态。"""
    conversation = Conversation()
    conversation.add_user("你好")
    handed_out = conversation.messages()
    handed_out.append({"role": "user", "content": "偷偷加一条"})
    assert conversation.messages() == [{"role": "user", "content": "你好"}]


def test_trim_keeps_system_and_recent_turns():
    """裁到最近 2 轮：system 留着，丢掉的条数报对。"""
    conversation = Conversation("你只说一句话")
    for number in range(1, 6):
        conversation.add_user(f"问 {number}")
        conversation.add_assistant(f"答 {number}")
    dropped = conversation.trim(2)
    assert dropped == 6
    assert conversation.turns() == 2
    messages = conversation.messages()
    assert messages[0] == {"role": "system", "content": "你只说一句话"}
    assert messages[1] == {"role": "user", "content": "问 4"}


def test_trim_does_nothing_when_history_is_short():
    """要留的轮数比现有的还多时，一条都不该丢。"""
    conversation = Conversation()
    conversation.add_user("你好")
    conversation.add_assistant("你好呀")
    assert conversation.trim(5) == 0
    assert conversation.turns() == 1
