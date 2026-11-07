"""AI 搭好的本机运行环境：临时端口、独立服务进程、就绪等待与停止。

running_server(脚本路径, 本轮输出目录)：在 with 内提供 base_url，退出时停止本轮子进程。
脚本须支持 --serve --port，并提供 GET /health；此处不实现演示或学员的业务。
本文件是运行背景，不要求学员重写 socket、子进程或上下文管理器。
"""

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[4]


@contextmanager
def running_server(worker: Path, run_dir: Path) -> Iterator[str]:
    """启动指定教具脚本；with 中得到本机地址，退出后无论成功失败都停止它。

    worker：已实现 --serve --port 的脚本绝对路径；run_dir：已存在的本轮目录。
    进入 with 后另起 Python 程序执行 worker --serve --port 本轮端口；worker 的 main
    根据 --serve 调用它自己的 serve(port)，不会再次进入默认演示分支。
    服务就绪后 yield 的地址交给 with 的 as 变量；离开 with 后执行 finally 停止服务。
    只绑定 127.0.0.1；端口由操作系统选择。保存 server.log 和 server_info.json。
    启动失败抛 RuntimeError/TimeoutError；端口被其他程序抢占时重跑即可。
    """
    # socket.bind((本机地址, 0))：让操作系统选择空闲端口；本轮随后交给 Uvicorn。
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_socket:
        probe_socket.bind(("127.0.0.1", 0))
        port = probe_socket.getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    metadata = {"base_url": base_url, "port": port, "pid": None, "stopped": False}
    info_path = run_dir / "server_info.json"
    # Popen(参数列表)：启动独立 Python 进程；不用 shell 拼接命令。
    with (run_dir / "server.log").open("w", encoding="utf-8") as server_log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-B",
                "-u",
                "-X",
                "utf8",
                str(worker),
                "--serve",
                "--port",
                str(port),
            ],
            cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            stdout=server_log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        metadata["pid"] = process.pid
        info_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        try:
            deadline = time.perf_counter() + 10
            # timeout 是每次请求的等待上限；trust_env=False 避免本机请求被环境代理转发。
            with httpx.Client(timeout=0.5, trust_env=False) as client:
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("服务启动失败，请看本轮 server.log")
                    try:
                        if client.get(base_url + "/health").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if time.perf_counter() >= deadline:
                        raise TimeoutError("本机服务未在十秒内就绪，请看 server.log")
                    time.sleep(0.05)
            print(
                "运行环境：独立服务进程已就绪；地址：", base_url, "；PID：", process.pid
            )
            yield base_url
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            metadata["stopped"] = True
            info_path.write_text(
                json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
            )
            print("运行环境：本轮服务进程已停止。")
