"""Day 8 材料二：temperature 对比实验（只负责跑数据，结论你来下）。

这是什么：temperature（温度）是 0~2 的参数，控制模型选下一个词时的随机程度。
          0 最保守，越高越放飞。

这个脚本**只做一件事**：把同一个问题在两个温度下各跑几次，把原始结果和
用量打印出来，方便你抄进 day08_参数对比记录.md。它不给结论——观察、
归纳、写规则都是你的活。

用法（需要网络，会消耗少量额度；密钥从仓库根目录的 .env 读）：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_temperature_demo.py
    ... --times 5           每个温度跑几次（默认 5）
    ... --prompt "换个问题"  换一个要观察的 prompt
    ... --max-tokens 1024   限制每次最多生成多少 token（默认 1024）

为什么 max_tokens 默认给 1024 而不是几十：当前接的是推理模型，它先想一段
（reasoning_tokens），再给正式回答。额度给小了，思考就把额度用光、回答会是空的。
注意：遇到开放式问题（比如「给我起个名字」）它可能一直想下去，1024 也未必够；
可以继续调大，或者按官方文档用 thinking / reasoning_effort 控制思考强度。
"""

import argparse
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# 往上两层是仓库根目录（这个文件在 weeks/week01_llm_api/ 里）
ROOT = Path(__file__).resolve().parents[2]

# 两个对照组：一个最稳，一个明显放飞（再高基本就没法用了）
TEMPERATURES = [0.0, 1.5]

# 起名是「多样但不唯一」的任务，温度的影响比较容易看出来
DEFAULT_PROMPT = (
    "给一个「查询未来三天天气」的工具起个中文名字，"
    "不超过 8 个字，只输出名字本身，不要引号和解释。"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="temperature 对比实验")
    parser.add_argument("--times", type=int, default=5, help="每个温度跑几次")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="要观察的问题")
    parser.add_argument(
        "--max-tokens", type=int, default=1024, help="最多生成多少 token"
    )
    return parser.parse_args(argv)


def ask_once(
    client: OpenAI,
    model: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> tuple[str, str, object, float]:
    """发一次请求，返回（回答, 结束原因, 用量, 耗时秒数）。用非流式，要完整结果。"""
    start = time.perf_counter()
    # chat.completions.create(...)：发一次请求。temperature 越高，同样的
    # 输入越可能得到不同的输出
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    elapsed = time.perf_counter() - start
    choice = response.choices[0]
    return (
        (choice.message.content or "").strip(),
        choice.finish_reason,
        response.usage,
        elapsed,
    )


def describe_tokens(usage: object) -> str:
    """把用量拼成一行短说明，usage 为空时返回空串。"""
    if usage is None:
        return "（无用量信息）"
    details = getattr(usage, "completion_tokens_details", None)
    reasoning = getattr(details, "reasoning_tokens", 0)
    return (
        f"输入 {usage.prompt_tokens} / 输出 {usage.completion_tokens}"
        f"（其中思考 {reasoning or 0}）"
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    load_dotenv(ROOT / ".env")
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL"),
    )
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    print(f"模型：{model}")
    print(f"prompt：{args.prompt}")
    print(f"每个温度跑 {args.times} 次，max_tokens={args.max_tokens}\n")

    results: dict[float, list[str]] = {}
    for temperature in TEMPERATURES:
        print(f"--- temperature = {temperature} ---")
        answers: list[str] = []
        for i in range(1, args.times + 1):
            try:
                answer, finish, usage, elapsed = ask_once(
                    client, model, args.prompt, temperature, args.max_tokens
                )
            except OpenAIError as error:
                # 只捕 SDK 的异常；网络/密钥/限流都可能，记下类型就够排查了
                print(f"  {i}. 失败：{type(error).__name__}: {error}")
                continue
            answers.append(answer)
            shown = answer if answer else "（空——把 --max-tokens 调大再看）"
            print(
                f"  {i}. {elapsed:.1f}s  finish={finish}  "
                f"{describe_tokens(usage)}  ->  {shown}"
            )
        results[temperature] = answers
        print(f"  小计：{len(answers)} 次里出现 {len(set(answers))} 种结果\n")

    # 下面这段是给你直接抄进记录的原始数据，不是结论
    print("=" * 56)
    print("原始数据（复制到 day08_参数对比记录.md 的第一节）")
    print("=" * 56)
    print(f"- 模型：{model}")
    print(f"- prompt：{args.prompt}")
    print(f"- max_tokens：{args.max_tokens}")
    print()
    print("| 次数 | temperature=0.0 | temperature=1.5 |")
    print("|---|---|---|")
    for i in range(args.times):
        cells = []
        for temperature in TEMPERATURES:
            answers = results.get(temperature, [])
            cells.append(answers[i] if i < len(answers) else "（这次失败）")
        print(f"| {i + 1} | {cells[0]} | {cells[1]} |")
    print()
    for temperature in TEMPERATURES:
        answers = results.get(temperature, [])
        print(
            f"- temperature={temperature}：{len(answers)} 次，{len(set(answers))} 种结果"
        )

    print("\n观察、归纳、判断温度规则——回 day08_参数对比记录.md 写你的答案。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
