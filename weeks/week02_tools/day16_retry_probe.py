"""Day 16 工具：**零成本**验证「重试」到底有没有真的重发请求。

做法：把 llm_client.chat_json 换成一个假函数（它不发网络请求、直接返回一段写死的文本），
然后数一数它被调用了几次。逻辑对不对，看次数就知道：

    attempts=2 且模型一直给坏数据  → 应该被调用 2 次（第一次 + 重试一次）

用法（跑之前练习文件要能编译）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_retry_probe.py

这个「把要花钱的那一层换成假的」的手法本身就值钱：它让你在写完的当天，
不用花一分钱就能把重试、上限、错误回填这些逻辑全验一遍。
"""

import importlib.util
import sys
from pathlib import Path

PRACTICE = Path(__file__).with_name("day16_pydantic_exercises.py")

# 学员的模块里有 `from llm_client import ...`，而 llm_client 就在同一个目录。
# 直接 import 这个文件时，脚本所在目录**不在** sys.path 上（只有仓库根在），
# 所以要手动补一下，否则报 ModuleNotFoundError: No module named 'llm_client'
sys.path.insert(0, str(Path(__file__).parent.resolve()))

spec = importlib.util.spec_from_file_location("ex", PRACTICE)
practice = importlib.util.module_from_spec(spec)
sys.argv = ["ex"]  # 别让 --live 把它带起来
spec.loader.exec_module(practice)

# 一段「永远过不了校验」的模型返回：电话带横线，11 位数字那条规矩拦得下
BAD_REPLY = '{"name": "王芳", "phone": "138-0013-8000", "city": "上海", "job": "销售"}'

calls: list[list] = []


def fake_chat_json(messages, *, client=None, **kwargs):
    """假的 chat_json：不发请求，记录下这次发出去几条消息，然后返回坏数据。"""
    calls.append(messages)
    return BAD_REPLY, "stop"


practice.chat_json = fake_chat_json

ATTEMPTS = 2
result = practice.extract_with_retry("随便一句话", attempts=ATTEMPTS)

print(f"attempts = {ATTEMPTS}，chat_json 实际被调用了 {len(calls)} 次")
print(f"每次发出去的消息条数：{[len(m) for m in calls]}")
print(
    "（第一次 2 条：system + user；重试那次应该是 4 条：多出 assistant + user 的纠错要求）"
)
print(f"函数返回值：{result}（一直给坏数据时应该是 None）")

if len(calls) == ATTEMPTS:
    print("\n✓ 次数对了：重试真的重发了一次请求。")
    if len(calls) > 1 and len(calls[1]) < 4:
        print("✗ 但第二次发出去的消息太少了——第 5 步回填的两条消息没带上。")
else:
    print(
        f"\n✗ 次数不对：只发了 {len(calls)} 次。多半是「拿模型返回」那一步写在了循环外面，"
        "所以循环里每圈校验的都是同一段旧文本，重试等于没发。"
    )
