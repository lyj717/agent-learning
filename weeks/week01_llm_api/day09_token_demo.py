"""Day 9 材料一：token 与成本。

每一节都按同一个顺序来：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

默认**不联网、不消耗额度**：用官方价格表和你 Day 8 的真实数据算账。
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day09_token_demo.py

加上 --live，真的发一次请求，把 usage 和算出来的钱一起打印（需要网络）：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day09_token_demo.py --live

价格与换算比例抄自官方文档（2026-10-04），会变，以官网为准：
    https://api-docs.deepseek.com/zh-cn/quick_start/pricing
    https://api-docs.deepseek.com/zh-cn/quick_start/token_usage
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 往上两层是仓库根目录（这个文件在 weeks/week01_llm_api/ 里）
ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv

# 单价：元 / 百万 token。deepseek-flash，抄自官方价格页
PRICE = {
    "空闲": {"input_hit": 0.02, "input_miss": 1.0, "output": 4.0},
    "高峰": {"input_hit": 0.04, "input_miss": 2.0, "output": 8.0},
}
# 高峰时段：周一~周五 9:00-12:00、14:00-18:00（北京时间，不含法定节假日），
# 其余时间都按空闲价算，正好是一半


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


def cost_of_call(
    prompt_tokens: int,
    completion_tokens: int,
    *,
    cached_tokens: int = 0,
    price: dict[str, float] = PRICE["空闲"],
) -> float:
    """算一次调用花多少钱（单位：元）。

    prompt_tokens     本次输入用了多少 token（响应里的 usage.prompt_tokens）
    completion_tokens 本次输出用了多少 token（usage.completion_tokens，**含思考**）
    cached_tokens     输入里命中缓存的那部分（usage.prompt_cache_hit_tokens）
    """
    miss = prompt_tokens - cached_tokens
    return (
        miss / 1_000_000 * price["input_miss"]
        + cached_tokens / 1_000_000 * price["input_hit"]
        + completion_tokens / 1_000_000 * price["output"]
    )


def simulate_input_tokens(
    system_tokens: int, user_tokens: int, assistant_tokens: int, turns: int
) -> list[int]:
    """模拟多轮对话：返回每一轮**请求**发出去的输入 token 数。

    关键点：模型没有记忆，每一轮都要把「system + 之前所有问答 + 新问题」
    重新发一遍，所以第 n 轮的输入会一轮比一轮大。
    """
    rows: list[int] = []
    history = system_tokens
    for _ in range(turns):
        current = history + user_tokens
        rows.append(current)
        history = current + assistant_tokens
    return rows


# ============================================================
section("1. token 是什么")
# ============================================================

say(
    "这是什么：token 是模型读写文本的最小单位，也是**计费单位**。",
    "           它不是「字」，也不是「词」——是模型自己的一套切分方式。",
    "",
    "  官方给的换算比例（只是估算，别拿它当账单）：",
    "    1 个中文字符 ≈ 0.6 个 token",
    "    1 个英文字符 ≈ 0.3 个 token",
    "    实际数量以响应里的 usage 为准",
    "",
    "为什么需要懂它：你发出去的每一个 token、收到的每一个 token 都要付钱。",
    "  「这句话值多少钱」这个问题，答案就是 token 数 × 单价。",
)


# ============================================================
section("2. 价格表：输入、输出、缓存，三档价")
# ============================================================

say(
    "  单位：元 / 百万 token。deepseek-flash（抄自官方价格页，2026-10-04）：",
    "",
    f"    {'项目':<22}{'空闲时段':>12}{'高峰时段':>12}",
    f"    {'输入（缓存命中）':<20}{PRICE['空闲']['input_hit']:>12}{PRICE['高峰']['input_hit']:>12}",
    f"    {'输入（缓存未命中）':<18}{PRICE['空闲']['input_miss']:>12}{PRICE['高峰']['input_miss']:>12}",
    f"    {'输出':<22}{PRICE['空闲']['output']:>12}{PRICE['高峰']['output']:>12}",
    "",
    "  三句话读完这张表：",
    "    ① 输出比输入贵 4 倍——因为它更值钱，也更容易被滥用（像思考）。",
    "    ② 缓存命中比未命中便宜 50 倍——重复的开头（比如固定的 system）",
    "       命中了缓存就几乎不要钱。",
    "    ③ 高峰时段是空闲时段的两倍价：工作日 9:00-12:00、14:00-18:00。",
)


# ============================================================
section("3. 代码：从 usage 算这次花了多少钱")
# ============================================================

say(
    "  响应里的 usage 就是账单的原始数据，三个字段最有用：",
    "    prompt_tokens              输入了多少 token",
    "    completion_tokens          输出了多少 token（含思考！）",
    "    prompt_cache_hit_tokens    输入里命中缓存的部分",
    "",
    "  有了这三个数，钱是这么算的：",
    "",
    "    miss = prompt_tokens - cached_tokens        # 没命中缓存的那部分",
    "    费用 = miss / 100 万 × 输入单价",
    "         + cached_tokens / 100 万 × 缓存单价",
    "         + completion_tokens / 100 万 × 输出单价",
    "",
)

sample_input, sample_output = 1_000, 500
sample_cost = cost_of_call(sample_input, sample_output)
say(
    f"  拿一组假数据试一下（输入 {sample_input}、输出 {sample_output}、空闲价）：",
    f"    {sample_input}/100万 × 1 + {sample_output}/100万 × 4 = {sample_cost:.6f} 元",
    "    不到 1 分钱——但真实产品的量级是每天几十万次调用。",
)


# ============================================================
section("4. 场景一：聊 20 轮，输入 token 会滚雪球")
# ============================================================

SYSTEM, USER, ASSISTANT, TURNS = 30, 10, 50, 20
rows = simulate_input_tokens(SYSTEM, USER, ASSISTANT, TURNS)

say(
    "  假设：system 30 token，每轮用户问 10 token，模型答 50 token。",
    "  每一轮都要把之前的问答重新发一遍，于是：",
    "",
)
for index, tokens in enumerate(rows, start=1):
    bar = "█" * min(40, tokens // 30)
    say(f"    第 {index:>2} 轮  输入 {tokens:>5} token  {bar}")

total_input = sum(rows)
content_only = SYSTEM + TURNS * (USER + ASSISTANT)
say(
    "",
    f"  第 1 轮只发 {rows[0]} 个 token，第 {TURNS} 轮要发 {rows[-1]} 个"
    f"（{rows[-1] / rows[0]:.0f} 倍）。",
    f"  {TURNS} 轮加起来一共发了 {total_input} 个输入 token；",
    f"  而对话内容的总量其实只有 {content_only} 个——",
    f"  差了约 {total_input / content_only:.1f} 倍，多出来的全是**重复发送**。",
    "",
    f"  换成钱（空闲价，输出按每轮 {ASSISTANT} 个算）：",
    f"    输入 {total_input}/100万 × 1 = {total_input / 1_000_000:.4f} 元",
    f"    输出 {TURNS * ASSISTANT}/100万 × 4 = {TURNS * ASSISTANT / 1_000_000 * 4:.4f} 元",
    f"    合计约 {cost_of_call(total_input, TURNS * ASSISTANT):.4f} 元",
    "",
    "  这就是「上下文越用越贵」的真相：不是模型变贵了，",
    "  是你每一轮都在为同一段历史重复付费。",
)


# ============================================================
section("5. 场景二：思考 token 也是钱（用你 Day 8 的真实数据）")
# ============================================================

name_input, name_output = 37, 1024
peak = PRICE["高峰"]
single = cost_of_call(name_input, name_output, price=peak)
say(
    "  你跑「给我起个名字，姓刘」那次，每一行都是：",
    f"    输入 {name_input} token，输出 {name_output} token（其中思考 {name_output}），finish=length，正文为空",
    "",
    f"  一次的钱（按高峰价）：{name_input}/100万 × 2 + {name_output}/100万 × 8"
    f" = {single:.6f} 元",
    f"  十次约 {single * 10:.4f} 元——你拿到了 0 个字。",
    "",
    "  两个可以记住的结论：",
    "    ① 思考算在**输出**那一档，也就是最贵的那档。",
    "    ② 被 max_tokens 截断的调用照样全额收费，一个字没出来也是钱。",
)


# ============================================================
section("6. 要注意什么")
# ============================================================

say(
    "  · 字符换算只能用来估：中文 0.6/字、英文 0.3/字符。要准就读 usage。",
    "  · 思考 token 记在输出里，而输出是最贵的一档——推理模型尤其要看住它。",
    "  · 缓存命中便宜 50 倍，但命中与否由服务商决定，别把省钱全押在这上面。",
    "  · 高峰/空闲差一倍价，批量任务挑空闲时段跑。",
    "  · 价格随时会变：账算不清时，先回官网看价格页，别看二手文章。",
    "  · 估算函数永远只是估算：真账单以服务商后台为准。",
)


# ============================================================
section("7. 接下来动手（这些是你的事）")
# ============================================================

say(
    "  1. 做练习，把成本估算函数自己写出来：",
    "     .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day09_exercises.py",
    "",
    "  2. 计划表上 Day 9 的交付物写的是「加上 /cost 命令」。",
    "     但 CLI 骨架要 Day 10 才搭——所以今天的交付物是**成本估算函数**，",
    "     Day 10 把它接进 CLI，/cost 命令就自然有了。",
    "",
    "  3. 想实测一次真实 usage，加 --live 再跑这个脚本：",
    "     .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day09_token_demo.py --live",
)


if LIVE:
    from openai import OpenAI, OpenAIError

    load_dotenv(ROOT / ".env")
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL"),
    )
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    section("--live：真实发一次，看看 usage 长什么样")
    try:
        # chat.completions.create(...)：发一次请求，这次要的是 usage 而不是内容
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "用一句话说明什么是 token"}],
            max_tokens=512,
        )
        usage = response.usage
        details = getattr(usage, "completion_tokens_details", None)
        reasoning = getattr(details, "reasoning_tokens", 0)
        hit = getattr(usage, "prompt_cache_hit_tokens", 0)
        say(
            f"  模型：{response.model}",
            f"  回答：{response.choices[0].message.content}",
            "",
            f"  prompt_tokens             = {usage.prompt_tokens}",
            f"  completion_tokens         = {usage.completion_tokens}"
            f"（其中思考 {reasoning or 0}）",
            f"  prompt_cache_hit_tokens   = {hit}",
            "",
            f"  按空闲价算，这次花了 {cost_of_call(usage.prompt_tokens, usage.completion_tokens, cached_tokens=hit):.6f} 元",
        )
    except OpenAIError as error:
        # 只捕 SDK 自己的异常类型
        say(f"  调用失败：{type(error).__name__}: {error}")
