"""Day 22：从工具回合走到有状态、有出口的 Agent 循环，完全离线。

直接运行时按「这是什么 → 为什么 → 场景 → 代码 → 注意」逐节讲解。
fake_chat、execute_tool、show_result 也供同目录的练习文件导入。
"""

import json


def section(title: str) -> None:
    """打印一节的标题。"""
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


def fake_chat(messages: list[dict], *, scenario: str = "normal") -> dict:
    """接收消息历史；返回固定情境的一条 assistant 字典，代替模型请求。"""
    if scenario not in {"normal", "direct", "error"}:
        # 不认识的情境要立刻报错，避免下面按错误的规则继续生成回复。
        raise ValueError(f"未知情境：{scenario}")
    if scenario == "direct":
        # 演示“不调用工具，直接回答”：空 tool_calls 表示循环可以结束。
        return {
            "role": "assistant",
            "content": "你好！",
            "tool_calls": [],
        }

    # 从消息历史中逐条找出工具结果；只有 role='tool' 才算一次观察。
    observations = []
    for item in messages:
        if item["role"] == "tool":
            # 只收集本地工具回填的结果，后面用它判断算到了哪一步。
            observations.append(item)
    if scenario == "error":
        # 故意每次都给错误参数，用来检查 Agent 会不会按步数上限停下。
        arguments = '{"left": "三", "right": 4}'
        summary = "教学脚本：故意重复错误参数，检查程序会不会停。"
    elif not observations:
        # 还没有工具结果：第一步先算 3 箱、每箱 4 件，一共有多少件。
        arguments = '{"left": 3, "right": 4}'
        summary = "教学脚本：先算 3 箱、每箱 4 件，一共多少件。"
    elif len(observations) == 1:
        # 已有第一步的件数：读出它，再请求乘以每件 8 元。
        try:
            count = float(observations[-1]["content"])
        except ValueError:
            # 第一条观察不是数字，无法继续计算；返回说明并停止点工具。
            return {
                "role": "assistant",
                "content": "没有得到有效件数，无法继续计算。",
                "tool_calls": [],
            }
        # json.dumps(对象, ensure_ascii=False)：把参数变成 JSON 字符串，保留中文。
        arguments = json.dumps({"left": count, "right": 8}, ensure_ascii=False)
        summary = "教学脚本：用刚收到的件数乘以每件 8 元。"
    else:
        # 已有两条工具结果：第二条是总价，可以给出最终答复。
        return {
            "role": "assistant",
            "content": f"这批商品总价为 {observations[-1]['content']} 元。",
            "tool_calls": [],
        }
    return {
        "role": "assistant",
        "content": summary,
        "tool_calls": [
            {
                "id": f"call_{len(observations) + 1}",
                "type": "function",
                "function": {"name": "multiply", "arguments": arguments},
            }
        ],
    }


def execute_tool(name: str, arguments: str) -> str:
    """执行教学用乘法；输入 JSON 字符串，返回可回填的结果或错误文字。"""
    try:
        if name != "multiply":
            # 这个教具只提供乘法；别的工具名不能执行。
            raise ValueError(f"未知工具：{name}")
        # json.loads(字符串)：将模型给的 JSON 参数解析成 Python 对象。
        data = json.loads(arguments)
        if not isinstance(data, dict) or set(data) != {"left", "right"}:
            # 参数必须是字典，而且只能有 left 和 right 两个键。
            raise ValueError("参数必须恰好包含 left、right")
        # 逐个检查 left、right 的值；bool 也不能冒充数字。
        for value in data.values():
            if type(value) not in (int, float):
                # 值不是整数或浮点数时，拒绝执行乘法。
                raise ValueError("left、right 必须是数字")
        return str(data["left"] * data["right"])
    except (ValueError, TypeError) as error:
        return f"工具执行失败：{type(error).__name__}: {error}"


def show_result(result: dict) -> None:
    """打印练习返回的状态、轨迹和消息，供学员核对观察题。"""
    print(f"停止原因：{result['stop_reason']}")
    print(f"模型请求次数：{result['steps']}")
    print(f"最终答案：{result['answer']!r}")
    print("逐步轨迹：")
    for event in result["trace"]:
        print(json.dumps(event, ensure_ascii=False))
    print("完整消息历史：")
    for message in result["messages"]:
        print(json.dumps(message, ensure_ascii=False))


