"""Day50：独立认识请求 ID 贯穿阶段、耗时和失败事件，供问答路径日志练习迁移。"""

import json
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def main() -> None:
    """用独立的文件查找案例展示关联 ID，不提供问答整合或通用包装函数。"""
    print("Week07 的服务失败后要能找到那次请求；这份演示解决‘几行日志怎样串在一起’。")
    print("学完能让一次请求的多条事件共用 ID，再在 B 里用于检索和回答阶段。")
    print("\n一、是什么：request_id 是一次请求的标签；同一次沿用，不同次重新生成。")
    print("为什么：日志顺序可能交错，仅靠前后位置会把两次请求混起来。")
    print("场景：查一份本地资料失败，想知道哪次查找、花了多久、失败类型是什么。")
    print("\n二、接口：from uuid import uuid4；uuid4() 无必填参数，返回 UUID 对象。")
    print(".hex 取 32 位十六进制字符串。它不是用户身份、会话历史或业务幂等键。")
    print("import time；time.perf_counter() 返回浮点秒数，两次相减后乘 1000 得毫秒。")
    print("只用差值计时，不把它当日期；datetime 的日期用途与它不同。")

    def execute(run_dir: Path) -> None:
        """生成两次独立查找，每次开始与失败共享一个随机请求 ID。"""
        path = run_dir / "events.jsonl"

        def emit(event: dict) -> None:
            """打印并立刻追加一个事件；这是已讲过的保存格式。"""
            # 保存位置 path 已由外层 execute 确定，调用 emit 时只需传事件字典。
            # dumps：字典转 JSON 字符串；这里省略 indent，不插入排版换行。
            # 每条记录末尾的实际换行由下面 write 显式补上。
            line = json.dumps(event, ensure_ascii=False)
            print(line)
            with path.open("a", encoding="utf-8") as stream:
                stream.write(line + "\n")

        for _ in range(2):
            # uuid4：随机生成一个 UUID；每次请求入口只生成一次。
            request_id = uuid4().hex
            start = {"request_id": request_id, "stage": "load_file", "state": "start"}
            emit(start)
            # perf_counter：取单调的高精度计时读数，用差值算运行秒数。
            started = time.perf_counter()
            try:
                (run_dir / "not_created.md").read_text(encoding="utf-8")
            except FileNotFoundError as error:
                elapsed_ms = (time.perf_counter() - started) * 1000
                end = {
                    "request_id": request_id,
                    "stage": "load_file",
                    "state": "error",
                    "elapsed_ms": elapsed_ms,
                    "error_type": type(error).__name__,
                }
            emit(end)
        print("两次均为故意触发的文件缺失；每次两条事件同 ID，两次 ID 不同。")
        # loads：单行 JSON 转回字典，随后按 ID 筛选。
        events = [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        ]
        selected_id = events[0]["request_id"]
        print(
            "按第一个 request_id 找回：",
            [event for event in events if event["request_id"] == selected_id],
        )

    run_logged(
        "request_id_demo",
        execute,
        {"mode": "offline_teaching"},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY50_RUN_ORIGIN",
    )
    print(
        "\n三、注意：error_type 只取异常类名；不记录 str(error)，文件路径也可能敏感。"
    )
    print("本例捕获已知缺失继续演示；练习 A 要在记错之后原样 raise，让调用方知道失败。")
    print("单进程按请求关联的阶段日志是今天的最小链路；尚未接入追踪 SDK。")
    print(
        "后续选择一种工具补标准 span、父子关系和跨服务传播，不将普通 ID 冒充标准 trace。"
    )


if __name__ == "__main__":
    main()
