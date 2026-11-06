"""Day51A：严格请求模型与进程内 HTTP 小接口。

--part a 检查模型；--part b 检查应用。观察与到期短复验写在 demos/day51/day51a_记录.md。
"""

import argparse
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 以下是 AI 维护的留证与对照环境，做题不需要读内部实现。
from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day51.day51_checks import run_a, run_b


class QuestionRequest(BaseModel):
    """校验问题字符串、数量范围与允许字段。"""

    model_config = ConfigDict(extra="forbid")
    question: str = Field(strict=True, min_length=1)
    top_k: int = Field(default=2, strict=True, ge=1, le=4)


def create_app() -> FastAPI:
    """创建提供健康检查与问题检查接口的新应用。"""
    app = FastAPI()

    def common_get() -> dict:
        return {"status": "ok", "mode": "offline"}

    def common_post(request: QuestionRequest) -> dict:
        question = request.question.strip()
        top_k = request.top_k
        if not question:
            raise HTTPException(status_code=400, detail="question 不能只有空白")
        return {"question": question, "top_k": top_k, "character_count": len(question)}

    app.add_api_route(path="/health", endpoint=common_get, methods=["GET"])
    app.add_api_route(path="/inspect", endpoint=common_post, methods=["POST"])
    return app


def main() -> None:
    """记录本轮配置、模型/HTTP 对照和异常，失败也留证。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b"], default="a")
    args = parser.parse_args()

    def execute(run_dir: Path) -> None:
        """只调用学员模型或应用工厂，不补写练习答案。"""
        if args.part == "a":
            run_a(QuestionRequest, run_dir)
        else:
            run_b(create_app, run_dir)

    run_logged(
        args.part,
        execute,
        {"transport": "testclient_in_process", "model_calls": 0},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day51/outputs",
        origin_env="DAY51_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
