# Day67 记录：打包与宿主配置

> 客观数据照抄终端输出；观察题写你自己的判断，每题 1～2 句。
> 写不出来先空着，跑完检查器回来补。

## 一、运行数据（照抄终端输出）

| 项目 | 实际值 | 从哪来 |
|---|---|---|
| A 组（打包配置） | `8/8` | 全量运行 `outputs/all_20261124_221603_925084_b135604c/` 的第 1～8 组 |
| B 组（README 与许可证） | `8/8` | 同一次运行的第 9～16 组 |
| C 组（模块冒烟） | `2/2` | 同一次运行的第 17～18 组 |
| 合计 | `18/18` | 同一次运行的最后一行 |
| 本次日志目录 | `demos/day67/outputs/all_20261124_221603_925084_b135604c/` | 检查器启动时打印的第一行 |
| 模型调用次数 | `0` | 同目录 `run_info.json` 的 `config.model_calls` |

## 二、可选：自己验一次安装

| 项目 | 结果 |
|---|---|
| `pip install -e . --no-deps --no-build-isolation` | （没记录；试过就把结果填这里） |
| `notes-mcp-server` 空 stdin 是否退出 | （没记录；试过就把结果填这里） |

## 三、观察题

### 1. `[project.scripts]` 右边写的是「模块:函数」，不是脚本路径。装好以后，系统里的 `notes-mcp-server` 命令是怎么找到 `main` 的？

答：因为包已经被装进当前 Python 环境的 site-packages，import 能按模块路径找到它

### 2. Claude Desktop / Cursor / VS Code 三份配置的外层键分别是什么？为什么 `command` 要写绝对路径、`NOTES_ROOT` 要放在 `env` 里？

答：分别是mcpServers，mcpServers，servers；写相对路径可能会找不到，把NOTES_ROOT放在env里方便得到环境变量
env 是宿主启动子进程时设置的环境变量，server 用 os.environ 读；不同机器配不同笔记目录，不改代码

### 3. `NOTES_ROOT` 由谁传？为什么不在 `server.py` 里把它写死成一个路径？不设这个变量时用的是什么？

答：由宿主配置里的 env（或用户 shell）传，保留NOTES_ROOT变化的可能性，不设时用的默认 notes/

### 4. 你选了哪个许可证、为什么？`pyproject.toml` 和 `projects/mcp_server/__init__.py` 两处都有版本号，怎么保证它们不漂？

答：选了MIT，因为我希望别人零门槛复用和修改，并且这个规模的项目不需要额外的专利条款
看pyproject.toml里的版本号，projects/mcp_server/__init__.py里的版本号必须和pyproject.toml一致

## 四、今天的失败与订正

| 现象 | 原因 | 改了什么 | 是否已复跑 |
|---|---|---|---|
|  |  |  |  |
