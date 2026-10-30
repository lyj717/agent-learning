"""AI 维护的 A/B 输出留证：终端照常显示，同时保存日志与运行信息。

只包装检查入口，不修改学员函数，也不自动填写观察、解释或基线判分。
"""

import hashlib
import json
import os
import sys
import traceback
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import TextIO
from uuid import uuid4

DAY41 = Path(__file__).resolve().parent
CHECK_LOGS = DAY41 / "outputs" / "checks"
EXERCISE = DAY41.parents[1] / "exercises" / "day41_rag_exercises.py"


class _Tee:
    """把输出同时写入原终端与 UTF-8 日志，供运行环境内部使用。"""

    def __init__(self, console: TextIO, log: TextIO) -> None:
        self.console = console
        self.log = log

    def write(self, text: str) -> int:
        """同步写入两处并刷新日志，返回本次字符数。"""
        self.log.write(text)
        self.log.flush()
        self.console.write(text)
        return len(text)

    def flush(self) -> None:
        """刷新终端与日志，不关闭原终端。"""
        self.console.flush()
        self.log.flush()

    def isatty(self) -> bool:
        """沿用原终端属性，兼容依赖终端输出的库。"""
        return self.console.isatty()

    @property
    def encoding(self) -> str | None:
        """沿用原终端声明的编码；日志本身固定使用 UTF-8。"""
        return self.console.encoding


def _save_info(path: Path, info: dict) -> None:
    """把运行状态写为 UTF-8 JSON，不推断执行者或自动判定学习结果。"""
    path.write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run_logged_check(
    part: str,
    check_fn: Callable[..., None],
    learner_fn: Callable[..., object],
    log_root: Path = CHECK_LOGS,
) -> None:
    """运行 A/B 检查并留证，发生异常时保存回溯并原样抛出。

    part 是 a 或 b；check_fn 是已有检查入口；learner_fn 是学员函数。
    log_root 默认位于 Day 41 输出目录，供 AI 验证时也可传入隔离目录。
    每次使用独立目录；origin 是来源标记，默认未确认，不据此声称学员亲跑。
    返回 None；控制台、日志和运行状态分别保留，不修改学员函数结果。
    """
    if part not in {"a", "b"}:
        raise ValueError("只保存 A/B 检查日志，part 必须是 a 或 b")
    started = datetime.now().astimezone()
    run_dir = log_root.resolve() / (
        f"{part}_{started.strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:8]}"
    )
    # mkdir 默认继承父目录权限；不使用会收紧权限的临时目录创建方式。
    run_dir.mkdir(parents=True)
    log_path = run_dir / "console.log"
    info_path = run_dir / "run_info.json"
    info = {
        "part": part,
        "started_at": started.isoformat(),
        "finished_at": None,
        "origin": os.environ.get("DAY41_RUN_ORIGIN", "unconfirmed"),
        "python_executable": sys.executable,
        "working_directory": str(Path.cwd()),
        "arguments": sys.argv,
        "exercise_sha256": hashlib.sha256(EXERCISE.read_bytes()).hexdigest(),
        "console_log": str(log_path),
        "state": "running",
    }
    _save_info(info_path, info)
    print(f"本次 {part.upper()} 检查日志目录：{run_dir}")
    with log_path.open("w", encoding="utf-8") as log:
        try:
            with (
                redirect_stdout(_Tee(sys.stdout, log)),
                redirect_stderr(_Tee(sys.stderr, log)),
            ):
                check_fn(learner_fn)
        except BaseException as error:
            # 仅在进程边界留回溯并立即重抛，不把错误改成成功或吞掉中断。
            info["state"] = "failed"
            info["error"] = f"{type(error).__name__}: {error}"
            traceback.print_exc(file=log)
            raise
        else:
            info["state"] = "completed"
        finally:
            log.flush()
            info["finished_at"] = datetime.now().astimezone().isoformat()
            _save_info(info_path, info)
    # completed 仅表示检查运行结束；对照是否一致仍看日志，不能只看退出码。
    print(f"控制台输出已保存：{log_path}")
    print(f"运行信息已保存：{info_path}")
