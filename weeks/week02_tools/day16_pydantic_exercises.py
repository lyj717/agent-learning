"""Day 16 练习：用 Pydantic 把「值不对」拦住，失败了让模型自己改一次。

跑法（默认离线：拿写死的脏数据自测，不花钱）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_exercises.py

真跑（把难抽的文本喂给模型，看它能不能自己改对；要网络，最多 3 次调用）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_exercises.py --live

做完把结果抄进交付物：weeks/week02_tools/day16_脏数据处理记录.md

本文件已实现的三部分：
    第 1 题  PersonExtract 的两处校验器 —— 空串归一成 None、电话必须是 11 位数字
    第 2 题  errors_to_hint()      —— 把 Pydantic 的报错翻译成「给模型看的一句话」
    第 3 题  extract_with_retry()  —— 把前两件串成一个循环：抽 → 校验 →
                                      不过就把错误回填再抽一次

本目录里今天会用到的其它文件（AI 搭的，你只管用）：

    llm_client.py       共用的请求层。**这是 Day 16 新加的文件**，
                        里面是把 Week 01 你写的 chat_cli/llm.py 那套样板代码搬过来的，
                        一共三个东西：
                          · make_client()
                              建一个 openai 客户端：密钥和 base_url 读仓库根目录的
                              .env，带 60 秒超时，并关掉 SDK 自带的 2 次重试
                              （Day 12 的坑：不关的话一次调用会悄悄变成好几次）。
                              它的前身就是 chat_cli/llm.py 里的 _make_client——
                              搬过来之后去掉了下划线，因为它现在要**给外面用**。
                          · chat_json(messages, *, client=None, model=None,
                                      max_tokens=2048) -> (原始文本, finish_reason)
                              发一次请求，自动开 JSON 模式。注意它**只负责发**：
                              不解析 JSON、不做校验——解析和校验是上层的事。
                              extract_with_retry() 用它请求模型。
                          · require_api_key()  读密钥，缺了就抛异常（make_client 内部用）

                        怎么拿到它们：本文件顶部已经写好了
                            from llm_client import chat_json, make_client
                        （PyCharm 若标红说找不到 llm_client，是它没把本目录当源码根：
                          右键 week02_tools → Mark Directory as → Sources Root。
                          命令行运行不受影响。）

    day16_pydantic_demo.py        讲解脚本：Pydantic 校验 + 失败重试（AI 搭，你跑）
    day16_validator_decorator_demo.py  加餐：那两个装饰器干嘛用（5 个小实验）
    day16_regex_demo.py           加餐：re.fullmatch 与「11 位数字」的坑
    day16_脏数据处理记录.md        学员的运行记录
"""

import json
import sys
from pathlib import Path

from llm_client import chat_json, make_client
from pydantic import BaseModel, Field, ValidationError, field_validator

ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv

# 第 3 题真跑用的三条文本。它们不是随便挑的：
#   ① 电话里带横线——看模型会不会自己规整成 11 位数字
#      （实测：提示词里写清「phone 是 11 位手机号」时，它第一次就规整好了，
#       所以「重试」这条分支**不一定**会被触发——见下面 --live 里的注入式验证）
#   ② 一条完整的个人信息——用来确认「顺利的一轮」长什么样
#   ③ 昨天的第 9 条——压根没有姓名，看它填 null 还是空串
DIRTY_TEXTS = [
    "我是王芳，联系方式 138-0013-8000，在上海负责华东区销售。",
    "入职登记表——姓名：欧阳娜娜；联系电话：13500009999；现居：广州；岗位：运维工程师。",
    (
        "受强冷空气影响，预计明天本市气温将下降 8 到 10 摄氏度，"
        "请市民注意添衣保暖。（本条为气象台发布）"
    ),
]

# 注入式验证用的「假返回」：电话故意写成带横线的，怎么都过不了 11 位数字那一关。
# 有了它，重试分支就一定跑得到（不用赌模型会不会犯错）。
INJECTED_REPLY = (
    '{"name": "王芳", "phone": "138-0013-8000", "city": "上海", "job": "销售"}'
)
hint = (
    "name（姓名，字符串）、phone（手机号，字符串）、"
    "city（城市，字符串）、job（岗位，字符串）"
)


# ============================================================
# 两个 validator 的来龙去脉（@field_validator + @classmethod、before/after）
# 见 day16_validator_decorator_demo.py；「11 位数字」为什么挡不住全角数字
# 见 day16_regex_demo.py 第 5 节
# ============================================================


