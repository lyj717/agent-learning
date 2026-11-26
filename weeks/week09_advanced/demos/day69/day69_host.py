"""Day69 宿主：把 notes MCP Server 接到真实模型上，跑一次「模型决定调用工具」的问答。

宿主要做的事：启动 server（stdio）→ 把 tools/list 转成模型能看懂的 tools 参数 →
让模型自己决定调哪个工具 → 把工具结果拼回对话 → 循环到模型给出最终回答。
本文件是 AI 提供的教具；你要用它跑真实问题、核对引用、记录轨迹，不要求你重写宿主。

用法（仓库根目录）：
    # 离线自检：用脚本化的假模型，验证「宿主 → MCP → 模型」这条链能跑通
    .venv\\Scripts\\python.exe -B -X utf8 weeks\\week09_advanced\\demos\\day69\\day69_host.py --fake
    # 真实模型：读 .env 里的 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
    .venv\\Scripts\\python.exe -B -X utf8 weeks\\week09_advanced\\demos\\day69\\day69_host.py --live --question "我的笔记里怎么处理流式块？"

轨迹保存到 demos/day69/outputs/<live|fake>_<时间戳>.json，控制台同时打印每一步。
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp import Client, StdioServerParameters

from weeks.week02_tools.demos.shared.llm_client import make_client

DAY69 = Path(__file__).resolve().parent
CORPUS = REPO_ROOT / "weeks/week09_advanced/demos/day65/corpus"
MAX_ROUNDS = 4


def mcp_tools_to_openai(tools: list[object]) -> list[dict[str, object]]:
    """把 MCP 的工具定义转成 OpenAI 的 tools 参数；返回可直接传的列表。"""
    converted: list[dict[str, object]] = []
    for tool in tools:
        converted.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
        )
    return converted


def fake_model(
    messages: list[dict[str, object]], tools: list[dict[str, object]]
) -> dict:
    """离线假模型：第一轮要求检索，看到工具结果后给最终回答。"""
    has_tool_result = any(message["role"] == "tool" for message in messages)
    if not has_tool_result:
        return {
            "tool_calls": [
                {
                    "id": "call_fake_1",
                    "name": "search_notes",
                    "arguments": {"keyword": "关键词", "limit": 2},
                }
            ],
            "content": None,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
    sources = []
    for message in messages:
        if message["role"] == "tool":
            sources.append(str(message["content"])[:60])
    return {
        "tool_calls": [],
        "content": f"（离线假模型）工具返回了 {len(sources)} 段结果：{sources}",
        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
    }


def live_model(
    client,
    messages: list[dict[str, object]],
    tools: list[dict[str, object]] | None,
    *,
    model_override: str | None = None,
) -> dict:
    """调用真实模型，返回归一化的 tool_calls / content / usage。"""
    kwargs: dict[str, object] = {
        "model": model_override or os.environ.get("LLM_MODEL", "deepseek-flash"),
        "messages": messages,
        "max_tokens": 1024,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message
    calls = []
    for call in message.tool_calls or []:
        try:
            arguments = json.loads(call.function.arguments)
        except json.JSONDecodeError:
            arguments = {}
        calls.append(
            {"id": call.id, "name": call.function.name, "arguments": arguments}
        )
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
    }
    return {
        "tool_calls": calls,
        "content": message.content,
        "usage": usage,
        "reasoning": getattr(message, "reasoning_content", None),
    }


async def run_host(
    question: str,
    *,
    live: bool,
    notes_root: Path | None = None,
    with_index: bool = False,
) -> dict[str, object]:
    """启动 server、跑模型循环，返回轨迹（含工具调用与最终回答）。"""
    root = notes_root or (REPO_ROOT / "notes" if live else CORPUS)
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "projects.mcp_server.server"],
        env={**os.environ, "NOTES_ROOT": str(root), "PYTHONIOENCODING": "utf-8"},
        cwd=str(REPO_ROOT),
    )
    client = make_client() if live else None
    messages: list[dict[str, object]] = [
        {
            "role": "system",
            "content": "你是笔记助手。先用工具检索，同一文件不要重复读取；信息够了立即给出最终回答，回答时引用文件名与行号。",
        },
        {"role": "user", "content": question},
    ]
    trajectory: dict[str, object] = {
        "mode": "live" if live else "fake",
        "question": question,
        "model": os.environ.get("LLM_MODEL", "deepseek-flash") if live else "fake",
        "started_at": datetime.now().astimezone().isoformat(),
        "steps": [],
        "answer": "",
        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
    }

    async with Client(params) as session:
        tools = mcp_tools_to_openai((await session.list_tools()).tools)
        if with_index:
            index_text = (await session.read_resource("note://index")).contents[0].text
            messages[0]["content"] = (
                str(messages[0]["content"])
                + "\n\n可用笔记清单（应用已加载，不需要再检索文件名）：\n"
                + index_text
            )
        for round_no in range(1, MAX_ROUNDS + 1):
            if live:
                step = live_model(client, messages, tools)
            else:
                step = fake_model(messages, tools)
            trajectory["usage"]["prompt_tokens"] += step["usage"]["prompt_tokens"]
            trajectory["usage"]["completion_tokens"] += step["usage"][
                "completion_tokens"
            ]
            record = {
                "round": round_no,
                "tool_calls": [],
                "content": step["content"],
                "reasoning": (step.get("reasoning") or "")[:200],
            }
            if not step["tool_calls"]:
                trajectory["answer"] = (
                    step["content"] or "（模型只返回了思考内容，没有最终回答）"
                )
                trajectory["steps"].append(record)
                break
            for call in step["tool_calls"]:
                result = await session.call_tool(call["name"], call["arguments"])
                text = result.content[0].text if result.content else ""
                record["tool_calls"].append(
                    {
                        "name": call["name"],
                        "arguments": call["arguments"],
                        "result": text[:400],
                    }
                )
                assistant_message: dict[str, object] = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call["id"],
                            "type": "function",
                            "function": {
                                "name": call["name"],
                                "arguments": json.dumps(
                                    call["arguments"], ensure_ascii=False
                                ),
                            },
                        }
                    ],
                }
                if step.get("reasoning"):
                    assistant_message["reasoning_content"] = step["reasoning"]
                messages.append(assistant_message)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": text,
                    }
                )
            trajectory["steps"].append(record)
        if live and (
            not trajectory["answer"]
            or "没有最终回答" in trajectory["answer"]
            or "DSML" in trajectory["answer"]
        ):
            # 模型在限定轮数内没有收尾：把已取得的资料收拢，换一个新对话要最终回答。
            evidence = []
            for step_record in trajectory["steps"]:
                for call_record in step_record["tool_calls"]:
                    evidence.append(f"[{call_record['name']}] {call_record['result']}")
            harvest = [
                {
                    "role": "system",
                    "content": "你是笔记助手。工具已关闭，只能根据已有资料回答，并引用文件名与行号。",
                },
                {
                    "role": "user",
                    "content": (
                        f"问题：{question}\n\n已检索到的资料：\n"
                        + "\n\n".join(evidence)[:6000]
                    ),
                },
            ]
            if live:
                step = live_model(
                    client,
                    harvest,
                    None,
                    model_override="deepseek-chat",
                )
                trajectory["usage"]["prompt_tokens"] += step["usage"]["prompt_tokens"]
                trajectory["usage"]["completion_tokens"] += step["usage"][
                    "completion_tokens"
                ]
                trajectory["answer"] = (
                    step["content"] or ""
                ).strip() or "（收尾没有返回内容）"
            else:
                trajectory["answer"] = "（离线假模型）达到最大轮数"
    return trajectory


def main() -> None:
    """解析参数、跑宿主、打印轨迹并保存 JSON。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="用真实模型")
    parser.add_argument("--fake", action="store_true", help="用脚本化假模型自检")
    parser.add_argument("--question", default="我的笔记里怎么处理流式块？")
    parser.add_argument(
        "--notes-root", default=None, help="语料根目录；默认仓库 notes/"
    )
    parser.add_argument(
        "--with-index", action="store_true", help="启动时把 note://index 注入系统提示"
    )
    args = parser.parse_args()
    if not args.live and not args.fake:
        parser.error("需要 --live 或 --fake")

    notes_root = Path(args.notes_root) if args.notes_root else None
    trajectory = asyncio.run(
        run_host(args.question, live=args.live, notes_root=notes_root)
    )
    mode = "live" if args.live else "fake"
    print(json.dumps(trajectory, ensure_ascii=False, indent=2))

    out_dir = DAY69 / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{mode}_{stamp}.json"
    path.write_text(
        json.dumps(trajectory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n轨迹已保存：{path}")


if __name__ == "__main__":
    main()
