"""Day 40 的请求运行环境：沿用已学的 JSON 请求，并保留原文、结束原因与用量。

这里不组装证据、不解析回答，也不判断引用是否支持结论；这些由上层处理。
密钥、服务商地址和模型继续读取仓库的 .env，不向屏幕打印凭据。
"""

import os
import sys
from pathlib import Path

# __file__ 定位本文件；parents[4] 是仓库根目录，启动目录改变也能找到共用模块。
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week02_tools.demos.shared.llm_client import make_client


def request_grounded_json(messages: list[dict[str, str]]) -> dict:
    """发一次无重试的 JSON 请求，返回原文、结束原因、用量和实际响应模型名。"""
    # make_client()：读取根目录 .env，建超时且 max_retries=0 的客户端。
    # with 会在请求结束或抛异常时关闭客户端连接。
    with make_client() as client:
        # os.environ.get(名字, 默认值)：读取环境配置；make_client 已加载 .env。
        model = os.environ.get("LLM_MODEL", "deepseek-flash")
        # create(...)：提交消息；JSON 模式限制输出格式，不保证证据足够或引用正确。
        # max_tokens 限制输出量，timeout 限制本次等待秒数；关闭思考沿用 Day 35 配置。
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=1024,
            timeout=45,
            extra_body={"thinking": {"type": "disabled"}},
        )
    if not response.choices:
        raise RuntimeError("模型响应没有 choices，无法取得正文和结束原因")

    choice = response.choices[0]
    usage = response.usage
    return {
        "raw_text": choice.message.content or "",
        "finish_reason": choice.finish_reason or "",
        "usage": (
            {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
            if usage is not None
            else None
        ),
        "model": response.model,
    }
