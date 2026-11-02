"""AI 维护的通用运行留证；Tee 沿用 Week05 已验证实现。

run_logged 保存运行模式、来源、参数、摘要、控制台和异常；不填写学员观察。
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


def run_logged(
    part: str,
    action: Callable[[Path], None],
    config: dict,
    exercise_path: Path,
    log_root: Path,
    *,
    origin_env: str = "DAY44_RUN_ORIGIN",
) -> None:
    """运行 action(本次新输出目录)，保存来源、配置与异常；返回 None。

    前五个参数必填；config 只放可公开的运行配置。origin_env 可指定来源变量名，
    默认读 DAY44_RUN_ORIGIN，供 Day44 的既有调用保持原行为。
    默认 unconfirmed；AI 验证显式标记 ai_validation，不自动认定学员亲跑。
    运行失败保留日志并原样抛错；不覆盖已有目录，不修改数据与学员函数。
    """
    started = datetime.now().astimezone()
    run_dir = log_root.resolve() / (
        f"{part}_{started.strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:8]}"
    )
    run_dir.mkdir(parents=True)
    log_path = run_dir / "console.log"
    info_path = run_dir / "run_info.json"
    info = {
        "part": part,
        "config": config,
        "started_at": started.isoformat(),
        "finished_at": None,
        "origin": os.environ.get(origin_env, "unconfirmed"),
        "python_executable": sys.executable,
        "working_directory": str(Path.cwd()),
        "arguments": sys.argv,
        "exercise_path": str(exercise_path.resolve()),
        "exercise_sha256": hashlib.sha256(exercise_path.read_bytes()).hexdigest(),
        "state": "running",
    }

    def save_info() -> None:
        """刷新本次运行信息，失败时也保留最终状态。"""
        info_path.write_text(
            json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    save_info()
    print(f"本次 {part} 日志目录：{run_dir}")
    with log_path.open("w", encoding="utf-8") as log:
        try:
            with (
                redirect_stdout(_Tee(sys.stdout, log)),
                redirect_stderr(_Tee(sys.stderr, log)),
            ):
                print(f"运行模式={part}；来源={info['origin']}；配置={config}")
                action(run_dir)
        except BaseException as error:
            info["state"] = "failed"
            info["error"] = f"{type(error).__name__}: {error}"
            traceback.print_exc(file=log)
            raise
        else:
            info["state"] = "completed"
        finally:
            info["finished_at"] = datetime.now().astimezone().isoformat()
            save_info()
    print(f"控制台及结构化结果已保存：{run_dir}")
