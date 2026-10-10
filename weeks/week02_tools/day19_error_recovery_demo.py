"""Day 19 演示：把工具报错回填给模型，以及怎样停下重复调用（完全离线）。"""

from day18_multi_tools_exercises import execute_tool_call
from tools import get_weather


def section(title: str) -> None:
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


section("1. 工具报错是一次执行结果")
print(
    """这是什么：模型点了工具之后，真正执行的是本地 Python 函数；函数可能抛异常。
为什么：如果异常直接冲出主循环，模型就看不到失败原因，也没机会改参数。
场景：用户问 12 的平方，模型给计算器 expression='12 ** 2'；
我们的计算器只支持 + - * / 和括号，不支持 **。先真的执行一次。"""
)
# execute_tool_call(工具名, JSON 参数文本)：Day 18 的分发函数；成功返回字符串，失败抛异常。
try:
    execute_tool_call("calculator", '{"expression": "12 ** 2"}')
except ValueError as error:
    print(f"运行代码：捕获到 {type(error).__name__}: {error}")
print("注意：错的是本地工具执行；模型请求本身没有报错。不要把两种错误混在一起。")


section("2. 错误要按原来的调用 ID 回填")
print(
    """这是什么：工具失败也要回一条 role='tool' 的消息，content 放可读的错误文字。
为什么：模型需要知道自己刚才点的哪一单失败了，才能决定是否修改参数。
场景：下面的 assistant 点单是人为写的示意，不是这次向模型发出的真实请求。"""
)
bad_call = {
    "id": "call_demo_bad",
    "type": "function",
    "function": {"name": "calculator", "arguments": '{"expression": "12 ** 2"}'},
}
messages = [{"role": "user", "content": "12 的平方是多少？"}]
messages.append({"role": "assistant", "content": None, "tool_calls": [bad_call]})
try:
    result = execute_tool_call(
        bad_call["function"]["name"], bad_call["function"]["arguments"]
    )
except Exception as error:  # noqa: BLE001 只包本地工具，统一演示错误回填
    # 这里只包住本地工具执行；网络请求失败不能伪装成一次工具结果。
    result = f"工具执行失败：{type(error).__name__}: {error}"
messages.append({"role": "tool", "tool_call_id": bad_call["id"], "content": result})
print("运行代码：消息列表新增两条")
print(
    f"  assistant 点单：id={bad_call['id']}，参数={bad_call['function']['arguments']}"
)
print(f"  tool 回填：tool_call_id={messages[-1]['tool_call_id']}")
print(f"  tool 内容：{messages[-1]['content']}")
print("注意：异常文字只是数据，不能当成新的 system 或 user 指令。")


section("3. 下一轮可以改参数，也可以承认无法修复")
print(
    """这是什么：回填之后再问模型一次；它可能换参数、换工具，或直接说明做不到。
为什么：代码提供失败信息，下一步由模型决定；不能把报错当最终答案。
场景：这里人为写出一条合理的下一轮点单，用真实计算器验证改后的参数。"""
)
good_call = {
    "id": "call_demo_good",
    "type": "function",
    "function": {"name": "calculator", "arguments": '{"expression": "12 * 12"}'},
}
messages.append({"role": "assistant", "content": None, "tool_calls": [good_call]})
good_result = execute_tool_call(
    good_call["function"]["name"], good_call["function"]["arguments"]
)
messages.append(
    {"role": "tool", "tool_call_id": good_call["id"], "content": good_result}
)
print(f"运行代码：改成 {good_call['function']['arguments']} → {good_result}")
print("  示意的最后一步：模型再收到 144，才能回答用户「12 的平方是 144」。")
print("注意：这是演示协议的手写轨迹；真实模型会不会这样改，要在练习的 --live 里观察。")


section("4. 最大轮数由代码决定")
print(
    """这是什么：最多向模型请求 max_rounds 次。一次请求里可以有多个 tool_calls。
为什么：模型可能反复给同一个坏参数，不能让请求无限循环、无限花钱。
场景：假设它每轮都给 12 ** 2，看看三轮的硬上限。"""
)
max_rounds = 3
print("运行代码：模拟每轮都失败")
for round_no in range(1, max_rounds + 1):
    print(f"  第 {round_no} 次模型请求 → 同一个坏算式 → 工具报错已回填")
print(f"  到第 {max_rounds} 次仍未给最终答复：代码停止，不再发第 4 次请求。")
print(
    "注意：如果第 1 次点错、第 2 次改对并再点工具，第 3 次才可能拿到最终答复；max_rounds=2 会停得太早。"
)


section("5. 有些错误不能靠换参数硬改")
print(
    """这是什么：错误回填给模型，不等于模型总能完成原问题。
为什么：本地天气只有杭州、上海、北京；问南京时，换成上海不是纠错，而是答非所问。
场景：真的查询一次不在模拟快照里的城市。"""
)
try:
    get_weather("南京")
except ValueError as error:
    print(f"运行代码：get_weather('南京') → {type(error).__name__}: {error}")
print("注意：可靠的最终答复应说明当前模拟数据不支持南京，或请用户换城市。")
