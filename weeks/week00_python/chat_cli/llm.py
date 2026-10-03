"""和模型打交道的那一层：拼请求、发请求、把回复取出来。

为什么要单独放一个文件：这一层不碰命令行、也不打印任何东西，
只负责「把请求发出去、把回复拿回来」。这样它才好测——
第 6 条要求的那几个 pytest 测试，测的就是这里的纯逻辑。

要写的四个东西：
    require_api_key()  读密钥，读不到就大声报错（Day 5 第 2 题写过一模一样的）
    build_request()    把一个问题拼成完整的请求结构（纯逻辑，最好测）
    stream_chat()      发请求，把模型吐出来的字一个个 yield 出来
    chat()             非流式的版本（可以最后再做，测试不依赖它）
"""

import os
from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

MIN_KEY_LEN = 20
# 这个文件在 weeks/week00_python/chat_cli/ 里，往上四层才是仓库根目录
ROOT = Path(__file__).resolve().parents[3]


class Message(BaseModel):
    """一条消息。第 4 条要求：用 Pydantic 定义请求结构。"""

    role: str
    content: str


class ChatRequest(BaseModel):
    """一次请求的全部内容：用哪个模型、带哪几条消息、要不要流式。"""

    model: str
    messages: list[Message]
    stream: bool = True


def require_api_key(env_name: str = "LLM_API_KEY") -> str:
    """读出 API Key；读不到就抛异常，绝不返回一个假值。
    要做的：
        1. load_dotenv(ROOT / ".env")，把 .env 读进环境变量
        2. value = os.environ.get(env_name)
        3. 没有、或者明显太短（比如少于 20 个字符）就 raise RuntimeError，
           信息里写清缺的是哪个变量、该怎么办
        4. 正常就返回它
    期望结果：
        有值   -> 返回密钥字符串（注意：永远别把它打印出来）
        没值   -> 抛异常，信息能直接念给人听
    """
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get(env_name)
    if api_key is None or len(api_key) < MIN_KEY_LEN:
        raise RuntimeError(
            f"缺少配置 {env_name}：请在仓库根目录复制 .env.example 为 .env，并填入真实值"
            f"（当前长度 {len(api_key) if api_key else 0}，疑似没复制完整）"
        )
    return api_key


def build_request(
    question: str,
    *,
    model: str | None = None,
    system_prompt: str | None = None,
    stream: bool = True,
) -> ChatRequest:
    """把「用户问的一句话」拼成完整的请求结构。
    要做的：
        1. messages 至少要有用户那一条：Message(role="user", content=question)
        2. 如果传了 system_prompt，就在最前面插一条 role="system"
        3. model 没传的话，从环境变量 LLM_MODEL 取（取不到给个默认值）
        4. 返回 ChatRequest(model=..., messages=..., stream=...)

    期望结果（这就是测试要断言的东西）：
        build_request("你好").messages
            == [Message(role="user", content="你好")]
        build_request("你好", system_prompt="简洁点").messages[0].role == "system"
        build_request("你好", model="deepseek-chat").model == "deepseek-chat"

    提示：这个函数是纯逻辑——不发请求、不打印，所以最适合写测试。
         它是「参数拼装」那类可以脱离网络验证的代码。
    """
    messages: list[Message] = []
    if system_prompt is not None:
        messages.append(Message(role="system", content=system_prompt))
    messages.append(Message(role="user", content=question))

    if model is None:
        load_dotenv(ROOT / ".env")
        model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    return ChatRequest(model=model, messages=messages, stream=stream)


def stream_chat(request: ChatRequest) -> Iterator[str]:
    """发请求，把模型吐出来的字一个个 yield 出来。
    要做的：
        1. 用 require_api_key() 拿密钥，建客户端：
               client = OpenAI(api_key=..., base_url=os.environ.get("LLM_BASE_URL"))
        2. 发请求：
               stream = client.chat.completions.create(
                   model=request.model,
                   messages=[m.model_dump() for m in request.messages],
                   stream=True,
               )
           注意 model_dump()：把 Pydantic 对象变回普通字典，
           这正是接口要的形状——第 4 条要求用 Pydantic 的意义就在这。
        3. for chunk in stream: 取出 chunk.choices[0].delta.content
        4. 有内容就 yield 出去（空的那块要跳过，Day 6 学过为什么）
    期望结果：
        调用方这样用，就能看到打字机效果——
            for piece in stream_chat(request):
                print(piece, end="", flush=True)
    """
    client = OpenAI(api_key=require_api_key(), base_url=os.environ.get("LLM_BASE_URL"))
    stream = client.chat.completions.create(
        model=request.model,
        messages=[m.model_dump() for m in request.messages],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def chat(request: ChatRequest) -> str:
    """非流式版本：一次拿回完整回复。
    要做的：和上面几乎一样，只是不发 stream=True，
    然后 return response.choices[0].message.content。
    提示：这个是可选项，最后再做。它能让 --no-stream 那个开关有东西可用。
    """
    client = OpenAI(api_key=require_api_key(), base_url=os.environ.get("LLM_BASE_URL"))
    response = client.chat.completions.create(
        model=request.model,
        messages=[m.model_dump() for m in request.messages],
        stream=False,
    )
    return response.choices[0].message.content
