"""Week 02 共用的小工具层：建客户端、发一次 JSON 模式的请求。

Day 15 时这两件事写在练习文件里面；从 Day 16 起好几个文件都要用，
所以收到这里来，免得每个文件都抄一遍。这一层**什么也不打印、什么也不校验**——
解析、校验、重试都是上层的事，因为「失败了怎么办」只有上层知道。

用法（脚本和它放在同一个目录，直接 import 就行）：
    from llm_client import chat_json, make_client

在 PyCharm 里如果这两个名字被标红，是它没把本目录当源码根：
右键 week02_tools → Mark Directory as → Sources Root（运行不受影响）。
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

# 这个文件在 weeks/week02_tools/ 里，往上两层是仓库根目录
ROOT = Path(__file__).resolve().parents[2]

# 思考 token 和正文共用这个额度（Day 15 的坑二），所以别省
DEFAULT_MAX_TOKENS = 2048

# 一次请求最多等多少秒。不设的话网络卡住时请求会一直挂着（Day 12 的坑）
TIMEOUT_SECONDS = 60

# 密钥短于这个长度基本就是没填（防止把占位符当密钥用）
MIN_KEY_LEN = 20


def require_api_key(env_name: str = "LLM_API_KEY") -> str:
    """读出 API Key；读不到就抛异常，绝不返回一个假值。"""
    # load_dotenv(路径)：把一个 .env 文件里的 KEY=VALUE 读进环境变量。
    # 重复调用没有副作用，所以每个入口各读一次没关系
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get(env_name)
    if not api_key or len(api_key) < MIN_KEY_LEN:
        raise RuntimeError(
            f"缺少配置 {env_name}：请在仓库根目录复制 .env.example 为 .env 并填入真实值"
        )
    return api_key


def make_client() -> OpenAI:
    """建一个 openai 客户端：密钥和 base_url 读 .env，关掉 SDK 自带重试，带超时。"""
    return OpenAI(
        api_key=require_api_key(),
        base_url=os.environ.get("LLM_BASE_URL"),
        timeout=TIMEOUT_SECONDS,
        # 关掉 SDK 自带的 2 次重试，否则一次业务调用会悄悄变成好几次（Day 12 实测过）
        max_retries=0,
    )


def chat_json(
    messages: list[dict[str, str]],
    *,
    client: OpenAI | None = None,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> tuple[str, str]:
    """发一次请求（开了 JSON 模式），返回（原始文本, finish_reason）。
    messages 就是普通的消息列表：system 里必须出现「json」字样，
    否则服务商直接 400 拒收（Day 15 的坑一）。
    特意把**原始文本**原样返回，不在这里解析成 dict：
    解析失败、字段不对都属于「上层要处理的事」，
    而且报错时你想看到的正是那段原始文本。
    finish_reason 也一起给出来：它是 length 就说明输出被截断，
    这时候别去纠结 JSON 语法，先加额度（Day 15 的坑二）。
    """
    # client 可以外部传进来复用（省掉每次重建连接）；不传就现建一个
    client = client or make_client()
    response = client.chat.completions.create(
        model=model or os.environ.get("LLM_MODEL", "deepseek-flash"),
        messages=messages,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    choice = response.choices[0]
    return choice.message.content or "", choice.finish_reason or ""


def chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    *,
    client: OpenAI | None = None,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> ChatCompletionMessage:
    """发一次请求（带上工具说明），把模型的**整个 message 对象**返回给你。

    工具调用专用，和上面 chat_json 的区别值得记牢：
      · chat_json 写死了 `response_format={"type": "json_object"}`——那是让**正文**
        变成 JSON（Day 15 学的）。
      · 工具调用要的是模型在 `tool_calls` 字段里「点单」，正文可以是空。
      两个一起发会打架：实测（2026-10-09，deepseek-flash）不报错，但
      finish_reason='stop'、tool_calls=None，正文里吐出一段带内部标记、
      根本没法解析的残渣。所以工具调用这条路不用 JSON 模式。

    拿到返回后：`message.tool_calls` 是空的 → 这就是最终回答，看 `message.content`；
    不为空 → 它点了单，你要去执行（见练习第 2、3 题）。
    """
    client = client or make_client()
    response = client.chat.completions.create(
        model=model or os.environ.get("LLM_MODEL", "deepseek-flash"),
        messages=messages,
        tools=tools,
        max_tokens=max_tokens,
    )
    return response.choices[0].message