class PersonExtract(BaseModel):
    """从一段文本里抽出来的一个人：四个字段都可能缺失，缺失就记 None。"""

    name: str | None = Field(default=None, description="姓名；原文没有就填 null")
    phone: str | None = Field(
        default=None, description="11 位手机号；原文没有就填 null"
    )
    city: str | None = Field(default=None, description="城市；原文没有就填 null")
    job: str | None = Field(default=None, description="岗位；原文没有就填 null")

    @field_validator("name", "phone", "city", "job", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        """把空串和「未知」这类的占位符归一成 None（在类型校验之前跑）。"""
        if isinstance(value, str):
            text = value.strip()
            if text in {"", "未知", "null", "N/A", "无"}:
                return None
            return text
        return value

    @field_validator("phone")
    @classmethod
    def phone_must_be_11_digits(cls, value):
        """电话要么是 None，要么是 11 位数字；不合规就抛 ValueError。"""
        if value is not None and not (value.isdigit() and len(value) == 11):
            raise ValueError("手机号必须是11位数字！")
        return value


def errors_to_hint(error: ValidationError) -> str:
    """把 Pydantic 的报错整理成一句给模型看的话，一条错一行。"""
    lines = []
    for item in error.errors():
        loc = ".".join(str(part) for part in item["loc"]) or "整体"
        # 版式：横线后留空格、全角冒号分隔；值用 !r 显示——带引号才看得出首尾有没有空格
        lines.append(f"- 字段 {loc}：{item['msg']}（收到的值：{item['input']!r}）")
    return "\n".join(lines)


def extract_with_retry(
    text: str, *, attempts: int = 2, first_reply: str | None = None
) -> PersonExtract | None:
    """抽一次；不合格就把错误回填给模型再试，试满 attempts 次仍不合格返回 None。"""
    client = make_client()
    messages = [
        {"role": "system", "content": f"你是信息抽取助手，只输出 JSON。字段：{hint}"},
        {"role": "user", "content": f"从下面这段话里抽取字段，输出 JSON：{text}"},
    ]
    for round_no in range(attempts):
        if round_no == 0 and first_reply is not None:
            raw = first_reply
        else:
            raw, _ = chat_json(messages, client=client)  # 其余圈真发请求
        try:
            return PersonExtract.model_validate_json(raw)
        except ValidationError as error:
            messages = [
                *messages,
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": f"你刚才的输出没通过校验：\n{errors_to_hint(error)}\n"
                    "请只输出修正后的 JSON，缺失的字段填 null。",
                },
            ]
    return None


# 主程序里的四条脏数据。故意用「字符串形式的 JSON」而不是 dict，
# 因为 model_validate_json 收到的就是一段文本——和模型返回的东西一样。
DIRTY_CASES = [
    ("空串当缺失", '{"name": "", "phone": null, "city": "北京", "job": null}'),
    (
        "电话带了横线",
        '{"name": "王芳", "phone": "138-0013-8000", "city": "上海", "job": "销售"}',
    ),
    (
        "电话是数字",
        '{"name": "张伟", "phone": 18600001111, "city": "北京", "job": "数据分析师"}',
    ),
    ("JSON 本身坏了", '{"name": "李娜"'),
]


if __name__ == "__main__":
    print("=== 第 1 题：你的模型能不能拦住四条脏数据 ===")
    print("  模型结构：")
    print("  " + json.dumps(PersonExtract.model_json_schema(), ensure_ascii=False))
    print()
    for label, raw in DIRTY_CASES:
        print(f"  ── {label}：{raw}")
        try:
            person = PersonExtract.model_validate_json(raw)
            print(f"     校验通过：{person.model_dump()}")
        except ValidationError as error:
            # error.errors()：把报错拆成结构化的一条条记录，
            # 每条形如 {'type': 'value_error', 'loc': ('phone',), 'msg': '...', 'input': ...}
            item = error.errors()[0]
            where = ".".join(str(part) for part in item["loc"]) or "整体"
            print(f"     校验失败：{item['type']} @ {where}｜{item['msg']}")

    print("\n=== 第 2 题：把报错变成给模型看的话 ===")
    for label, raw in DIRTY_CASES[1:]:
        try:
            PersonExtract.model_validate_json(raw)
            print(f"  ── {label}：这条居然通过了，说明第 1 题还漏了规矩")
        except ValidationError as error:
            print(f"  ── {label}：")
            print(errors_to_hint(error))

    print("\n=== 第 3 题：真抽三条难抽的文本 ===")
    if not LIVE:
        print("  这题要联网、会花钱，所以默认不跑。想跑就加 --live：")
        print(
            "  .venv\\Scripts\\python.exe "
            "weeks\\week02_tools\\day16_pydantic_exercises.py --live"
        )
        print("  跑完之后，把「第一次怎么错的、重试后改没改对」抄进交付物")
    else:
        for index, text in enumerate(DIRTY_TEXTS, start=1):
            print(f"  ── 第 {index} 条：{text[:30]}……")
            person = extract_with_retry(text)
            if person is None:
                print("     最终没抽出合法结果（返回 None）")
            else:
                print(f"     最终结果：{person.model_dump()}")

        print("\n  ── 注入式验证：这一次必定会走重试 ──")
        print(f"     假装模型第一次返回：{INJECTED_REPLY}")
        person = extract_with_retry(DIRTY_TEXTS[0], first_reply=INJECTED_REPLY)
        if person is None:
            print("     重试后还是没过（返回 None）——把这条现象写进交付物")
        else:
            print(f"     重试后拿到：{person.model_dump()}")
        print("     对照上面三条：真实模型一次就对，是「提示词写得不错」")
        print("     还是「这条本来就不难」？你可以在交付物里说说自己的判断。")
