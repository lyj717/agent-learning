"""命令行入口：一个能连续聊天的机器人。

流程就是一句话：读一行 → 是命令就处理 → 不是就发给模型 → 把回答存回历史。

用法：
    cd weeks\\week01_llm_api\\chat_cli
    ..\\..\\..\\.venv\\Scripts\\python.exe chat_cli.py
"""

import argparse
import logging

import cost
import llm
from conversation import Conversation

# 历史上限：超过这么多轮就把最早的对话丢掉（system 人设永远留着）。
# 为什么要有：Day 9 算过——20 轮对话里发出去的输入 token 是内容本身的 9.9 倍，
# 聊得越久每一轮越贵、越慢，最后还会撑爆上下文窗口。
MAX_TURNS = 8


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """定义并解析命令行参数。"""
    parser = argparse.ArgumentParser(description="连续聊天机器人")
    parser.add_argument("--system", default=None, help="系统提示词")
    parser.add_argument("--model", default=None, help="模型名")
    return parser.parse_args(argv)


def handle_command(
    line: str, conversation: Conversation, usage_log: list[tuple[int, int]]
) -> bool:
    """这一行如果是命令就处理掉（返回 True）；不是命令返回 False，交给模型。"""
    if line[0] != "/":
        return False
    if line == "/clear":
        turn = conversation.turns()
        conversation.clear()
        print(f"已清空历史，清掉了 {turn} 轮对话")
        return True
    if line == "/cost":
        input_per_turn: list[int] = []
        output_per_turn: list[int] = []
        for input_token, output_token in usage_log:
            input_per_turn.append(input_token)
            output_per_turn.append(output_token)
        total = cost.session_cost(
            input_per_turn=input_per_turn, output_per_turn=output_per_turn
        )
        print(
            f"本次会话：{len(usage_log)} 次调用，"
            f"输入 {sum(input_per_turn)} token，输出 {sum(output_per_turn)} token"
        )
        print(f"预计花费 {total:.6f} 元（按空闲价估算；真实账单以服务商后台为准）")
        return True
    print(f"未知命令：{line}")
    print("可用命令：/clear、/cost、/exit")
    return True


def main(argv: list[str] | None = None) -> int:
    """把一切串起来，返回退出码。"""
    args = parse_args(argv)
    conversation = Conversation(args.system)
    usage_log = []
    print("你好，想聊点什么？")
    print("命令：/clear 清空对话、/cost 看花费、/exit 退出")
    while True:
        line = input("你> ").strip()
        if not line:
            continue
        if line in {"/exit", "/quit"}:
            print("再见！")
            break
        if handle_command(line, conversation, usage_log):
            continue
        payload = conversation.messages() + [{"role": "user", "content": line}]
        # TODO(Day 12)：把这一整段改成「不会崩」的版本，四件事：
        #   ① 用 try/except 包住：断网（APIConnectionError）、限流（RateLimitError）、
        #      超长输入（BadRequestError/UnprocessableEntityError）都别让程序退出，
        #      打印一句人话（「网络连不上，重试过了还是不行，请稍后再试」这种）
        #   ② 失败时**别把这条问句留在历史里**——把 conversation.add_user(line)
        #      挪到调用成功之后
        #   ③ KeyboardInterrupt（Ctrl+C）：把整个 while 循环都包进 try，
        #      这样不管在哪一步按都能打印「再见」再干净退出，别甩 traceback
        #   ④ 每一轮结束后调一次 conversation.trim(MAX_TURNS)，别让历史无限长
        pieces = []
        usage = []
        conversation.add_user(line)
        for piece in llm.stream_chat(payload, model=args.model, usage_box=usage):
            print(piece, end="", flush=True)
            pieces.append(piece)
        print()
        conversation.add_assistant("".join(pieces))
        if usage:
            usage_log.append((usage[0].prompt_tokens, usage[0].completion_tokens))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
