"""Day47：生成调用耗时与已知费用范围；默认离线，--live 只请求一条 AI 教具。"""

import argparse
import json
import sys
import time
from pathlib import Path

from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week05_rag.demos.day40.day40_model_io import request_grounded_json
from weeks.week06_retrieval_eval.demos.day47.day47_support import (
    PRICE_SNAPSHOT,
    collect_answer,
    save_json,
    usage_and_cost,
)
from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def offline_request(messages: list[dict[str, str]]) -> dict:
    """独立替身返回固定用量，不联网；传入消息的形状与旧真实请求相同。"""
    return {
        "raw_text": json.dumps(
            {
                "status": "answered",
                "answer": "在前台领取。",
                "cited_ids": ["guide.md#L1-L1"],
            },
            ensure_ascii=False,
        ),
        "finish_reason": "stop",
        "model": "deepseek-flash",
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 100,
            "total_tokens": 1100,
        },
    }


def main() -> None:
    """展示计时与缺失处理，再用一条独立教具核对同一请求环境。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    print("Week6 要比较效果和代价；本演示为 Day47 读取用量、生成耗时做准备。")
    print("学完能判断哪个区间在计时、哪些费用能估算；练习不要求重写请求客户端。")
    print("\n一、是什么：耗时是两次计时读数的差，单位从秒乘 1000 转为毫秒。")
    print("为什么：旧 Day41 没保存耗时，不能事后从 token 数推算。")
    print("场景：同样的片段数，模型可能生成不同长度的回答，需保留实际用量与调用耗时。")
    # time.perf_counter()：无参数，返回单调计时的秒数；只使用两次读数之差。
    started = time.perf_counter()
    total = sum([12, 20])
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(
        f"最小计时代码：sum([12,20])={total}，这段本地计算的实测耗时={elapsed_ms:.6f} 毫秒。"
    )
    print(
        "这不是模型耗时；下面运行环境只在 request_fn(messages) 前后计时，失败也保留耗时。"
    )
    print("\n二、费用：沿用 cost_of_call，显式传同一份官方价格版本。")
    print(f"本演示统一按高峰价折算，元/百万 token：{PRICE_SNAPSHOT['price']}")
    sample = offline_request([])
    known = usage_and_cost(sample)
    print(
        f"人工用量：输入1000、输出100；缓存拆分未记录。已知费用范围={known['cost_low_yuan']}～{known['cost_high_yuan']} 元。"
    )
    print(f"没有 usage 时={usage_and_cost(None)}；不能把未记录当成零费用。")
    print("同价换算范围不是实际账单；模型不匹配也不套用这份价格。")

    def execute(run_dir: Path) -> None:
        """用一条独立 AI 原文试跑同一请求环境，不运行真实开发集。"""
        original = Document(
            id="guide.md", page_content="在前台领取。", metadata={"source": "guide.md"}
        )
        evidence = [
            Document(
                id="guide.md#L1-L1",
                page_content=original.page_content,
                metadata={"source": "guide.md", "line_start": 1, "line_end": 1},
            )
        ]
        request = request_grounded_json if args.live else offline_request
        print("\n三、独立教具：问题‘在哪里领取？’，原文 guide.md 第1行‘在前台领取’。")
        print(
            "真实模型请求"
            if args.live
            else "离线替身：以下响应与 token 为人工值，耗时仅为替身调用时间"
        )
        row = collect_answer(
            "demo01",
            "vector",
            "在哪里领取？",
            evidence,
            {"guide.md": original},
            request,
        )
        save_json(run_dir / "demo_response.json", row)
        print(
            f"请求次数={row['request_count']}；生成调用毫秒={row['generation_ms']}；错误={row['error']}"
        )
        if row["response"] is not None:
            print(
                f"实际响应模型={row['response']['model']}；原始正文={row['response']['raw_text']}"
            )
        print(
            f"输入/输出 token={row['prompt_tokens']}/{row['completion_tokens']}；费用范围={row['cost_low_yuan']}～{row['cost_high_yuan']}"
        )
        print("本处不做人工作答判分；本地检索和人工评阅不在计时范围内。")
        if row["error"]:
            raise RuntimeError(row["error"])

    run_logged(
        "measure_live" if args.live else "measure_offline",
        execute,
        {
            "data": "AI_demo_only",
            "live": args.live,
            "price_version": PRICE_SNAPSHOT["checked_date"],
        },
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY47_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
