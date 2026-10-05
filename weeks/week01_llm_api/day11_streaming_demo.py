"""Day 11 材料一：流式输出（打字机效果）是怎么来的。

每一节都按同一个顺序来：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

默认**不联网**：用假的「数据块」把流式返回的结构和解析过程演一遍。
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day11_streaming_demo.py

加上 --live，真的流式打一次（需要网络，会消耗一点点额度）：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day11_streaming_demo.py --live
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 往上两层是仓库根目录（这个文件在 weeks/week01_llm_api/ 里）
ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 这是什么：把「等一整段」换成「来一块给一块」")
# ============================================================

say(
    "非流式（你 Day 10 写的那版）：请求发出去 → 等模型把话全部说完 → 一次性拿到整段。",
    "流式（stream=True）：模型每生成一小段就立刻推给你，你收到一块显示一块。",
    "",
    "  为什么需要它：注意——**总时间几乎没变**，变的只是「你什么时候看到第一个字」。",
    "    非流式：5 秒后，屏幕上突然出现 200 个字。",
    "    流式：  0.8 秒后开始一个字一个字往外冒，一共还是 5 秒。",
    "  人的感受差别巨大：前者像卡住了，后者像有人在打字。这个指标叫「首字延迟」",
    "  （Time To First Token），是聊天类产品最重要的一条体感指标。",
    "",
    "  这也是 Week 00 Day 6 那条结论的又一次应用：流式不改总时长，改的是等待的形状。",
)


# ============================================================
section("2. 流式发回来的东西：一串「增量块」")
# ============================================================

say(
    "  底层走的是 SSE（server-sent events）：服务器一条条推，每条是一个 JSON，",
    "  最后用 data: [DONE] 收尾。单个块长这样（简化过的真实结构）：",
    "",
    '    {"choices": [{"delta": {"content": "流式"}, "index": 0}]}',
    '    {"choices": [{"delta": {"content": "输出"}, "index": 0}]}',
    "",
    "  三个要点，一个都不能漏：",
    "    ① 字段名是 delta（增量），不是 message——它只带「这次新多出来的那部分」",
    "    ② content 可能是空的（null）：思考模式下推理过程走 reasoning_content，",
    "       那时 content 是 None；最后一块也常常是空内容、只带 finish_reason 和用量",
    "    ③ 所以「有内容才拼」这个判断是必须的，不是可写可不写",
    "",
    "  这正是 Week 00 那份 stream_example.py 里 `if delta:` 的来历。",
)


# ============================================================
section("3. 拿假块跑一遍解析（离线，不花钱）")
# ============================================================

fake_chunks = [
    {"choices": [{"delta": {"role": "assistant", "content": ""}, "index": 0}]},
    {"choices": [{"delta": {"content": "流式"}, "index": 0}]},
    {"choices": [{"delta": {"content": "输出就是"}, "index": 0}]},
    {"choices": [{"delta": {"content": "边生成"}, "index": 0}]},
    {"choices": [{"delta": {"content": None}, "index": 0}]},
    {"choices": [{"delta": {"content": "边发给你。"}, "index": 0}]},
    {
        "choices": [{"delta": {"content": ""}, "finish_reason": "stop", "index": 0}],
        "usage": {"prompt_tokens": 37, "completion_tokens": 126, "total_tokens": 163},
    },
]

say("  解析规则就一句话：有 content 就拼上、就打印；没有就跳过。", "")

pieces: list[str] = []
for index, chunk in enumerate(fake_chunks, start=1):
    # chunk["choices"] 有时是空列表，先挡一下，不然 choices[0] 会 IndexError
    if not chunk["choices"]:
        say(f"    第 {index} 块：choices 是空的，跳过")
        continue
    delta = chunk["choices"][0]["delta"]
    piece = delta.get("content")
    usage = chunk.get("usage")
    if not piece:
        note = "空内容，跳过" + ("（这块带着 usage）" if usage else "")
        say(f"    第 {index} 块：{note}")
        continue
    pieces.append(piece)
    say(f"    第 {index} 块：打印 {piece!r}   → 目前拼到 {''.join(pieces)!r}")

say(
    "",
    f"  拼完整：{''.join(pieces)!r}",
    "",
    "  最后一块的原始 JSON 长这样（真实推过来的就是这种结构）：",
    f"    {json.dumps(fake_chunks[-1], ensure_ascii=False)}",
    "",
    "  看出来了吗：**整个回答不是一次拿到的，是你自己一块块拼出来的**。",
    "  所以流式这一路要自己维护两个东西：拼起来的完整文本（要存历史）和用量（要记账）。",
)


# ============================================================
section("4. 真实数据：这个模型的流式，前面一大段是「安静」的")
# ============================================================

say(
    "  下面这组是你今天真跑一次流式（prompt「用一句话说明什么是流式输出」）的数字：",
    "",
    "    一共 127 块",
    "    第 1 块就该有正文？没有——**第 99 块才开始出正文**",
    "    前 98 块全是 reasoning_content（思考），它们的 content 是 None",
    "    第 127 块：content=''、finish_reason='stop'、usage=CompletionUsage(...)",
    "",
    "  这件事很反直觉，但它直接影响体感：",
    "    · 对这个模型，用户点下回车之后要先等它「想」——打字机效果不会立刻启动；",
    "    · 想让它更早开口，就得压思考强度（reasoning_effort / thinking），这是 Day 12 的事；",
    "    · 写代码时更要小心：**不能拿「有没有收到内容」当「模型是不是在动」**。",
)


# ============================================================
section("5. 为什么打印必须带 flush=True")
# ============================================================

say(
    '  print(piece, end="", flush=True) —— 两个参数一个都不能少：',
    "",
    '    end=""      不要每次都换行（否则一个字一行，变成瀑布）',
    "    flush=True  立刻把内容推出去，别攒在缓冲区里",
    "",
    "  为什么非得 flush：Python 的输出默认有缓冲。往终端打是「行缓冲」——",
    "  没遇到换行就不吐出来；重定向到文件时是「块缓冲」，攒够一大块才吐。",
    "  而我们流的每一块都没有换行，所以不 flush 的话，你会看到「憋很久，然后一坨全出来」，",
    "  打字机效果就没了。",
    "",
    "  想亲眼确认：在你自己的终端里跑两次对比——",
    "    第 1 次把 flush=True 去掉，第 2 次加上。第一次是「憋住再吐」，第二次才是一个个冒。",
)


# ============================================================
section("6. 流被打断了怎么办（这天要求处理的第二件事）")
# ============================================================

say(
    "  流式和「一次性请求」最大的不同：**它可能中途断掉**——网断了、用户按了 Ctrl+C、",
    "  程序自己抛异常。这时屏幕上已经有了半截回答，而你没有完整文本。",
    "",
    "  三条处理原则：",
    "    ① 已经打出去的字收不回来（那是用户看到的），但**别把半截回答存进历史**——",
    "       下一轮模型会顺着一段残缺的 assistant 消息往下说，比丢了还糟；",
    "    ② 要么在屏幕上补一句「（回答被中断）」，要么把这一轮整个丢掉；",
    "    ③ 这一轮已经花掉的 token 照样要记账——usage 没拿到就记 0，但别不记。",
    "",
    "  这和 Day 10 那条「失败的问句不要留在历史里」是同一个原则：",
    "  **屏幕上的东西可以残缺，历史里必须是完整的。**",
)


# ============================================================
section("7. 接下来动手（这些是你的事）")
# ============================================================

say(
    "  1. 去 llm.py 写 stream_chat()——骨架和「要做的」都写好了：",
    "     weeks/week01_llm_api/chat_cli/llm.py",
    "     （Week 00 你写过一版流式，这次多两件事：usage 要带回来、思考那块要跳过）",
    "",
    "  2. 然后把 chat_cli.py 的 main 换成流式（那里留了 TODO(Day 11)）：",
    "     边收边打，收完再存历史、记用量。",
    "",
    "  3. 验收标准（计划表上写的）：**打字机效果能稳定跑 10 次不崩**。",
    "     自己多按几次，尤其试试打一半按 Ctrl+C。",
)


if LIVE:
    from openai import OpenAI, OpenAIError

    section("--live：真流式打一次（每块都标了序号）")
    load_dotenv(ROOT / ".env")
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL"),
    )
    try:
        # stream=True：不要等全部生成完，让服务端一块块推过来
        stream = client.chat.completions.create(
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": "用一句话说明什么是流式输出"}],
            max_tokens=512,
            stream=True,
        )
        say("  正文：", end="")
        index = 0
        usage = None
        for chunk in stream:
            index += 1
            if not chunk.choices:
                continue
            piece = chunk.choices[0].delta.content
            if piece:
                print(piece, end="", flush=True)
            if chunk.usage is not None:
                usage = chunk.usage
        print()
        say(
            "",
            f"  一共 {index} 块；用量：{usage}",
            "  （思考那几百块不打出来，所以你看不到它们——但它们确实在流里占着位置）",
        )
    except OpenAIError as error:
        # 只捕 SDK 自己的异常类型
        say(f"  调用失败：{type(error).__name__}: {error}")
