"""命令行入口：一个能连续聊天的机器人。

流程就是一句话：读一行 → 是命令就处理 → 不是就发给模型 → 把回答存回历史。

用法：
    cd weeks\\week01_llm_api\\chat_cli
    ..\\..\\..\\.venv\\Scripts\\python.exe chat_cli.py
"""

import argparse
import logging
from pathlib import Path

import cost
import llm
import memory
from conversation import Conversation

# 历史上限：超过这么多轮就把最早的对话丢掉（system 人设永远留着）。
MAX_TURNS = 8

# 长期记忆存在这个文件里（一行一条事实）。
# **它必须在 .gitignore 里**：里面是用户的私人信息，不能跟着代码提交。
FACTS_PATH = Path(__file__).resolve().parent / "facts.json"


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
    if line.startswith("/remember"):
        if line == "/remember":
            print("请在/remember后加入你想让模型记住的话！")
            return True
        text = line[9:].strip()
        memory.add_fact(FACTS_PATH, text)
        print(f"记住了：{text}")
        return True
    print(f"未知命令：{line}")
    print("可用命令：/clear、/cost、/exit、/remember")
    return True


def main(argv: list[str] | None = None) -> int:
    """把一切串起来，返回退出码。"""
    args = parse_args(argv)
    conversation = Conversation(args.system)
    usage_log = []
    print("你好，想聊点什么？")
    print("命令：/clear 清空对话、/cost 看花费、/exit 退出、/remember 让模型记住这句话")
    try:
        while True:
            line = input("你> ").strip()
            if not line:
                continue
            if line in {"/exit", "/quit"}:
                print("再见！")
                break
            if handle_command(line, conversation, usage_log):
                continue
            conversation.set_system(
                memory.compose_system(args.system, memory.load_facts(FACTS_PATH))
            )
            payload = conversation.messages() + [{"role": "user", "content": line}]
            try:
                pieces = []
                usage = []
                for piece in llm.stream_chat(
                    payload, model=args.model, usage_box=usage
                ):
                    print(piece, end="", flush=True)
                    pieces.append(piece)
                print()
                conversation.add_user(line)
                conversation.add_assistant("".join(pieces))
                if usage:
                    usage_log.append(
                        (usage[0].prompt_tokens, usage[0].completion_tokens)
                    )
            except llm.RETRYABLE_ERRORS as error:
                print(f"网络波动，请稍后再试：{type(error).__name__}")
            except llm.REQUEST_ERRORS as error:
                print(f"消息太长了，修改一下：{type(error).__name__}")
            except llm.MODEL_ERRORS as error:
                print(f"模型服务出错了：{type(error).__name__}")
            conversation.trim(MAX_TURNS)
    except KeyboardInterrupt:
        print("再见！")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
