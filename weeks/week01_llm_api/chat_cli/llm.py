"""和模型打交道的那一层：发请求，把回复和用量一起拿回来。

这一层不碰命令行、也不打印任何东西，所以好测、也好替换。
Day 10 先做**非流式**——一次拿回完整回答；流式打印是 Day 11 的事。
"""

import os
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import openai
from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    BadRequestError,
    InternalServerError,
    OpenAI,
    RateLimitError,
    UnprocessableEntityError,
)

# 这个文件在 weeks/week01_llm_api/chat_cli/ 里，往上三层才是仓库根目录
ROOT = Path(__file__).resolve().parents[3]
MIN_KEY_LEN = 20

DEFAULT_MAX_TOKENS = 2048

# 一次请求最多等多少秒。不设的话，网络卡住时请求会一直挂着，
# 用户看不到任何反馈（而且那时候连 Ctrl+C 都要等数据回来才响应）
TIMEOUT_SECONDS = 30

# 值得重试的错误：连不上、超时、限流（429）、服务端 5xx。
# 其他错误（401 密钥错、400/422 参数错）重试一百次也一样，纯浪费时间和额度。
RETRYABLE_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)

# 请求本身有问题的错误：重试也没用，而且多半是「输入太长」。
# 单独拎出来，是为了让上层能给一句更具体的提示，而不是笼统地说「出错了」
REQUEST_ERRORS = (BadRequestError, UnprocessableEntityError)

# 给上层兜底用的：openai 所有错误的基类。
# 上层按这个顺序接：RETRYABLE_ERRORS → REQUEST_ERRORS → MODEL_ERRORS
MODEL_ERRORS = (APIError,)


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


def _make_client() -> OpenAI:
    """建一个客户端，两个函数共用（原来 chat 和 stream_chat 各写了一遍）"""
    return OpenAI(
        api_key=require_api_key(),
        base_url=os.environ.get("LLM_BASE_URL"),
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
    )


def retry(
    make_request, *, attempts: int = 3, base_delay: float = 1.0, sleep=time.sleep
):
    """把「一次请求」包成「失败会自动重试」的版本，成功就把结果原样返回。"""
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return make_request()
        except RETRYABLE_ERRORS as error:
            last_error = error
            if attempt < attempts:
                sleep(base_delay * (2 ** (attempt - 1)))
        except openai.APIError:
            raise
    raise last_error


def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> tuple[str, Any]:
    """发一次请求（非流式），返回（回答文本, usage 用量对象）"""
    client = _make_client()
    fields = {
        "model": model or os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        fields["temperature"] = temperature
    response = retry(lambda: client.chat.completions.create(**fields))
    return (response.choices[0].message.content or "").strip(), response.usage


def stream_chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    usage_box: list | None = None,
) -> Iterator[str]:
    """边收边给：每收到一块正文就 yield出去"""
    client = _make_client()
    fields = {
        "model": model or os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if temperature is not None:
        fields["temperature"] = temperature
    stream = retry(lambda: client.chat.completions.create(**fields))
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        piece = delta.content
        if piece:
            yield piece
        if chunk.usage is not None and usage_box is not None:
            usage_box.append(chunk.usage)
