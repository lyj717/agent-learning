"""Day 15 练习：从杂乱文本里抽出固定字段。

跑法（默认离线自测，不花钱）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day15_structured_output_exercises.py

真跑 10 条样本、统计解析成功率（要网络，会用掉 10 次调用）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day15_structured_output_exercises.py --live

做完把结果抄进交付物：weeks/week02_tools/day15_抽取成功率记录.md
"""

import json
import os
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv

max_tokens = 2048

# 第 3 题读 .env 时要用到它（这个文件在 weeks/week02_tools/ 里，往上两层是仓库根目录）
ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv

# 要从每条文本里抽出来的四个字段。名字和类型先定死，
# 提示词、解析、统计全都对着这四个走——这就是「结构化」。
FIELDS = {
    "name": "姓名，字符串",
    "phone": "手机号，字符串；原文里没有就填 null",
    "city": "城市，字符串；原文里没有就填 null",
    "job": "岗位，字符串；原文里没有就填 null",
}

# 十条样本。真人写的东西就长这样：中英混杂、顺序乱、有噪声、偶尔缺字段。
SAMPLE_TEXTS = [
    "我叫刘小明，电话 13800138000，在杭州做后端，2021 年入职，主要写 Python。",
    "您好，我是王芳，负责华东区销售。手机 13912345678，常驻上海，随时联系。",
    "张伟 | 北京 | 数据分析师 | 18600001111 | 会 SQL 和 Tableau。",
    "刚才那个同学是李娜，做前端的，电话号码我忘了，好像是在深圳。",
    (
        "Hi, this is Chen Jie from Guangzhou. I work as a QA engineer. "
        "Reach me at 13711112222 any time."
    ),
    "赵敏，女，1995 年生，目前待业，想找产品经理的岗位，人在成都。",
    (
        "联系我：周杰（13655556666）。顺带说一下，我同事吴磊也在找工作，"
        "他在南京做运维，电话 13655557777。"
    ),
    (
        "啊啊啊忘了我还没自我介绍😅 我是孙悟空，从石头里蹦出来的🐒 电话没有，"
        "我在花果山当大王。"
    ),
    (
        "受强冷空气影响，预计明天本市气温将下降 8 到 10 摄氏度，"
        "请市民注意添衣保暖。（本条为气象台发布）"
    ),
    (
        "入职登记表——姓名：欧阳娜娜；联系电话：13500009999；"
        "现居：广州；岗位：运维工程师；备注：曾在北京、上海两地工作。"
    ),
]

# 每条文本的「参考答案」。先自己看抽出来的结果，再回头对这里。
# 注意它只是**参考答案**，不是标准答案——它也是 AI 照着原文记下来的判断。
# 抽出来和它对不上时，先回原文看谁更忠实，再决定谁错。
# 第 5 条和第 8 条是有争议的，下面单独写了。
EXPECTED = [
    {"name": "刘小明", "phone": "13800138000", "city": "杭州", "job": "后端"},
    # 原文说「负责华东区销售」，所以「华东区销售」比「销售」更忠实；
    # 抽成「销售」也不算错——这类「细一点还是粗一点」的分寸，就是 Day 16 要讨论的。
    {"name": "王芳", "phone": "13912345678", "city": "上海", "job": "华东区销售"},
    {"name": "张伟", "phone": "18600001111", "city": "北京", "job": "数据分析师"},
    {"name": "李娜", "phone": None, "city": "深圳", "job": "前端"},
    # 原文是英文，写 "Guangzhou" 更忠实；翻成「广州」也说得通。
    {
        "name": "Chen Jie",
        "phone": "13711112222",
        "city": "Guangzhou",
        "job": "QA engineer",
    },
    {"name": "赵敏", "phone": None, "city": "成都", "job": "产品经理"},
    {"name": "周杰", "phone": "13655556666", "city": None, "job": None},
    # 争议样本：原文说「我在花果山当大王」。这里填 None 是我的判断——
    # 「大王」是玩笑话，不是岗位。模型很可能给你填上别的词，
    # 那条到底算对还是算错，你先自己想清楚判据是什么。
    {"name": "孙悟空", "phone": None, "city": None, "job": None},
    {"name": None, "phone": None, "city": None, "job": None},
    {"name": "欧阳娜娜", "phone": "13500009999", "city": "广州", "job": "运维工程师"},
]


