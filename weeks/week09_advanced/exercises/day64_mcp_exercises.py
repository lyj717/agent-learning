"""Day64 检查器：验证 projects/mcp_server 的 search_text 工具是否按约定工作。

题目与 13 组固定输入见 demos/day64/day64_题目说明.md。
检查器只读你的 server，不修改任何文件；全部离线，0 次模型调用。
每次运行在 demos/day64/outputs/ 下新建目录，保存 console.log、run_info.json 与 results.json。
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp import Client

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY64 = REPO_ROOT / "weeks/week09_advanced/demos/day64"

TEXT_A = "第一行：笔记开头\n第二行：关键词 在这里\n第三行：关键词 也在\n第四行：结束"
TEXT_B = "Note 大写\nnote 小写\nNOTE 全大写"

EXPECTED_TWO = [
    {"line": 2, "text": "第二行：关键词 在这里"},
    {"line": 3, "text": "第三行：关键词 也在"},
]
EXPECTED_ONE = [{"line": 2, "text": "第二行：关键词 在这里"}]
EXPECTED_THREE = [
    {"line": 1, "text": "Note 大写"},
    {"line": 2, "text": "note 小写"},
    {"line": 3, "text": "NOTE 全大写"},
]


def unwrap(result: object) -> object:
    """拆掉 SDK 对 list 返回值的 {"result": ...} 包装，返回内层结构化结果。"""
    payload = getattr(result, "structured_content", None)
    if isinstance(payload, dict) and set(payload) == {"result"}:
        return payload["result"]
    return payload


def row(number: int, label: str, ok: bool, detail: str) -> dict[str, object]:
    """组装一条检查组；detail 写实际值与期望值，失败时好定位。"""
    return {"no": number, "label": label, "ok": ok, "detail": detail}


async def call_safe(
    client: Client, name: str, arguments: dict[str, object]
) -> tuple[object | None, str | None]:
    """调用工具；工具层错误是 is_error 结果，只有协议层异常才在这里被捕获。"""
    try:
        return await client.call_tool(name, arguments), None
    except Exception as error:  # noqa: BLE001 - 协议层异常要报出来，不能吞
        return None, f"{type(error).__name__}: {error}"


async def check_success(
    client: Client,
    number: int,
    label: str,
    arguments: dict[str, object],
    expected: object,
) -> dict[str, object]:
    """跑一次应当成功的调用，比较结构化返回值。"""
    result, error = await call_safe(client, "search_text", arguments)
    if error or result is None:
        return row(number, label, False, error or "没有拿到结果")
    actual = unwrap(result)
    return row(number, label, actual == expected, f"实际={actual} 期望={expected}")


def result_text(result: object) -> str:
    """取出工具结果里的文本（错误消息也在这里），便于判断是哪一类失败。"""
    content = getattr(result, "content", None) or []
    if content and isinstance(getattr(content[0], "text", None), str):
        return content[0].text
    return ""


async def check_error(
    client: Client,
    number: int,
    label: str,
    name: str,
    arguments: dict[str, object],
    *,
    expect_unknown_tool: bool = False,
) -> dict[str, object]:
    """跑一次应当失败的调用，确认失败以 is_error 结果返回、而不是异常。"""
    result, error = await call_safe(client, name, arguments)
    if error or result is None:
        return row(number, label, False, f"调用本身抛了异常：{error}")
    is_error = getattr(result, "is_error", None)
    text = result_text(result)
    if not expect_unknown_tool and "Unknown tool" in text:
        return row(number, label, False, f"search_text 未注册（{text}）")
    return row(number, label, is_error is True, f"is_error={is_error}；{text[:60]}")


async def run_checks() -> list[dict[str, object]]:
    """连上学员的 server，按固定表跑 13 组检查，返回逐项结果列表。"""
    try:
        from projects.mcp_server.server import mcp
    except Exception as error:  # noqa: BLE001 - 导入失败要整段报出来
        traceback.print_exc()
        return [
            row(
                0,
                "导入 projects.mcp_server.server",
                False,
                f"{type(error).__name__}: {error}",
            )
        ]

    checks: list[dict[str, object]] = []
    async with Client(mcp) as client:
        listed = await client.list_tools()
        names = [tool.name for tool in listed.tools]
        checks.append(row(1, "工具已注册", "search_text" in names, f"实际工具={names}"))

        tool = next((item for item in listed.tools if item.name == "search_text"), None)
        if tool is None:
            for number, label in (
                (2, "必填参数"),
                (3, "limit 默认值"),
                (4, "工具描述非空"),
            ):
                checks.append(row(number, label, False, "search_text 未注册，无法检查"))
        else:
            schema = tool.input_schema
            required = sorted(schema.get("required", []))
            checks.append(
                row(
                    2,
                    "必填参数",
                    required == ["keyword", "text"],
                    f"required={required}",
                )
            )
            limit_schema = schema.get("properties", {}).get("limit", {})
            has_default = limit_schema.get("default") == 5
            not_required = "limit" not in schema.get("required", [])
            checks.append(
                row(
                    3,
                    "limit 默认值",
                    has_default and not_required,
                    f"default={limit_schema.get('default')}，limit 在 required={not not_required}",
                )
            )
            description = (tool.description or "").strip()
            checks.append(
                row(
                    4,
                    "工具描述非空",
                    len(description) >= 8,
                    f"去空白后长度={len(description)}",
                )
            )

        checks.append(
            await check_success(
                client,
                5,
                "正常命中",
                {"text": TEXT_A, "keyword": "关键词", "limit": 5},
                EXPECTED_TWO,
            )
        )
        checks.append(
            await check_success(
                client,
                6,
                "limit 截断",
                {"text": TEXT_A, "keyword": "关键词", "limit": 1},
                EXPECTED_ONE,
            )
        )
        checks.append(
            await check_success(
                client,
                7,
                "大小写不敏感",
                {"text": TEXT_B, "keyword": "note", "limit": 5},
                EXPECTED_THREE,
            )
        )
        checks.append(
            await check_success(
                client,
                8,
                "无命中",
                {"text": TEXT_A, "keyword": "不存在的词", "limit": 5},
                [],
            )
        )

        checks.append(
            await check_error(
                client, 9, "空关键词", "search_text", {"text": TEXT_A, "keyword": "   "}
            )
        )
        checks.append(
            await check_error(
                client,
                10,
                "limit 为 0",
                "search_text",
                {"text": TEXT_A, "keyword": "关键词", "limit": 0},
            )
        )
        checks.append(
            await check_error(
                client,
                11,
                "limit 为负数",
                "search_text",
                {"text": TEXT_A, "keyword": "关键词", "limit": -1},
            )
        )
        checks.append(
            await check_error(
                client, 12, "工具不存在", "no_such_tool", {}, expect_unknown_tool=True
            )
        )
        checks.append(
            await check_error(
                client, 13, "参数类型不对", "search_text", {"text": 123, "keyword": "x"}
            )
        )

    return checks


def main() -> None:
    """跑检查、打印逐项结果并保存留证；返回 None。"""

    def action(run_dir: Path) -> None:
        checks = asyncio.run(run_checks())
        passed = sum(1 for item in checks if item["ok"])
        print("\n逐项结果：")
        for item in checks:
            mark = "[OK]" if item["ok"] else "[X] "
            print(f"{mark} 第 {item['no']:>2} 组 {item['label']}：{item['detail']}")
        print(f"\n合计：{passed}/{len(checks)}")
        if passed == len(checks):
            print("全过。可以把这组结果抄进记录，再回答观察题。")
        else:
            print("没过：先看每个 [X] 的「实际=... 期望=...」，再回题目说明对接口。")

        payload = {"counts": {"passed": passed, "total": len(checks)}, "checks": checks}
        (run_dir / "results.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    run_logged(
        "day64",
        action,
        config={"model_calls": 0, "data": "day64-fixed-text", "cases": 13},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY64 / "outputs",
        origin_env="DAY64_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
