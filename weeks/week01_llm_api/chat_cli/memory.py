"""简易长期记忆：把你告诉它的事实存到本地文件，下次启动还记得。

为什么要单独一个文件：模型自己不留任何东西，所谓「记忆」是你存在外面、每次重新
喂回去的东西。这一层只管「存 / 取 / 拼成提示词」——不碰网络、不打印，所以好测。
"""

from pathlib import Path

# 写 load_facts / add_fact 的时候，把下面这行的注释去掉（现在还没有代码用它）
# import json


def load_facts(path: Path) -> list[str]:
    """从文件里读回事实列表。

    要做的：
        1. 文件不存在 → 返回空列表（第一次用的时候就是这样，不是错误）
        2. 文件存在 → 用 json 读出来，返回里面的列表
        3. 文件坏了（不是合法 JSON、或者内容不是列表）→ 别让程序崩：
           当成「还没有记忆」，返回空列表

    期望结果：
        没存过任何东西时：load_facts(路径) == []
        存过 ["我叫刘小明"] 之后：load_facts(路径) == ["我叫刘小明"]
        往文件里写一段「这不是 json」再读：返回 []，不抛异常

    提示：json.loads(文本) 把 JSON 字符串变回 Python 对象；
          文件读写在 Day 5 讲过：path.read_text(encoding="utf-8")。
    """
    raise NotImplementedError("load_facts 还没写")


def add_fact(path: Path, text: str) -> None:
    """把一条新事实追加进文件（文件不存在就新建）。

    要做的：
        1. 先用 load_facts(path) 拿到现有的事实
        2. 把 text 追加进去（要不要去重、要不要去掉首尾空格，你自己定，
           定了就在 docstring 里写清楚）
        3. 用 json 写回文件

    期望结果：
        add_fact(路径, "我叫刘小明") 之后，load_facts(路径) == ["我叫刘小明"]
        再 add_fact(路径, "我在学 Agent")，两条都在，顺序不变
        事实里的中文要原样写进文件，不能变成 \u5218 这种转义

    提示：json.dumps(对象, ensure_ascii=False, indent=2) —— ensure_ascii=False
          是关键，不然中文会被转义，文件打开没法看。
    """
    raise NotImplementedError("add_fact 还没写")


def compose_system(base_system: str | None, facts: list[str]) -> str | None:
    """把「人设 + 记得的事实」拼成一条 system 提示词。

    要做的：
        1. 没有事实 → 原样返回 base_system（是 None 就返回 None）
        2. 有事实 → 把人设和事实拼成一段，比如：
               你是一个只说一句话的助手。
               你记得关于用户的这些事实：
               - 我叫刘小明
               - 我在学 Agent
        3. 只有事实、没有 base_system 时，也要能拼出来

    期望结果：
        compose_system(None, []) is None
        compose_system("人设", []) == "人设"
        "刘小明" in compose_system("人设", ["我叫刘小明"])

    提示：为什么拼进 system 而不是历史——system 不参与裁剪（trim 只动历史）、
          /clear 也清不掉它，所以「记忆」每轮都能重新喂进去。
    """
    raise NotImplementedError("compose_system 还没写")
