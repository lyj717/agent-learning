"""Day 16 练习：用 Pydantic 把「值不对」拦住，失败了让模型自己改一次。

跑法（默认离线：拿写死的脏数据自测，不花钱）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_exercises.py

真跑（把难抽的文本喂给模型，看它能不能自己改对；要网络，最多 3 次调用）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_exercises.py --live

做完把结果抄进交付物：weeks/week02_tools/day16_脏数据处理记录.md
"""

import json
import sys
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

# 第 3 题要用 llm_client 里的这两个函数（就是昨天你写的建客户端 + 发 JSON 请求），
# 写完把下面这行的注释去掉：
# from llm_client import chat_json, make_client
#
# 顺带一提：PyCharm 万一给 llm_client 标红，右键 week02_tools 目录 →
# Mark Directory as → Sources Root（运行不受影响，Week 01 踩过同一个坑）。

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


# ============================================================
# 第 1 题：给四个字段补上「什么算合格」的规矩
#
# 字段声明和说明都给你了（它不是什么新东西——Day 15 的 FIELDS 就是这四个），
# 今天在这题里要写的只有下面两处 validator：
#   · blank_to_none：把空串、纯空白、"未知"、"N/A"、"无" 这类占位符
#     统一变成 None，而且必须在类型校验**之前**执行
#   · phone_must_be_11_digits：电话要么是 None，要么是 11 位数字，否则报错
#     （提示：value.isdigit() and len(value) == 11 就够，不用正则；
#      报错用 raise ValueError("你的话")，那句话会被原样回填给模型）
#     想用正则写也行：re.fullmatch(r"[0-9]{11}", value)（要 import re）——
#     两种写法都挡不住全角数字「１３８…」，为什么会这样见 day16_regex_demo.py 第 5 节
#
# 看不懂这两行装饰器（@field_validator + @classmethod）？
# 先跑 day16_validator_decorator_demo.py——专门为这两行做了 5 个实验，
# 只改一个地方、跑一次、看结果怎么变。
#
# 期望结果（对着主程序里那四条脏数据看）：
#   · {"name": ""}                 -> name 变成 None，校验通过
#   · phone="138-0013-8000"        -> 校验失败，报错里带上你自己写的话
#   · phone=18600001111（数字）    -> 校验失败，报 Input should be a valid string
#   · '{"name": "李娜"'（坏 JSON） -> 校验失败，type 是 json_invalid
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
        raise NotImplementedError("第 1 题：blank_to_none 还没写")

    @field_validator("phone")
    @classmethod
    def phone_must_be_11_digits(cls, value):
        """电话要么是 None，要么是 11 位数字；不合规就抛 ValueError。"""
        raise NotImplementedError("第 1 题：phone_must_be_11_digits 还没写")


def errors_to_hint(error: ValidationError) -> str:
    """第 2 题：把 Pydantic 的报错，变成一句**给模型看**的话。

    要做的：
      · 用 `error.errors()` 拿结构化报错：每一项是一个 dict，
        里面有 `type`（错在哪类）、`loc`（哪个字段）、`msg`（人话）、`input`（收到的值）
      · 每一项拼成一行，含「字段路径 / 问题 / 收到的值」三件事
      · loc 可能是空元组（整体 JSON 语法坏了），这时字段那一格写「整体」

    期望结果：主程序会把两条真实报错喂给它，打印出来应该像：
      - 字段 phone：Value error, 手机号必须是 11 位数字（收到的值：'138-0013-8000'）
      - 字段 整体：Invalid JSON ...（收到的值：'{"name": "李娜"'）
    提示：`".".join(str(part) for part in item["loc"]) or "整体"`——
          空元组在布尔判断里是假值，所以这句能同时处理两种 loc。
    """
    raise NotImplementedError("第 2 题还没写")


def extract_with_retry(
    text: str, *, attempts: int = 2, first_reply: str | None = None
) -> PersonExtract | None:
    """第 3 题：抽一次；值不合法就把错误回填给模型，再试一次。

    要做的：
      · 用 `make_client()` 建客户端（昨天那套样板代码，现在住在 llm_client 里）
      · 拼 messages：system 里**必须**出现「json」字样 + 字段说明，
        user 里放要抽的 text（没这个词，JSON 模式会被 400 拒收）
      · 用 `chat_json(messages, client=client)` 发请求，它返回 `(原始文本, finish_reason)`
      · 原始文本交给 `PersonExtract.model_validate_json(...)`：过了直接返回对象
      · 没过（ValidationError）：
          - 把**原始文本**当成 assistant 消息塞回对话（模型无状态，不塞它不知道改哪份）
          - 追加一条 user 消息，里面放 `errors_to_hint(error)`，
            并写明「请只输出修正后的 JSON，缺失字段填 null」
          - 再发一次、再校验
      · `attempts` 是总尝试次数（默认 2 = 第一次 + 重试一次）；
        用完还是不过就返回 None，**不要**把异常抛给上层

    `first_reply` 是留给**测重试分支**的口子：传了它，就跳过第一次真实请求，
    直接把它当成「模型的第一次返回」。为什么需要这个口子——真实模型大部分时候
    一次就对（实测三条全对），不注入脏数据，你写完可能一次重试都看不到。

    期望结果：
      · --live 跑 DIRTY_TEXTS 三条都不崩（可能一次就过，那就如实记下来）
      · --live 里那次注入式验证（first_reply 是带横线的号码）**必定**走重试，
        而且重试后应该能拿到合法结果
      · 遇到改不了的，返回 None 而不是抛异常
    提示：`attempts` 这个循环写成 `for _ in range(attempts):`，循环里 return，
          循环外面 return None——这样「上限」是天然有的，不会死循环。
    """
    raise NotImplementedError("第 3 题还没写")


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
            item = error.errors()[0]
            where = ".".join(str(part) for part in item["loc"]) or "整体"
            print(f"     校验失败：{item['type']} @ {where}｜{item['msg']}")
        except NotImplementedError as error:
            print(f"     还没写：{error}")

    print("\n=== 第 2 题：把报错变成给模型看的话 ===")
    for label, raw in DIRTY_CASES[1:]:
        try:
            PersonExtract.model_validate_json(raw)
            print(f"  ── {label}：这条居然通过了，说明第 1 题还漏了规矩")
        except ValidationError as error:
            print(f"  ── {label}：")
            print(errors_to_hint(error))
        except NotImplementedError as error:
            print(f"  ── {label}：还没写：{error}")

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


# ============================================================
# 现象与原因（做完之后填，用自己的话）
# ============================================================
#
# 1. 四条脏数据，哪几条被拦下了、哪几条被「悄悄修好」了？被修好的那两条，
#    分别是谁（哪个 validator）修的、在类型校验之前还是之后？
#
#
# 2. 电话是数字 `18600001111` 那条，Pydantic 报的是哪一类错？为什么它不
#    干脆帮你转成字符串（Week 00 见过这条边界）？
#    ——想验证的话，把类型改成 `int | str | None` 再跑一遍，看行为怎么变。
#
#
# 3. --live 那三条里，真正触发重试的有几条？一条都没有的话，说明什么——
#    是提示词写得太好，还是「这几条本来就不难」？注入式那一次，第一次的假返回
#    和重试后的返回差在哪？把两次文本都贴上来（这才是面试时能讲的现场）。
#
#
# 4. 校验通过就等于抽得对吗？从 Day 15 的 10 条里挑一个「格式合法但内容可疑」
#    的例子说明你的判断。
#
#
# 5. 如果你把重试上限从 1 次加到 3 次，会发生什么？什么时候该停、该怎么停？
#
#
