# Day62 题目说明：GitHub Actions 离线 CI + 手动 live

本页是 [入口](day62_ci_exercises.py) 的完整题面。学员的答案不是 Python 函数，
而是 `.github/workflows/ci.yml` 这份 workflow；检查器只做 YAML 静态检查。

## 要交什么

`.github/workflows/ci.yml`，包含两个 job，名字固定为 `offline` 与 `live`。

| 部分 | 要求 |
|---|---|
| 触发 | `push`、`pull_request`、`workflow_dispatch` 三种都要有 |
| 手动输入 | `workflow_dispatch.inputs.run_live`，`type: boolean`，`default: false` |
| `offline` | `ubuntu-latest`；checkout、setup-python（3.13）、安装依赖、ruff、pytest |
| `live` | `ubuntu-latest`；只在 `workflow_dispatch` 且 `run_live` 为真时运行 |
| live 密钥 | `LLM_API_KEY: ${{ secrets.LLM_API_KEY }}`，不得写明文 |
| live 命令 | 运行 `weeks/week08_evaluation_reliability/demos/day62/day62_live_smoke.py` |
| live 限时 | `timeout-minutes` 设为 1～10 的整数 |
| 预算 | offline 0 次模型调用；live 最多 1 次，不自动重试 |

## 固定命令

`offline` 里的检查命令用：

```bash
pip install -r requirements-ci.txt
ruff check weeks/week08_evaluation_reliability tests
ruff format --check weeks/week08_evaluation_reliability tests
pytest -p no:cacheprovider
```

`live` 里的命令用：

```bash
python weeks/week08_evaluation_reliability/demos/day62/day62_live_smoke.py
```

## 检查器的 10 个验收点

| # | 检查 | 期望 |
|---|---|---|
| 1 | 文件存在 | `.github/workflows/ci.yml` |
| 2 | YAML 可解析 | `yaml.safe_load` 成功 |
| 3 | 三种触发 | `push` / `pull_request` / `workflow_dispatch` |
| 4 | 手动输入 | `run_live` 是 boolean、默认 false |
| 5 | `offline` job | 存在，`runs-on` 含 `ubuntu` |
| 6 | 安装步骤 | checkout、setup-python 3.13、`pip install` |
| 7 | 离线检查 | `ruff check`、`ruff format --check`、`pytest`，ruff 限定本周 |
| 8 | `live` 条件 | 含 `workflow_dispatch` 与 `run_live`，`runs-on` 含 `ubuntu` |
| 9 | live 密钥/冒烟/限时 | `secrets.LLM_API_KEY`、`day62_live_smoke.py`、`timeout-minutes` 1～10 |
| 10 | 无明文密钥 | 不出现 `sk-...`，`LLM_API_KEY` 不是明文 |

检查器逐条打印「通过/失败 + 依据」，最后汇总 `x/10`。

## 本地怎么跑

```powershell
# 1. 先写 workflow，再跑静态检查
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day62_ci_exercises.py

# 2. 本地把 CI 的命令各跑一遍
.venv\Scripts\python.exe -m ruff check weeks\week08_evaluation_reliability tests
.venv\Scripts\python.exe -m ruff format --check weeks\week08_evaluation_reliability tests
.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests

# 3. 手动 live 冒烟（只在配置了 .env 时；1 次调用）
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\demos\day62\day62_live_smoke.py
```

## 远端验收

1. 本地检查器 10/10、命令全绿后，提交并 push（推送由学员执行）。
2. 打开 GitHub 仓库的 **Actions** 页，看 `CI` 这次运行：
   - `offline` 应为绿色；
   - `live` 在 push 上应被跳过（skipped），这是预期；
   - 需要真实调用时，手动 **Run workflow**，勾 `run_live`，再观察一次 `live`。
3. 把这次运行的 URL、两个 job 的状态、实际用量/费用写进 [记录](day62_record.md)。
4. **没看到远端运行之前，不写「CI 已通过」。**

## 预算

- offline：0 次模型调用；
- live：1 次，`max_tokens=32`，超时 30 秒，`max_retries=0`，约 0.001 元；
- push/PR 绝不自动跑 live；只有手动勾选才跑。

## 常见坑

- PyYAML 可能把 `on` 解析成布尔 `True`；检查器已兼容，但读 YAML 时要知道。
- `if:` 是字符串，写成 `if: ${{ ... }}` 时注意引号与缩进。
- `run: |` 的多行命令每行缩进要一致。
- 不要把 `LLM_API_KEY` 写进 workflow；只引用 `secrets`。
- `live` 不挂 `pull_request`，fork 的 PR 拿不到 secrets。
