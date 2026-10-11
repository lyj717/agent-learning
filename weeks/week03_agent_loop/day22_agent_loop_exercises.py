"""Day 22：离线 Agent 循环，返回停止状态与逐步轨迹。"""

from day22_agent_loop_demo import execute_tool, fake_chat, show_result


def run_agent(question: str, *, max_steps: int = 3, scenario: str = "normal") -> dict:
    """运行有限步 Agent 循环，返回答复、停止原因、消息历史和轨迹。"""
    if type(max_steps) != int or max_steps < 1:
        raise ValueError("最大步数必须是正整数！")
    # 后面还会放 assistant 的 tool_calls 和 tool 的结果，不能只按第一条 user 消息推断类型。
    messages: list[dict] = [{"role": "user", "content": question}]
    trace = []
    for step in range(1, max_steps + 1):
        messages.append(fake_chat(messages, scenario=scenario))
        if not messages[-1]["tool_calls"]:
            trace.append({"step": step, "answer": messages[-1]["content"]})
            return {
                "answer": messages[-1]["content"],
                "stop_reason": "final_answer",
                "steps": step,
                "messages": messages,
                "trace": trace,
            }
        for call in messages[-1]["tool_calls"]:
            name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            observation = execute_tool(name=name, arguments=arguments)
            tool_call_id = call["id"]
            trace.append(
                {
                    "step": step,
                    "tool": name,
                    "arguments": arguments,
                    "tool_call_id": tool_call_id,
                    "observation": observation,
                }
            )
            messages.append(
                {"role": "tool", "content": observation, "tool_call_id": tool_call_id}
            )
    return {
        "answer": None,
        "stop_reason": "max_steps",
        "steps": step,
        "messages": messages,
        "trace": trace,
    }


if __name__ == "__main__":
    for label, scenario, limit, expected in [
        ("直接回答", "direct", 3, "final_answer；1 次请求；0 次工具；你好！"),
        ("正常完成", "normal", 3, "final_answer；3 次请求；2 次工具；总价 96.0 元"),
        ("提前截停", "normal", 2, "max_steps；2 次请求；2 次工具；answer=None"),
        ("持续报错", "error", 2, "max_steps；2 次请求；2 次工具失败；answer=None"),
    ]:
        print(f"\n=== {label} ===")
        print(f"预期：{expected}")
        question = (
            "你好" if scenario == "direct" else "3 箱、每箱 4 件、每件 8 元，总价？"
        )
        show_result(run_agent(question, max_steps=limit, scenario=scenario))
    print("\n=== 非法上限 ===")
    try:
        run_agent("你好", max_steps=0)
    except ValueError as error:
        print(f"已拒绝：{error}")
    else:
        print("未拒绝 0，请检查参数校验。")

# 现象与原因（学员的运行记录）
# 1. 正常完成时，第二次乘法实际收到什么参数？历史中哪条消息提供了件数？
#    我的观察："name": "multiply", "arguments": "{\"left\": 12.0, \"right\": 8}",
#    {"role": "tool", "content": "12", "tool_call_id": "call_1"}
# 2. max_steps=2 时最后的工具结果是什么？answer 是什么？为什么不能混用？
#    我的观察：工具结果是96.0，answer是None
#    我的解释：工具得到了结果，但模型还没有发送第三次请求就被截停了，所以得不到输出
# 3. 持续报错时，复制一条错误 observation。请求了几次，由哪段代码决定停止？
#    我的观察：请求了2次，step达到max_steps后停止
#    我的解释：持续报错模式下，本地乘法工具参数每次都报错、反复失败，到max_steps后停止
# 4. 直接回答的轨迹有几条，工具调用有几次？为什么不能靠轨迹条数统计工具次数？
#    我的观察：轨迹一条，工具调用0次
#    我的解释：模型发送请求不一定需要工具调用，也可能一次请求调用多个工具，所以不能靠轨迹条数统计工具次数
# 5. 任选一条 tool 消息，把它的 tool_call_id 与之前 assistant 中的 id 对照。
#    我的对照：
#    {"role": "assistant", "content": "教学脚本：先算 3 箱、每箱 4 件，一共多少件。",
#    "tool_calls": [{"id": "call_1", "type": "function",
#    "function": {"name": "multiply", "arguments": "{\"left\": 3, \"right\": 4}"}}]}
#   {"role": "tool", "content": "12", "tool_call_id": "call_1"}
