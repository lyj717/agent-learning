"""Day58 演示二：裁判输出先解析、再校验——模型给的是文本，不是现成的字典。

模型经常把 JSON 包在 Markdown 代码块里，或在前后加一句话；字段也可能缺失、
类型写错。本演示用几个原始输出说明：先取 JSON，再逐项校验，失败要报清楚。
学完应能写出严格的解析函数，不靠猜；练习 B 有 10 组情形。
全部离线，不调用模型。
"""

import json


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def main() -> None:
    """按用途、四个原始输出、校验规则、边界的顺序讲一次解析。"""
    say("Day58 的裁判返回的是一段文本。你可能拿到纯 JSON，也可能拿到带代码块的文本。")
    say("本演示说明：为什么先 json.loads、再检查键和类型，失败时该保留什么。")
    say("学完应能写出严格解析，而不是「能解析就用」；练习 B 会逐组检查。")

    say("\n一、这是什么")
    say(
        "解析 = 把模型返回的字符串变成 Python 字典；校验 = 检查键是否齐全、类型是否正确。"
    )
    say("两步分开：JSON 语法对了，内容仍可能是错的。")

    say("\n二、场景一：纯 JSON，一次就能解析")
    raw_ok = '{"answer_ok": true, "citation_ok": null, "reason": "回答与原文一致。"}'
    data = json.loads(raw_ok)
    say(f"原文={raw_ok}")
    say(f"解析结果={data}")
    say(f"键={sorted(data)}；answer_ok 类型={type(data['answer_ok']).__name__}")
    say("这一步只证明「语法是 JSON」，还没证明三个键都在、类型都对。")

    say("\n三、场景二：包在 Markdown 代码块里")
    raw_fenced = (
        '```json\n{"answer_ok": true, "citation_ok": null, "reason": "一致。"}\n```'
    )
    stripped = raw_fenced.strip()
    stripped = stripped.removeprefix("```json").removesuffix("```").strip()
    data = json.loads(stripped)
    say(f"原文={raw_fenced!r}")
    say(f"去掉首尾代码块后={stripped}")
    say(f"解析结果={data}")
    say("先判断首尾是不是代码块，再去掉；不要对整段文本直接 json.loads。")

    say("\n四、场景三：JSON 前后带解释文字")
    raw_prose = '判断如下：{"answer_ok": true, "citation_ok": null, "reason": "一致。"}'
    say(f"原文={raw_prose}")
    try:
        json.loads(raw_prose)
    except json.JSONDecodeError as error:
        say(f"直接解析报错：{type(error).__name__}: {error}")
    say("这时应该报错并保留原文，而不是用正则去抠第一个花括号。")
    say("抠出来的片段可能是解释文字里的示例，解析成功但内容不是裁判结论。")

    say("\n五、场景四：语法对，但内容不合格")
    data = {"answer_ok": "true", "citation_ok": None, "reason": "一致。"}
    expected = {"answer_ok", "citation_ok", "reason"}
    say(f"数据={data}")
    say(
        f"键齐全={set(data) == expected}；answer_ok 是 bool={type(data['answer_ok']) is bool}"
    )
    say('字符串 "true" 不是 True；类型不对要报错，不能悄悄转换。')
    say("同理，多出 confidence 之类的键也算不合格：schema 说三个键就是三个键。")

    say("\n六、校验清单（练习 B 会逐组检查）")
    say("1. 输入不是字符串 → TypeError。")
    say(
        "2. 去掉首尾空白和可选的 ```json 代码块后，JSON 语法必须正确，否则 ValueError。"
    )
    say("3. 顶层必须是字典，键恰好是 answer_ok、citation_ok、reason。")
    say(
        "4. answer_ok 必须是 bool；citation_ok 必须是 bool 或 None；reason 必须是非空字符串。"
    )
    say("5. 返回新字典，不改输入；失败时保留原始文本供排查。")

    say("\n七、注意什么")
    say("1. 不要自动修复：缺键就补默认值，会把「裁判没答」伪装成「裁判判了」。")
    say("2. finish_reason 是 length 时，先看是不是输出被截断，再谈 JSON 语法。")
    say("3. 失败要保存原文、模型名、用量和耗时；只留一句「解析失败」没法排查。")
    say(
        "4. 重试要单独计数；同一份输出重试多次仍失败，说明 prompt 或模型需要改，不是运气问题。"
    )

    say(
        "\n下一步：实现练习 A 的 build_judge_messages，再实现 B 的 parse_judge_verdict；"
    )
    say("两部分都通过后，才按记录里的预算跑 --part live。")


if __name__ == "__main__":
    main()
