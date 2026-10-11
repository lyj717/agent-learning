"""Day 23：认识手写 Agent 的输出协议；默认离线，--live 请求一次真实模型。"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Path(__file__).resolve().parents[2]：从本脚本位置向上两级找到仓库根目录。
ROOT = Path(__file__).resolve().parents[2]


def section(title: str) -> None:
    """打印一节标题。"""
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


def inspect_reply(raw: str, finish_reason: str) -> None:
    """只展示解析过程；完整协议校验留给学员的两份练习。"""
    print(f"原始正文：{raw!r}")
    print(f"finish_reason：{finish_reason!r}")
    if finish_reason == "length":
        # 输出被截断时，即使眼前的文字碰巧能解析，也不能当成完整决定。
        print("先停止：模型输出被截断，不能据此调用工具。")
        return
    if finish_reason != "stop":
        # 其他结束原因也不是一次正常完成的决定，先查原因再继续。
        print(f"先停止：结束原因是 {finish_reason!r}，不是正常结束。")
        return
    if not raw.strip():
        # 空正文没有任何可执行的决定。
        print("先停止：正文为空。")
        return
    try:
        # json.loads(JSON 文本)：把字符串变成 Python 的字典、列表等对象。
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        # 语法错误和“字段不符合协议”是两类不同的问题。
        print(f"先停止：JSON 语法错误：{error.msg}")
        return
    print(f"解析后的类型：{type(data).__name__}")
    if not isinstance(data, dict):
        # 合法 JSON 也可能是列表；我们的协议要求最外层必须是字典。
        print("先停止：协议要求最外层是字典。")
        return
    print(f"已有字段：{list(data)}")
    print(f"kind 的值：{data.get('kind')!r}")
    print("下一步仍要检查字段、类型和允许的工具名，不能直接执行。")


def live_reply() -> tuple[str, str]:
    """从仓库根目录的 .env 读取配置，只请求一次模型并返回原始正文与结束原因。"""
    # load_dotenv(文件路径)：从指定 .env 文件读取环境变量；不会打印密钥。
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("LLM_API_KEY", "")
    if len(api_key) < 20:
        # 没有可用密钥时不要发请求；提示学员检查根目录的配置。
        raise RuntimeError("缺少 LLM_API_KEY：请检查仓库根目录的 .env")
    # OpenAI(api_key, base_url, timeout, max_retries)：建兼容接口的客户端。
    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("LLM_BASE_URL"),
        timeout=60,
        max_retries=0,
    )
    prompt = (
        "只输出一个 json 对象，不要 Markdown。"
        "若需要乘法工具，输出形如 "
        '{"kind":"action","tool":"multiply","arguments":{"left":3,"right":4}}。'
        '若可以直接回答，输出形如 {"kind":"final","answer":"你好"}。'
        "每次只作一个决定，不要自己计算乘法。"
    )
    # chat.completions.create(...)：发一次聊天请求；json_object 约束正文的 JSON 语法。
    response = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "deepseek-flash"),
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "3 箱商品，每箱 4 件。先用乘法工具算件数。"},
        ],
        response_format={"type": "json_object"},
        max_tokens=2048,
    )
    choice = response.choices[0]
    return choice.message.content or "", choice.finish_reason or ""


def main() -> None:
    """按这是什么、为什么、场景、代码、注意的顺序带着读者走。"""
    # ArgumentParser(description)：建立命令行选项解析器，description 是帮助文字。
    parser = argparse.ArgumentParser(description="Day 23 输出协议演示")
    # add_argument(选项, action)：出现 --live 时把 args.live 设为 True。
    parser.add_argument("--live", action="store_true", help="真实请求模型一次")
    # parse_args()：读取命令行参数；无 --live 时只跑离线样例。
    args = parser.parse_args()

    section("1. 先认识正文里的输出协议")
    print("这是什么：让模型每次在正文里给一个 JSON 对象，说明下一步是行动还是答复。")
    print("为什么需要：手写 Agent 要自己分辨该执行工具，还是该结束循环。")
    print("场景：算 3 箱、每箱 4 件时，先请求 multiply；拿到观察后才能回答。")
    print(
        '行动示例：{"kind":"action","tool":"multiply","arguments":{"left":3,"right":4}}'
    )
    print('答复示例：{"kind":"final","answer":"共 12 件"}')
    print("注意：这是我们约定的 message.content 格式，不是 API 原生 tool_calls 字段。")

    section("2. 把 JSON 语法和协议校验分开")
    print("这是什么：json.loads 负责把文字变成 Python 对象；我们再检查对象的形状。")
    print("为什么需要：能解析的 JSON 仍可能缺字段、字段类型不对，或乱写工具名。")
    print("场景：下面三个正文都是合法 JSON，但只有第一个像完整行动。")
    print("代码：data = json.loads(raw)，得到对象后再检查是不是 dict。")
    examples = [
        '{"kind":"action","tool":"multiply","arguments":{"left":3,"right":4}}',
        '{"kind":"action","tool":"erase_all","arguments":{}}',
        '["action", "multiply"]',
    ]
    for raw in examples:
        inspect_reply(raw, "stop")
    print("注意：演示只看到 kind 和字段；练习还要拒绝未知工具和错误字段。")

    section("3. 先看结束原因，再解析正文")
    print("这是什么：finish_reason 说明本次模型输出是正常结束还是被截断。")
    print("为什么需要：被截断的行动参数不能交给工具执行。")
    print("场景：同样一段正文，标记为 length 时也不能当成完整决定。")
    print('代码：先判断 finish_reason == "stop"，再解析正文。')
    inspect_reply('{"kind":"final","answer":"共 12 件"}', "length")
    inspect_reply('{"kind":"final","answer":"共 12 件"}', "content_filter")
    inspect_reply('{"kind":', "stop")
    print("注意：JSON 模式管语法，不替我们保证 kind、tool、arguments、answer 正确。")

    if args.live:
        # 用户明确加了 --live，才花费一次真实模型请求。
        section("4. 真实模型返回什么")
        print("这是什么：把同一份行动协议写入提示词，请模型只作一次决定。")
        print("为什么需要：固定样例不会暴露真实输出里的空正文、截断或字段偏差。")
        print("场景：请模型先调用 multiply 算 3 箱、每箱 4 件。")
        raw, finish_reason = live_reply()
        inspect_reply(raw, finish_reason)
        print("注意：此处只检查和展示，不执行模型要求的工具。")

    section("接下来做什么")
    print("第一步：先完成 day23_json_parse_exercises.py，只练正文解析与截断检查。")
    print("第二步：再完成 day23_decision_exercises.py，分别校验最终答复和行动。")
    print("第三步：运行本演示的 --live，把真实正文与两份练习的规则对照。")
    print("第四步：在练习文件末尾写下你观察到的现象与原因，再交给我批改。")
    print("注意：今天不把这些零件拼成完整 Agent；周末再整合。")


if __name__ == "__main__":
    main()
