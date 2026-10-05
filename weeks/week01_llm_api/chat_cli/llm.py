"""和模型打交道的那一层：发请求，把回复和用量一起拿回来。

这一层不碰命令行、也不打印任何东西，所以好测、也好替换。
Day 10 先做**非流式**——一次拿回完整回答；流式打印是 Day 11 的事。
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# 写 chat() 的时候，把下面这行的注释去掉——现在注释着，是因为 chat() 还没实现，
# 没人用它，ruff 会报「导入了没用」（F401）
# from openai import OpenAI

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
    """发一次请求（非流式），返回（回答文本, usage 用量对象）
    要做的（把它写成 Week 00 那版的升级版，不是照抄）：
        0. 先把文件顶部 `# from openai import OpenAI` 那行的注释去掉
        1. 建客户端：
               client = OpenAI(api_key=require_api_key(),
                               base_url=os.environ.get("LLM_BASE_URL"))
           （require_api_key 上面已经给你了，和 Week 00 那个是同一件事）
        2. 组装这次要发出去的字段：model（不传就用 .env 里的 LLM_MODEL）、
           messages、max_tokens
        3. temperature 只有**不是 None** 的时候才放进字段里——不传就别带这个键
        4. 发请求：client.chat.completions.create(**字段)
        5. 返回（回答文本去掉首尾空白, response.usage）
    期望结果：
        text, usage = chat([{"role": "user", "content": "你好"}])
        text  是模型的回答字符串（不是对象、不是列表）
        usage 上有 .prompt_tokens 和 .completion_tokens 两个数字，/cost 要用它算钱

    提示：
        - messages 是「一整串对话」：system + 历史 + 这次的问题，整段发过去
        - 为什么要返回 usage：不返回它，/cost 就没有原始数据可算（Day 9）
        - 为什么要给 max_tokens 上限：不给的话，思考模型可能一直想下去（Day 8）
        - 为什么 temperature 用「不传就不带」的写法：把用不用它的决定留给调用方，
          而且这个模型在思考模式下它本来也不生效（Day 8 实验验证过）
    """
    raise NotImplementedError(
        "把 Week 00 那版改写成「吃 messages、返回 (文本, usage)」的版本"
    )