def build_messages(text: str) -> list[dict[str, str]]:
    """第 1 题：把「要抽哪四个字段」写进提示词，拼成要发出去的 messages。"""
    messages = [
        {"role": "system", "content": f"你是信息抽取助手，只输出 JSON。字段：{FIELDS}"},
        {"role": "user", "content": f"从下面这段话里抽取字段，输出 JSON：\n{text}"},
    ]
    return messages


def parse_or_none(raw: str) -> dict | None:
    """第 2 题：把模型返回的**文本**变成 dict；变不成就返回 None。"""
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return None
    except json.JSONDecodeError:
        return None
    return parsed


def extract_fields(text: str) -> dict | None:
    """第 3 题：串起来——真发一次请求，把 text 抽成 dict；失败就返回 None。"""
    load_dotenv(ROOT / ".env")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    client = openai.Client(
        api_key=os.environ.get("LLM_API_KEY"),
        base_url=os.environ.get("LLM_BASE_URL"),
        max_retries=0,
    )
    fields = {
        "model": model,
        "messages": build_messages(text),
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    response = client.chat.completions.create(**fields)
    return parse_or_none(response.choices[0].message.content)


if __name__ == "__main__":
    print("=== 第 1 题：拼提示词 ===")
    messages = build_messages("我叫刘小明，电话 13800138000，在杭州做后端。")
    for message in messages:
        print(f"  [{message['role']}] {message['content']}")
    print(f"  一共 {len(messages)} 条（预期 2）")

    print("\n=== 第 2 题：安全解析（这三条都不联网）===")
    cases = [
        ("正常 JSON", '{"name": "刘小明"}'),
        ("空字符串", ""),
        (
            "带围栏的返回",
            '```json\n{\n  "name": "刘小明"\n}\n```',
        ),
        ("不是对象", "[1, 2]"),
    ]
    for label, raw in cases:
        print(f"  {label:<8} -> {parse_or_none(raw)}")
    print("  预期：正常 JSON 给出 dict，其余三条都是 None（对不上就是这题没做对）")

    print("\n=== 第 3 题：真抽 10 条 ===")
    if not LIVE:
        print("  这题要联网、会花钱，所以默认不跑。想跑就在命令后面加 --live：")
        print(
            "  .venv\\Scripts\\python.exe "
            "weeks\\week02_tools\\day15_structured_output_exercises.py --live"
        )
        print("  跑完之后，把每条的成败抄进 day15_抽取成功率记录.md")
    else:
        results = []
        for index, (text, want) in enumerate(zip(SAMPLE_TEXTS, EXPECTED), start=1):
            got = extract_fields(text)
            results.append(got)
            print(f"  [{index:>2}] 原文：{text[:28]}……")
            print(f"       抽到：{json.dumps(got, ensure_ascii=False)}")
            print(f"       我这边记的答案：{json.dumps(want, ensure_ascii=False)}")
        ok = sum(1 for item in results if item is not None)
        print(
            f"\n  解析成功 {ok} / {len(SAMPLE_TEXTS)}，成功率 {ok / len(SAMPLE_TEXTS):.1%}"
        )
        print("  逐条对一遍上面两行「抽到 / 答案」：解析成功 ≠ 抽得对。")
        print("  两个数（解析成功率、字段正确率）都抄进交付物，并写下你的结论。")

# ============================================================
# 现象与原因（做完之后填，用自己的话）
# ============================================================
#
# 1. 10 条里解析成功几条？失败的那几条，返回的到底是什么（空串？带了围栏？
#    被截断了？）把 finish_reason 也写下来。
#   10条都成功了
#
# 2. 解析成功但字段抽错的，有哪几条？错在哪一类——把原文没有的信息编了出来
#    （幻觉），还是该填 null 的地方填了别的东西？
#   一个不够细，一个把玩笑当成了岗位
#   一个该填null的输出了空字符
#
# 3. 第 9 条（气象台那条）和别的条有什么不一样？你的提示词对付得了这种
#    「压根不是个人信息」的输入吗？如果要改，你会改提示词还是改代码？
#   第9条完全不是简历内容，表现还行，其他都对了，但是姓名输出了""而不是null
#   我会改提示词，告诉模型什么内容不需要看
# 4. 你这次 JSON 模式里提示词写的是什么？试着把「json」这个词删掉再跑一条，
#    贴上报错原文，再解释为什么服务商要设这道关。
#   你是信息抽取助手，只输出 JSON。字段：{FIELDS}
#   BadRequestError: Error code: 400 - Prompt must contain the word 'json'",
#   in some form to use 'response_format' of type 'json_object'.
#   服务商必须确认用户是否真的需要输出json格式，而不是误触了json模式开关
