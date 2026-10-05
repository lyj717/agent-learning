"""和模型打交道的那一层：发请求，把回复和用量一起拿回来。

这一层不碰命令行、也不打印任何东西，所以好测、也好替换。
Day 10 先做**非流式**——一次拿回完整回答；流式打印是 Day 11 的事。
"""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

# 这个文件在 weeks/week01_llm_api/chat_cli/ 里，往上三层才是仓库根目录
ROOT = Path(__file__).resolve().parents[3]
MIN_KEY_LEN = 20

DEFAULT_MAX_TOKENS = 2048


def require_api_key(env_name: str = "LLM_API_KEY") -> str:
    """读出 API Key；读不到就抛异常，绝不返回一个假值。"""
    # load_dotenv(路径)：把一个 .env 文件里的 KEY=VALUE 读进环境变量
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get(env_name)
    if not api_key or len(api_key) < MIN_KEY_LEN:
        raise RuntimeError(
            f"缺少配置 {env_name}：请在仓库根目录复制 .env.example 为 .env 并填入真实值"
        )
    return api_key


def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> tuple[str, Any]:
    """发一次请求（非流式），返回（回答文本, usage 用量对象）"""
    client = OpenAI(api_key=require_api_key(), base_url=os.environ.get("LLM_BASE_URL"))
    fields = {
        "model": model or os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        fields["temperature"] = temperature
    response = client.chat.completions.create(**fields)
    return (response.choices[0].message.content or "").strip(), response.usage


def stream_chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    usage_box: list | None = None,
) -> Iterator[str]:
    """边收边给：每收到一块正文就 yield 出去。
    要做的（Week 00 你写过一版流式，这次多两件事）：
        1. 建客户端，和 chat() 里那行一样
        2. 组装字段，和 chat() 一样，再多加一个 `"stream": True`
        3. 逐块遍历 `client.chat.completions.create(**fields)`：
             · chunk.choices 可能是空列表——先 `if not chunk.choices: continue`
             · 取 `chunk.choices[0].delta.content`
             · 有内容就 yield；是 None 或空串就跳过
               （思考模式下一大片块的 content 都是 None，不跳过就会吐一堆空串）
        4. 如果用法方传了 usage_box（一个空列表），把最后那块上的 usage 塞进去：
               usage_box.append(chunk.usage)
    期望结果：
        box = []
        for piece in stream_chat(msgs, usage_box=box):
            print(piece, end="", flush=True)      # 打字机效果
        box[0].completion_tokens                  # 流结束之后拿到用量
    提示：
        - 官方文档：最后一个块上带着整次请求的 usage，不会单独发一个只含 usage 的块。
          实测也是——第 127 块上带着 usage，前面全是 None
        - 为什么 usage 用「传个列表进来」的写法：Python 里列表是引用传递，
          函数往里塞，调用方在外面能拿到。生成器没法 return 第二个值
        - 打印是调用方的事，这个函数只管 yield，别在这里 print
    """
    client = OpenAI(api_key=require_api_key(), base_url=os.environ.get("LLM_BASE_URL"))
    fields = {
        "model": model or os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if temperature is not None:
        fields["temperature"] = temperature
    for chunk in client.chat.completions.create(**fields):
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        piece = delta.content
        if piece:
            yield piece
        if chunk.usage is not None and usage_box is not None:
            usage_box.append(chunk.usage)
