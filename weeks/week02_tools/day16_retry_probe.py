"""Day 16 工具：**零成本**自测第 3 题（不发一次网络请求，不花一分钱）。

跑法（在你的练习文件能编译的前提下）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_retry_probe.py

它做三个检查：
    检查 1  第一次给坏数据、第二次给好数据 —— 看它会不会「校验失败 → 回填 → 重发 → 通过」
    检查 2  直接注入一段**合法**的 first_reply —— 看它是不是一次请求都不发就返回对象
    检查 3  一直给坏数据 —— 看它有没有在 attempts 次之后老实返回 None（不是死循环）

手法说明：把 llm_client.chat_json 换成一个**假的**函数（不发网络、直接返回写死的文本），
再用一个「一叫就报错」的守卫去证明「某条路径不该发请求」。
这个「把要花钱的那一层换成假的」的技巧，测工具调用、测 RAG 时同样好用。
"""

import importlib.util
import sys
from pathlib import Path

PRACTICE = Path(__file__).with_name("day16_pydantic_exercises.py")

# 学员的模块里有 `from llm_client import ...`，而 llm_client 就在同一个目录。
# 直接跑本脚本时，脚本所在目录**不在** sys.path 上（只有仓库根在），所以手动补一下，
# 否则会报 ModuleNotFoundError: No module named 'llm_client'
sys.path.insert(0, str(Path(__file__).parent.resolve()))

spec = importlib.util.spec_from_file_location("ex", PRACTICE)
practice = importlib.util.module_from_spec(spec)
sys.argv = ["ex"]  # 别让 --live 把练习文件的主程序带起来
spec.loader.exec_module(practice)

# 两种「模型返回」：坏的那段电话带横线，过不了 11 位数字那条规矩；好的那段是规整过的
BAD_REPLY = '{"name": "王芳", "phone": "138-0013-8000", "city": "上海", "job": "销售"}'
GOOD_REPLY = '{"name": "王芳", "phone": "13800138000", "city": "上海", "job": "销售"}'


class FakeChat:
    """假的 chat_json：按顺序吐出预设的返回，并记下每次发出去几条消息。"""

    def __init__(self, replies: list[str]) -> None:
        self.replies = replies
        self.sent: list[list] = []

    def __call__(self, messages, *, client=None, **kwargs):
        self.sent.append(list(messages))
        index = min(len(self.sent) - 1, len(self.replies) - 1)
        return self.replies[index], "stop"


def tell_me_why_not(ok: bool, reason: str) -> None:
    print("  ✓ 通过" if ok else f"  ✗ 没通过：{reason}")


print("=" * 64)
print("检查 1：第一次坏、第二次好 —— 应该「回填 → 重发 → 通过」")
print("=" * 64)
fake = FakeChat([BAD_REPLY, GOOD_REPLY])
practice.chat_json = fake
result = practice.extract_with_retry("随便一句话", attempts=2)
print(
    f"  chat_json 被调用 {len(fake.sent)} 次，每次的消息条数 {[len(m) for m in fake.sent]}"
)
print(f"  返回值：{result}")
tell_me_why_not(
    len(fake.sent) == 2, "只发了 1 次请求——多半是「拿模型返回」那步写在循环外面了"
)
tell_me_why_not(
    len(fake.sent) > 1 and len(fake.sent[1]) == 4,
    "第二次发出去的不是 4 条消息——第 5 步回填的 assistant + user 两条没带上",
)
tell_me_why_not(
    result is not None and getattr(result, "phone", None) == "13800138000",
    "最终没拿到对象（或 phone 不对）——重试之后没有再校验一次",
)

print()
print("=" * 64)
print("检查 2：注入一段合法的 first_reply —— 应该一次请求都不发")
print("=" * 64)


def guard(*args, **kwargs):
    """守卫：只要有人调用 chat_json 就报错，证明「这条路不该发请求」。"""
    raise AssertionError("走到了发请求这一步")


practice.chat_json = guard
try:
    injected = practice.extract_with_retry("随便一句话", first_reply=GOOD_REPLY)
except AssertionError:
    print("  ✗ 没通过：它还是去发请求了——first_reply 那个分支还没接上")
else:
    print(f"  返回值：{injected}")
    tell_me_why_not(
        injected is not None and getattr(injected, "name", None) == "王芳",
        "返回的不是 PersonExtract 对象",
    )
    print("  （一次网络请求都没发，所以这一检查不花任何钱）")

print()
print("=" * 64)
print("检查 3：一直给坏数据 —— 试满 attempts 次后返回 None，不能死循环")
print("=" * 64)
always_bad = FakeChat([BAD_REPLY])
practice.chat_json = always_bad
gave_up = practice.extract_with_retry("随便一句话", attempts=2)
print(f"  chat_json 被调用 {len(always_bad.sent)} 次，返回值：{gave_up}")
tell_me_why_not(
    len(always_bad.sent) == 2, f"应该正好试 2 次，实际 {len(always_bad.sent)} 次"
)
tell_me_why_not(gave_up is None, "一直失败时应该返回 None，而不是抛异常或返回半个结果")

print()
print("三个检查全过，就可以去掉守卫、跑一次真的 --live 了：")
print(
    "  .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_exercises.py --live"
)