def demo_loop(max_steps: int) -> None:
    """用教学假模型演示两次相互依赖的工具调用，以及最终答复占用的一步。"""
    messages = [{"role": "user", "content": "3 箱商品，每箱 4 件，每件 8 元，总价？"}]
    for step in range(1, max_steps + 1):
        print(f"\n--- 第 {step} 次模型请求 ---")
        roles = []
        for item in messages:
            roles.append(item["role"])
        print(f"请求前历史角色：{roles}")
        decision = fake_chat(messages)
        messages.append(decision)
        print(f"assistant 返回：{decision}")
        if not decision["tool_calls"]:
            # 没有新的工具请求，这一轮就是最终答复，循环可以结束。
            print(f"停止原因：final_answer；答案：{decision['content']}")
            return
        for call in decision["tool_calls"]:
            function = call["function"]
            observation = execute_tool(function["name"], function["arguments"])
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": observation}
            )
            print(f"本地执行并回填：id={call['id']}，观察={observation}")
    print("停止原因：max_steps；答案：None（没有收到最终答复）")


def main() -> None:
    """像 Week 02 演示一样，先讲清每一块，再展示实际运行。"""
    section("1. 先认清 ReAct 循环里的三件事")
    print("这是什么：先决定下一步，再做行动，读取观察结果，然后继续决定。")
    print("为什么需要：第二次行动可能依赖第一次拿到的结果。")
    print("场景：3 箱商品，每箱 4 件，每件 8 元；先算件数，再算总价。")
    print("代码分工：fake_chat 代替模型作决定；execute_tool 在本地执行乘法。")
    print("注意：这里的假模型是固定 Python 规则，教学摘要也是手写的。")

    section("2. 先只看一次点单和一次观察")
    print("这是什么：assistant 的 tool_calls 是行动请求；tool 消息是执行后的观察。")
    print("为什么需要：下一次决定要看见这次执行得到的件数。")
    print("场景：第一单要算 3 × 4。下面两条确实调用了本文件里的函数。")
    print("代码：decision = fake_chat(messages)")
    print("代码：observation = execute_tool(name, arguments)")
    messages = [{"role": "user", "content": "3 箱商品，每箱 4 件，每件 8 元，总价？"}]
    # fake_chat(消息历史, scenario=情境)：固定教具，按历史决定下一条 assistant。
    decision = fake_chat(messages)
    call = decision["tool_calls"][0]
    # execute_tool(工具名, JSON 参数文本)：本地执行乘法，失败也返回文字。
    observation = execute_tool(call["function"]["name"], call["function"]["arguments"])
    print(f"assistant 点单：{call}")
    print(f"本地观察：{observation}")
    print("注意：12 是工具结果，还需要把它作为 tool 消息交回去。")

    section("3. 把一次回合放进循环")
    print("这是什么：每次请求后保存 assistant，执行工具并保存 tool，再请求下一次。")
    print("为什么需要：第二单的 left 要来自刚得到的 12，最后还要等模型答复。")
    print("场景：允许请求三次：算件数 → 算总价 → 得到最终答复。")
    print("代码：看下面 demo_loop 的 for 循环与 messages.append。")
    demo_loop(max_steps=3)
    print("注意：一次模型请求算一步；一次请求也可能带多个工具调用。")

    section("4. 同一个问题，只给两步会怎样")
    print("这是什么：由 Python 的 max_steps 决定最多请求几次。")
    print("为什么需要：工具报错或模型反复调用时，程序也必须能停。")
    print("场景：第二步算出了 96 元，但第三次请求还没发生。")
    print("代码：把同一个 demo_loop 的 max_steps 从 3 改成 2。")
    demo_loop(max_steps=2)
    print("注意：工具结果是 96.0，不代表模型已经给出最终答复。")

    section("5. 接下来你做什么")
    print("第一步：看上面两次运行，指出 assistant 点单和 tool 观察各在哪里。")
    print("第二步：打开 day22_agent_loop_exercises.py，把顶部那条注释的 import 打开。")
    print("第三步：按函数 docstring 的 1～5 步自己写 run_agent；先实现直接回答。")
    print("第四步：补工具回填和 trace，再处理达到 max_steps 的出口。")
    print("第五步：运行练习，对照四组输出，最后填写文件末尾的观察题。")
    print("注意：练习写的是你自己的循环；这里的教具只给它固定输入。")


if __name__ == "__main__":
    main()
