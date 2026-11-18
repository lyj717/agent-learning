"""Day62 手动 live 冒烟：一次最小模型调用，验证密钥与入口，不重试。

只在 GitHub Actions 的 workflow_dispatch 或本地手动运行时使用；push 触发的
CI 不跑这个脚本。预算：1 次调用，max_tokens=32，超时 30 秒，失败不自动重试。
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    """发一次最小请求；密钥缺失、请求失败或空回答时以非零码退出。"""
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL")
    model = os.environ.get("LLM_MODEL", "deepseek-flash")
    if not api_key or not base_url:
        raise SystemExit("缺少 LLM_API_KEY 或 LLM_BASE_URL")

    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=0, timeout=30.0)
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "只回复两个字：收到"}],
        temperature=0,
        max_tokens=32,
    )
    elapsed = (time.perf_counter() - started) * 1000
    content = (response.choices[0].message.content or "").strip()
    usage = response.usage
    print(f"模型={model}")
    print(f"回答={content!r}")
    print(f"耗时={elapsed:.0f}ms")
    if usage is None:
        print("用量=未返回")
    else:
        print(
            f"用量={usage.prompt_tokens}+{usage.completion_tokens}"
            f"（共 {usage.total_tokens}）"
        )
    if not content:
        raise SystemExit("回答为空")


if __name__ == "__main__":
    main()
