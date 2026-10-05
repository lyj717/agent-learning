"""Day 8 练习：消息角色与参数感知。

跑法：.venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_exercises.py
"""


def build_conversation(
    system_prompt: str, turns: list[tuple[str, str]]
) -> list[dict[str, str]]:
    """把「人设 + turns 里的每轮问答」按顺序拼成一个 messages 列表。

    每一轮产出两条消息：先 user，后 assistant。
    """
    conversation = [{"role": "system", "content": system_prompt}]
    for question, answer in turns:
        conversation.append({"role": "user", "content": question})
        conversation.append({"role": "assistant", "content": answer})
    return conversation


def append_turn(
    messages: list[dict[str, str]], question: str, answer: str
) -> list[dict[str, str]]:
    """不改原列表，返回「追加了一轮问答」的新列表。

    这是多轮对话的雏形：每次往历史里加一轮。
    """
    new = list(messages)
    new.append({"role": "user", "content": question})
    new.append({"role": "assistant", "content": answer})
    return new


def pick_temperature(task: str) -> float:
    """按任务类型返回一个合适的 temperature。

    需要稳、可复现的任务给低温；需要多样的任务给高温；认不出来的给保守值。
    """
    if task in {"抽取", "工具调用"}:
        return 0.15
    if task in ["起名", "写文案", "闲聊"]:
        return 1.00
    return 0.60


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
#    0 是：3
#    1.5 是：5
#    和你的预期一致吗？不一致的话，你觉得原因可能是什么？
#    不一致。原因：这个模型默认开着思考模式，而官方文档写明 temperature
#    「思考模式下不生效」——所以设成 0 也不保证每次一样。
#    （补充实验见 day08_参数对比记录.md 的观察 1。）
# 2. 你要做一个「从简历里抽出姓名和电话」的功能，会选哪个温度？为什么？
#    0.2，抽取需要可复现，需要稳定输出
# 3. 你要做一个「给新产品起 10 个名字」的功能，会选哪个温度？为什么？
#    1.2，这个功能需要发挥创意（在题目给的 0.8~1.2 区间里；越界就开始散了）
# 4. 为什么 history 越长，每次请求越贵？（提示：想一想你每次到底发了什么出去）
#     因为模型并不是有记忆，而是在收到新请求时让历史记录全部看一遍，token花费自然更多
