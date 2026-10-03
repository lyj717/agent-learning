"""第 6 条要求：至少一个 pytest 测试。

测的是 llm.py 里的**纯逻辑**——拼请求这种不发网络、不打印的函数。
（流式那部分要真调 API，花钱又慢，不适合放在单元测试里。）

跑法（要先 cd 到 chat_cli 目录，原因见 ../pytest.ini 里的注释）：
    cd weeks\\week00_python\\chat_cli
    ..\\..\\..\\.venv\\Scripts\\python.exe -m pytest -v

要写这三个测试：
    1. 只有问题时，messages 里应该只有一条 role="user"
    2. 传了 system_prompt 时，它应该排在第一条，用户那条排第二
    3. 显式传 model 时，请求里用的就是传进来的那个（而不是环境变量里的）

提示：
    - 测试函数的断言用 assert，比如 assert result.model == "deepseek-chat"
    - 想比较整个对象也行：assert request.messages == [Message(role=..., content=...)]
    - 环境变量类的东西别依赖机器状态，测试里显式传参最稳
"""

from llm import Message, build_request


def test_build_request_default_messages():
    """只有问题时：messages 应该只有一条用户消息。"""
    request = build_request("你好")
    assert request.messages == [Message(role="user", content="你好")]


def test_build_request_with_system_prompt():
    """传了 system_prompt 时：它排第一，用户消息排第二。"""
    request = build_request("你好", system_prompt="简洁点")
    assert request.messages[0] == Message(role="system", content="简洁点")


def test_build_request_uses_given_model():
    """显式传的 model 应该原样出现在请求里。"""
    request = build_request("你好", model="deepseek-chat")
    assert request.messages == [
        Message(role="user", content="你好", model="deepseek-chat")
    ]
