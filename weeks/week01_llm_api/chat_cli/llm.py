"""和模型打交道的那一层：发请求，把回复和用量一起拿回来。

这一层不碰命令行、也不打印任何东西，所以好测、也好替换。
Day 10 先做**非流式**——一次拿回完整回答；流式打印是 Day 11 的事。
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

# 这个文件在 weeks/week01_llm_api/chat_cli/ 里，往上三层才是仓库根目录
ROOT = Path(__file__).resolve().parents[3]
MIN_KEY_LEN = 20

# 输出上限。为什么不是几十：当前模型是推理模型，思考也算在输出里，
# 给太小它会「想」到一半就被截断，正文为空（Day 8 踩过）。
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
    """发一次请求（非流式），返回（回答文本, usage 用量对象）。

    messages   要发过去的一整串对话（system + 历史 + 这次的问题）
    model      不传就用 .env 里的 LLM_MODEL
    temperature 不传就用服务商默认值
    usage      里带着 prompt_tokens / completion_tokens，是算钱和统计的原始数据
    """
    # OpenAI(...)：和模型通信的客户端，参数是密钥与服务商地址
    client = OpenAI(
        api_key=require_api_key(),
        base_url=os.environ.get("LLM_BASE_URL"),
    )
    kwargs: dict[str, Any] = {
        "model": model or os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    # chat.completions.create(...)：真正把请求发出去
    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content or ""
    return text.strip(), response.usage
