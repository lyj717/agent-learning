"""Day62 检查器：只读 .github/workflows/ci.yml，检查触发、两个 job、密钥与预算。

不调用模型、不推送；YAML 结构对不上时逐条打印，最后统一报错。
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"


def _on(data: dict) -> dict:
    """取 on 段；PyYAML 可能把 on 解析成布尔 True。"""
    raw = data.get("on")
    if raw is None:
        raw = data.get(True)
    return raw if isinstance(raw, dict) else {}


def _jobs(data: dict) -> dict:
    """取 jobs 段；不是字典时返回空字典。"""
    raw = data.get("jobs")
    return raw if isinstance(raw, dict) else {}


def _steps(job: dict) -> list[dict]:
    """取 job 的 steps；过滤掉非字典项。"""
    raw = job.get("steps")
    if not isinstance(raw, list):
        return []
    return [step for step in raw if isinstance(step, dict)]


def _runs(job: dict) -> list[str]:
    """收集一个 job 里所有 run 字符串。"""
    return [str(step.get("run", "")) for step in _steps(job)]


def _uses(job: dict) -> list[str]:
    """收集一个 job 里所有 uses 字符串。"""
    return [str(step.get("uses", "")) for step in _steps(job)]


def _env(job: dict) -> dict:
    """合并 job 级与各 step 级的 env。"""
    merged = dict(job.get("env") or {})
    for step in _steps(job):
        merged.update(step.get("env") or {})
    return merged


def _all_strings(value: object) -> list[str]:
    """递归收集 YAML 里所有字符串，用于明文密钥扫描。"""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        found: list[str] = []
        for item in value:
            found.extend(_all_strings(item))
        return found
    if isinstance(value, dict):
        found = []
        for item in value.values():
            found.extend(_all_strings(item))
        return found
    return []


def _checks(data: dict, path: Path) -> list[tuple[str, bool, str]]:
    """按 10 条验收点逐项判断，返回（名称, 是否通过, 说明）。"""
    on = _on(data)
    jobs = _jobs(data)
    offline = jobs.get("offline") if isinstance(jobs.get("offline"), dict) else {}
    live = jobs.get("live") if isinstance(jobs.get("live"), dict) else {}
    dispatch = on.get("workflow_dispatch")
    inputs = dispatch.get("inputs") if isinstance(dispatch, dict) else {}
    run_live = inputs.get("run_live") if isinstance(inputs, dict) else None

    offline_runs = _runs(offline)
    offline_uses = _uses(offline)
    live_runs = _runs(live)
    live_condition = str(live.get("if", ""))
    secrets = _env(live)
    timeout = live.get("timeout-minutes")

    checks: list[tuple[str, bool, str]] = []
    checks.append(("文件存在", path.is_file(), str(path)))
    checks.append(("YAML 可解析", True, "safe_load 成功"))

    triggers = all(key in on for key in ("push", "pull_request", "workflow_dispatch"))
    checks.append(("三种触发", triggers, f"on={sorted(str(key) for key in on)}"))

    boolean_input = (
        isinstance(run_live, dict)
        and run_live.get("type") == "boolean"
        and run_live.get("default") is False
    )
    checks.append(
        (
            "手动输入 run_live",
            boolean_input,
            f"type/default={run_live!r}",
        )
    )

    offline_ok = bool(offline) and "ubuntu" in str(offline.get("runs-on", ""))
    checks.append(("offline job", offline_ok, f"runs-on={offline.get('runs-on')!r}"))

    setup_ok = any("actions/checkout" in item for item in offline_uses) and any(
        "actions/setup-python" in item for item in offline_uses
    )
    install_ok = any("pip install" in item for item in offline_runs)
    python_ok = any(
        str(step.get("with", {}).get("python-version", "")).startswith("3.13")
        for step in _steps(offline)
        if "actions/setup-python" in str(step.get("uses", ""))
    )
    checks.append(
        (
            "offline 安装 Python 与依赖",
            setup_ok and install_ok and python_ok,
            f"checkout/setup={setup_ok}；pip={install_ok}；3.13={python_ok}",
        )
    )

    ruff_check = any("ruff check" in item for item in offline_runs)
    ruff_format = any("ruff format --check" in item for item in offline_runs)
    pytest_ok = any("pytest" in item for item in offline_runs)
    scoped = any(
        "weeks/week08_evaluation_reliability" in item
        for item in offline_runs
        if "ruff" in item
    )
    checks.append(
        (
            "offline 跑 ruff 与 pytest",
            ruff_check and ruff_format and pytest_ok and scoped,
            f"check={ruff_check}；format={ruff_format}；pytest={pytest_ok}；限定本周={scoped}",
        )
    )

    live_ok = (
        bool(live)
        and "ubuntu" in str(live.get("runs-on", ""))
        and "workflow_dispatch" in live_condition
        and (
            "inputs.run_live" in live_condition
            or "event.inputs.run_live" in live_condition
        )
    )
    checks.append(
        (
            "live 只在手动且勾选时运行",
            live_ok,
            f"runs-on={live.get('runs-on')!r}；if={live_condition!r}",
        )
    )

    key = str(secrets.get("LLM_API_KEY", ""))
    smoke_ok = any("day62_live_smoke.py" in item for item in live_runs)
    timeout_ok = isinstance(timeout, int) and 0 < timeout <= 10
    checks.append(
        (
            "live 用密钥、跑冒烟并限时",
            "secrets.LLM_API_KEY" in key and smoke_ok and timeout_ok,
            f"key={key!r}；smoke={smoke_ok}；timeout={timeout!r}",
        )
    )

    strings = _all_strings(data)
    plain_key = any(re.search(r"sk-[A-Za-z0-9]{8,}", item) for item in strings) or any(
        key == "LLM_API_KEY" and "secrets." not in str(value)
        for key, value in secrets.items()
    )
    checks.append(("没有明文密钥", not plain_key, "扫描 sk- 与 LLM_API_KEY"))
    return checks


def run_checks(path: Path = WORKFLOW) -> None:
    """读取 workflow，逐条打印；失败时汇总报错。"""
    print("来源：本地 YAML 静态检查；不调用模型、不推送。")
    if not path.is_file():
        raise AssertionError(f"没有找到 {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise AssertionError(f"YAML 解析失败：{error}") from error
    if not isinstance(data, dict):
        raise TypeError("workflow 顶层不是字典")

    checks = _checks(data, path)
    failures = 0
    for number, (name, passed, detail) in enumerate(checks, start=1):
        print(f"\n检查 {number}｜{name}：{'通过' if passed else '失败'}")
        print(f"  依据：{detail}")
        failures += int(not passed)
    print(f"\n汇总：{len(checks) - failures}/{len(checks)} 通过")
    if failures:
        raise AssertionError("workflow 还有未通过项，详见上方")
