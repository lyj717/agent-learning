"""Day 8 练习：消息角色与参数感知（自己动手，别抄）。

先跑完 day08_roles_demo.py，再来做这里的题：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_exercises.py

三个考点：
  - messages 是一个列表，每条是 {"role": ..., "content": ...}
  - 三种角色：system 设规矩、user 提问、assistant 模型的历史回答
  - temperature 低=稳、高=散，不同任务选不同的值

第 1、2、3 题是纯逻辑，离线就能做。做完再回答文件末尾的自测题。
卡住就按 notes/卡住了怎么办.md 里的六招走，还不行再问我。
"""


def build_conversation(
    system_prompt: str, turns: list[tuple[str, str]]
) -> list[dict[str, str]]:
    """第 1 题：把「人设 + 若干轮问答」拼成一个 messages 列表。

    要做的：
        1. 先放一条 {"role": "system", "content": system_prompt}
        2. 再按顺序把 turns 里每一轮拼进去
           turns 里每一项是一个 (用户问, 模型答) 的二元组
        3. 每一轮产出两条消息：先 user，后 assistant

    期望结果：
        build_conversation("只说一句话", [("你好", "你好呀。")])
        == [
            {"role": "system", "content": "只说一句话"},
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好呀。"},
        ]

    提示：for question, answer in turns: 一次就把二元组拆开了；
          往列表里加东西用 append。
    """
    raise NotImplementedError("第 1 题还没写")


def append_turn(
    messages: list[dict[str, str]], question: str, answer: str
) -> list[dict[str, str]]:
    """第 2 题：把新的一轮问答追加到已有 messages 末尾，返回新列表。

    要做的：
        1. 先复制一份传入的列表（别就地改别人的列表）
        2. 追加一条 user（question）和一条 assistant（answer）
        3. 返回复制并追加后的新列表

    期望结果：
        msgs = [{"role": "system", "content": "只说一句话"}]
        new = append_turn(msgs, "在吗", "在的")
        len(msgs) == 1     # 原来的列表没被动
        len(new) == 3

    提示：new = list(messages) 是浅拷贝，这里够用。
          这题就是 Day 10「多轮对话」的雏形。
    """
    raise NotImplementedError("第 2 题还没写")


def pick_temperature(task: str) -> float:
    """第 3 题：按任务类型挑一个合理的 temperature。

    要做的：
        1. task 会传进来 "抽取" / "工具调用" / "起名" / "写文案" / "闲聊" 之一
        2. 返回一个浮点数：
             需要稳定、可复现的任务 -> 0.0 ~ 0.3
             需要多样、有创意的任务 -> 0.8 ~ 1.2
        3. 传了别的值，给一个保守的默认温度

    期望结果（这只是形状示例，具体值你自己定）：
        pick_temperature("抽取") <= 0.3
        pick_temperature("起名") >= 0.8

    提示：先按自己的判断填；跑完 day08_temperature_demo.py 之后，
          再回来看看要不要改——那时候你手里有真实数据了。
    """
    raise NotImplementedError("第 3 题还没写")


if __name__ == "__main__":
    print("=== 第 1 题：拼一段两轮对话 ===")
    conversation = build_conversation(
        "你是一个只说一句话的技术助教。",
        [
            ("什么是流式输出？", "边生成边发送，让你更快看到第一批字。"),
            ("那它省时间吗？", "不省总时间，省的是你等第一句话的时间。"),
        ],
    )
    for message in conversation:
        print(f"  {message}")

    print("\n=== 第 2 题：往历史里追加一轮 ===")
    history = [{"role": "system", "content": "你是一个只说一句话的技术助教。"}]
    new_history = append_turn(history, "在吗？", "在的。")
    print(f"  原列表长度：{len(history)}，新列表长度：{len(new_history)}")
    print("  预期：原列表长度 1、新列表长度 3（对不上就是这题没做对）")
    for message in new_history:
        print(f"  {message}")

    print("\n=== 第 3 题：挑温度 ===")
    for task in ["抽取", "工具调用", "起名", "写文案", "闲聊", "别的"]:
        print(f"  {task}: {pick_temperature(task)}")

    print("\n=== 做完这三题，去跑 temperature 实验并填交付物 ===")
    print(
        "  .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_temperature_demo.py"
    )
    print("  weeks\\week01_llm_api\\day08_参数对比记录.md")


# ============================================================
# 现象与原因（做完之后填，用自己的话）
# ============================================================
#
# 1. 同一个问题在 temperature=0 和 1.5 下各跑 5 次，分别得到几种不同答案？
#    0 是：
#    1.5 是：
#    和你的预期一致吗？不一致的话，你觉得原因可能是什么？
#
# 2. 你要做一个「从简历里抽出姓名和电话」的功能，会选哪个温度？为什么？
#
# 3. 你要做一个「给新产品起 10 个名字」的功能，会选哪个温度？为什么？
#
# 4. 为什么 history 越长，每次请求越贵？（提示：想一想你每次到底发了什么出去）
