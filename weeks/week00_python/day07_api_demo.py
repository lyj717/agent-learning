"""调用模型 API：把前几天学的东西串成一条链。

每一节都是同一个顺序：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

这份演示是 Day 7 的前置知识：不涉及新语法，只是把 HTTP、JSON、Pydantic、
环境变量、生成器这几样你已经会的东西，组装成「问模型一句话」这件事。

默认**不联网、不消耗额度**，只讲解和用假数据演示：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day07_api_demo.py

想真的调用一次（需要网络，会消耗一点额度，密钥从 .env 读）：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day07_api_demo.py --live
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
LIVE = "--live" in sys.argv


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


def mask(secret: str | None) -> str:
    """密钥只显示长度，不显示内容——日志和截图里都该这么做。"""
    if not secret:
        return "（没设置）"
    return f"已设置，{len(secret)} 个字符"


# ============================================================
section("1. 所谓「调用模型 API」，就是发一次 HTTP 请求")
# ============================================================

say(
    "这是什么：把一段文字发给服务商的服务器，服务器把模型的回复发回来。",
    "为什么需要：模型跑在人家的机器上，你的程序只能通过网络问它。",
    "场景：Week 01 那个聊天机器人，核心就是这一次请求。",
    "",
    "  拆开看，一次请求包含四样东西：",
    "",
    "    ① 地址（URL）      往哪儿发，比如 https://api.deepseek.com/chat/completions",
    "    ② 方法（method）   POST，意思是「我要提交一段数据给你处理」",
    "    ③ 请求头（headers）附带的说明，最重要的一条是",
    "                       Authorization: Bearer sk-xxxx",
    "                       ——这就是你的密钥，服务器靠它认人",
    "    ④ 请求体（body）   你要说的话，一段 JSON",
    "",
    "  服务器回给你的也有两样：",
    "    状态码（status）   200 表示成功，401 表示密钥不对，429 表示限额用完",
    "    响应体（body）     一段 JSON，模型的话就装在里面",
    "",
    "  这就是全部。你现在回头看 day05 学的 httpx，会发现它就是干这个的。",
)


# ============================================================
section("2. 请求体长什么样：三个角色 + 一段历史")
# ============================================================

load_dotenv(ROOT / ".env")

example_messages = [
    {"role": "system", "content": "你是一个简洁的助手。"},
    {"role": "user", "content": "杭州今天天气怎么样？"},
    {"role": "assistant", "content": "22 度，多云。"},
    {"role": "user", "content": "那明天呢？"},
]

say(
    "  请求体里最重要的字段是 messages，它是一个列表，按时间顺序排列：",
    "",
)
for message in example_messages:
    say(f"    {message}")
say(
    "",
    "  三种角色各有分工：",
    "    system     设定模型的人设和规矩，一般只放一条，放最前面",
    "    user       用户说的话",
    "    assistant  模型之前说过的话（要接着聊，就得把历史带上）",
    "",
    "  看出来了吗——这就是你 Day 4 综合题里做的 Conversation。",
    "  所谓「多轮对话」，不是模型记得住，而是你每次都把历史重新发一遍。",
    "  这也是为什么聊得越久，每次请求带的内容越多、花的钱越多。",
    "",
    "  请求体里还有几个常用字段：",
    "    model        用哪个模型",
    "    stream       true 表示流式返回（第 5 节讲）",
    "    temperature  0 到 2，越小越稳定、越大越随机（写代码时用低的）",
    "    max_tokens   最多生成多少字，用来兜底防止话太多",
)


# ============================================================
section("3. 响应体长什么样：SDK 把 JSON 变成了对象")
# ============================================================

# 一段真实的响应 JSON（这里用假的示例数据，不联网）
fake_response = {
    "id": "chatcmpl-abc123",
    "model": "deepseek-v4-flash",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "22 度，多云。"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 21, "completion_tokens": 9, "total_tokens": 30},
}

say(
    "  服务器返回的是一段 JSON，长这样（下面是简化过的真实结构）：",
    "",
    json.dumps(fake_response, ensure_ascii=False, indent=2),
    "",
    "  你现在已经会读它了（Day 5 学的）：",
    f"    用字典的方式取值：{fake_response['choices'][0]['message']['content']!r}",
)
print()

say(
    "  但 openai 这个库（SDK）会先把 JSON 转成对象，让你能这么写：",
    "",
    "    response.choices[0].message.content",
    "",
    "  两种写法一一对应，只是点号代替了方括号和引号：",
    "    response.choices[0].message.content  ==  raw['choices'][0]['message']['content']",
    "    response.usage.total_tokens          ==  raw['usage']['total_tokens']",
    "",
    "  换句话说，SDK 内部也用 Pydantic 定义了模型（你 Day 4 学的那套），",
    "  只是它把字段定义藏起来了。你以后写工具时，用的就是同一个套路。",
    "",
    "  几个字段的意思：",
    "    choices[0]        第 0 个候选回复（默认只要一个）",
    "    finish_reason     stop 表示正常说完了，length 表示被 max_tokens 截断",
    "    usage             这次用了多少 token——这是计费的依据",
)


# ============================================================
section("4. 完整的一次调用（默认不真的发出去）")
# ============================================================

say(
    "  最小可运行的版本长这样，和你在 day06_stream_example.py 里看到的一样：",
    "",
    "    load_dotenv(ROOT / '.env')          # ① 先把密钥读进环境变量",
    "    client = OpenAI(                     # ② 建客户端",
    "        api_key=os.environ['LLM_API_KEY'],",
    "        base_url=os.environ.get('LLM_BASE_URL'),",
    "    )",
    "    response = client.chat.completions.create(   # ③ 发请求，等回复",
    "        model=os.environ.get('LLM_MODEL'),",
    "        messages=[{'role': 'user', 'content': '你好'}],",
    "    )",
    "    print(response.choices[0].message.content)   # ④ 把话取出来",
    "",
    "  三行代码背后，就是第 1 节那四样东西：地址、方法、请求头、请求体。",
    "  SDK 替你拼好了前三样，你只负责填请求体。",
)

say(
    "",
    "  当前 .env 里的配置（密钥打码）：",
    f"    LLM_BASE_URL = {os.environ.get('LLM_BASE_URL')!r}",
    f"    LLM_MODEL    = {os.environ.get('LLM_MODEL')!r}",
    f"    LLM_API_KEY  = {mask(os.environ.get('LLM_API_KEY'))}",
)


if LIVE:
    from openai import OpenAI, OpenAIError

    print()
    say("  --live 已开启，真的发一次请求：")
    try:
        live_client = OpenAI(
            api_key=os.environ["LLM_API_KEY"],
            base_url=os.environ.get("LLM_BASE_URL"),
        )
        live_response = live_client.chat.completions.create(
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": "用一句话说明什么是异步。"}],
        )
        say(
            f"    模型的回复：{live_response.choices[0].message.content}",
            f"    本次用量：{live_response.usage}",
        )
    except OpenAIError as error:
        # 只捕 SDK 自己的异常类型，别用 except Exception 一把抓
        say(
            f"    调用失败：{type(error).__name__}",
            f"    {error}",
            "",
            "    这是 SDK 抛出来的（密钥、模型名、余额、网络都可能），",
            "    对照第 6 节那张表看看是哪一种。",
        )
else:
    print()
    say(
        "  想真的发一次，就加 --live 重新运行：",
        "    .venv\\Scripts\\python.exe weeks\\week00_python\\day07_api_demo.py --live",
        "",
        "  这一节没有联网，所以上面的响应是假的示例数据。",
    )


# ============================================================
section("5. 流式：把 delta 一块块拼回去")
# ============================================================

say(
    "  非流式：等模型把话全部说完，一次性给你一整段。",
    "  流式（stream=True）：一个字刚生成出来就发给你，送来一串小碎片。",
    "",
    "  每个碎片长这样（同样是简化过的真实结构）：",
    "",
    '    {"choices": [{"delta": {"content": "杭州"}, "index": 0}]}',
    '    {"choices": [{"delta": {"content": "今天"}, "index": 0}]}',
    '    {"choices": [{"delta": {"content": "22 度。"}, "index": 0, "finish_reason": "stop"}]}',
    "",
    "  注意三点：",
    "    · 字段名是 delta（增量），不是 message——它只带「新多出来的那部分」",
    "    · 每块里那个 content 可能为空（比如最后一块只带 finish_reason）",
    "      所以 day06 里那个 if delta: 判断是必须的",
    "    · 想同时存下完整回复，就一边打印一边累加：full += delta",
    "",
    "  这正是你 Day 6 学的生成器：服务端一条条 yield 给你，你一条条消费。",
    "  区别只是这里的「生成器」在网线的另一端。",
)


# ============================================================
section("6. 出错了怎么读")
# ============================================================

say(
    "  调 API 最常见的几种失败，看到就知道该查哪里：",
    "",
    "    401 Unauthorized        密钥不对：没读到 .env、复制不全、或者已失效",
    "    402 / 429               余额不足或请求太频繁（等你账户里有钱再看）",
    "    404 Not Found           模型名写错了，或者 base_url 少/多了一段",
    "    400 Bad Request         请求体不对劲：参数名写错、格式不对",
    "    连接超时 / DNS 失败      网络问题，不是代码问题（你前天推 GitHub 就遇到过）",
    "",
    "  两条实用习惯：",
    "    1. 报错原文里通常有一句人话（比如 Invalid API key），先读它。",
    "    2. 把状态码和报错的 JSON 用 logging 记下来——Day 5 学的 logger.exception。",
    "",
    "  别做的一件事：不要把 except Exception 一把抓之后当成「网络问题」重试，",
    "  密钥错了重试一百次也还是错，只会浪费时间和额度。",
)


# ============================================================
section("7. 换服务商只改三个值")
# ============================================================

say(
    "  OpenAI、DeepSeek、通义千问、Kimi、GLM 都提供「OpenAI 兼容」的接口，",
    "  意思是：请求的格式一样，只是地址、密钥、模型名不同。",
    "",
    "  所以你代码里永远写变量名，不写死具体的服务商：",
    "",
    "    LLM_BASE_URL=https://api.deepseek.com      ← 换成别家的地址就行",
    "    LLM_MODEL=deepseek-v4-flash                ← 换成别家的模型名",
    "    LLM_API_KEY=sk-xxxx                        ← 换成别家的密钥",
    "",
    "  这也是 .env.example 里那三个变量名的来历。",
    "  换一家 = 改 .env 三行，代码一个字都不用动——这就是「配置和代码分开」的价值。",
)


section("小结：你已经具备了做 Day 7 交付物的全部知识")
say(
    "  API 调用   → 这份演示 + day06_stream_example.py",
    "  命令行参数 → argparse_demo.py（现成的，跑一遍就够）",
    "  密钥与日志 → Day 5 学的 dotenv / logging",
    "  请求结构   → Day 4 学的 Pydantic",
    "  流式打印   → Day 6 学的生成器 + flush",
    "  测试       → tests/test_check_env.py 就是现成的范例",
    "",
    "  接下来把这几块拼成一个工具：输入一个问题，流式打印模型的回答。",
    "  结构照着 docs/python-7天补齐清单.md 里 Day 7 那七条来。",
)
