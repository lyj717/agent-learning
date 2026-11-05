"""Day50：看清字典→JSON 字符串→文件中的行→字典，为服务日志的保存与查询准备。

dumps/loads 沿用 Day40 的用法；本课新增的是每条事件怎样单独占一行并追加到日志。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def demonstrate_jsonl(run_dir: Path) -> None:
    """在本次新目录逐步展示转换、追加、逐行解析与筛选；不提供练习整合实现。"""
    print("\n一、是什么、为什么：一次阶段变化记作一个字典，日志会不断收到新事件。")
    print("JSONL 是一种存放约定：一条事件先转成 JSON 字符串，再单独写成文件的一行。")
    print("场景：先收到‘检索成功’，随后收到‘生成失败’，希望追加保存并找回失败事件。")
    print("这里两条事件均为 AI 人工教具，没有真正检索或调用模型。")

    print("\n二、先看旧知识：dumps 仍然只是把 Python 对象转成 str")
    event = {"stage": "retrieve", "state": "ok"}
    print("执行：event = {'stage': 'retrieve', 'state': 'ok'}")
    print(f"原值：{event}；类型：{type(event).__name__}")
    print("执行：text = json.dumps(event, ensure_ascii=False)")
    # dumps(可序列化的 Python 对象, ensure_ascii=False)：返回 JSON 字符串，不写文件。
    text = json.dumps(event, ensure_ascii=False)
    print(f"返回类型：{type(text).__name__}")
    print("print(text) 看到的内容：", text)
    # repr(值)：返回便于检查的表示，让字符串外层引号、换行转义等可见。
    print("repr(text) 看到的字符串边界：", repr(text))
    print("字典看着也有大括号，字符串里面也可以有大括号；判断类型要看 type。")

    print("\n三、同一个 dumps，只换 indent 参数，看行数怎样变化")
    print("Day40 组装模型消息时用过：json.dumps(event, ensure_ascii=False, indent=2)")
    pretty_text = json.dumps(event, ensure_ascii=False, indent=2)
    print("加 indent=2 的实际内容：")
    print(pretty_text)
    print(
        "类型：",
        type(pretty_text).__name__,
        "；实际行数：",
        len(pretty_text.splitlines()),
    )
    print("本次日志采用：json.dumps(event, ensure_ascii=False)，省略 indent")
    print(text)
    print("类型：", type(text).__name__, "；实际行数：", len(text.splitlines()))
    print("两次都是 str，表达同一个对象；indent=2 为排版插入换行和缩进。")
    print("ensure_ascii=False 只让中文保持可读，不负责控制行数或保存文件。")

    print("\n四、到这里还没有写文件：write 才负责保存，换行也由我们补")
    path = run_dir / "events.jsonl"
    print("准备写入的文件：", path)
    print("dumps 已调用，文件存在吗？", path.exists())
    print("执行：with path.open('a', encoding='utf-8') as stream:")
    print('          stream.write(text + "\\n")')
    # Path.open("a", encoding="utf-8")：返回追加用的文件对象；文件不存在时创建。
    # "a" 会把后续内容加在末尾；with 结束时关闭文件。"w" 会清空已有内容。
    with path.open("a", encoding="utf-8") as stream:
        # write(字符串)：把字符写进文件；这里显式补一个实际换行，分隔记录。
        stream.write(text + "\n")
    # read_text(encoding="utf-8")：读取文件全部文字，返回 str，不自动解析 JSON。
    first_content = path.read_text(encoding="utf-8")
    print("写入后文件存在吗？", path.exists())
    print("现在文件内容的 repr：", repr(first_content))
    print('末尾的 \\n 来自 text + "\\n"，不是 dumps 自动添加的。')

    print("\n五、再追加一条：原来那一行仍在，新事件放到第二行")
    second_event = {"stage": "generate", "state": "error"}
    second_text = json.dumps(second_event, ensure_ascii=False)
    print("第二个字典：", second_event)
    print("执行同样的 open('a') 和 write(second_text + 换行)")
    with path.open("a", encoding="utf-8") as stream:
        stream.write(second_text + "\n")
    file_content = path.read_text(encoding="utf-8")
    # splitlines()：把实际换行分开的文字拆成 list[str]，不保留行末换行符。
    lines = file_content.splitlines()
    print("文件里的实际行数：", len(lines))
    for number, line in enumerate(lines, start=1):
        print(f"文件第 {number} 行：{line}")
    print("第一行没被覆盖；两行分别是一条完整 JSON。这种保存方式才叫 JSONL。")
    print("两行外面没有包成一个 JSON 数组，所以要逐行解析。")

    print("\n六、读回时先得到 str，再用 loads 恢复 dict，之后才能按字段筛选")
    events: list[dict] = []
    for number, line in enumerate(lines, start=1):
        print(f"读取第 {number} 行：类型={type(line).__name__}")
        print("执行：restored = json.loads(line)")
        # loads(JSON 字符串)：解析为 Python 对象；这里每行保存的是对象，所以得到 dict。
        restored = json.loads(line)
        print(f"解析后：{restored}；类型={type(restored).__name__}")
        print(f"现在可取字段：restored['state'] = {restored['state']}")
        events.append(restored)

    print("执行：逐个检查 event['state'] == 'error'")
    failed_events: list[dict] = []
    for saved_event in events:
        if saved_event["state"] == "error":
            failed_events.append(saved_event)
            print(f"找到失败阶段：{saved_event['stage']}")
    print(f"一共读回 {len(events)} 条事件，筛出 {len(failed_events)} 条失败。")

    print("\n七、注意边界")
    print(
        "dumps：对象→JSON 字符串；write：字符串→文件；loads：JSON 字符串→Python 对象。"
    )
    print("今天的新内容是存放方式：每条事件独立序列化、补换行、追加保存，再逐行读回。")
    print(
        "不要给 JSONL 的单条事件加 indent=2 这样的多行排版，会把一条记录拆成多个实际行。"
    )
    print("dumps 不会自动隐藏密钥；写哪些字段要先选好，异常原文也可能带敏感内容。")


def main() -> None:
    """说明阶段用途，再调用已有留证环境运行教学步骤。"""
    print("Week07 要把已有问答做成能排错的服务；本演示只讲阶段日志怎样保存和读回。")
    print("学完能分清‘转换字符串’和‘写文件’，之后用同样格式保存 A/B 的事件。")
    print(
        "从 demonstrate_jsonl 函数第一行顺读即可；main 以下调用是已有的运行留证环境。"
    )
    # run_logged 是沿用的留证工具：提供本次独立目录，保存控制台、来源、配置及异常。
    run_logged(
        "jsonl_demo",
        demonstrate_jsonl,
        {"mode": "offline_teaching"},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY50_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
