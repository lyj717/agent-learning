"""Day62 补充演示：从零理解 CI——push 之后远端到底做了什么。

之前的 CI 演示假设你见过 GitHub Actions；这份按「一台干净机器」的故事重讲：
workflow、event、job、step、runner、action、secret 各是什么，
以及 push 和手动按钮分别触发哪条路径。不联网、不调用模型。
"""

import platform
import sys


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def show_toy_workflow() -> None:
    """打印一份最小 workflow，并逐行说明它在说什么。"""
    say("四、一份最小 workflow（只是示意，不是今天的答案）")
    say("")
    say("name: Demo")
    say("on: [push]")
    say("jobs:")
    say("  hello:")
    say("    runs-on: ubuntu-latest")
    say("    steps:")
    say("      - uses: actions/checkout@v4")
    say("      - run: python --version")
    say("")
    say("逐行翻译：")
    say("  name       这份 workflow 叫什么，Actions 页面显示这个名字。")
    say("  on         什么时候触发；[push] 表示每次 push。")
    say("  jobs       要干的活，可以有多份，默认并行。")
    say("  hello      这个 job 的编号，页面和日志里用它区分。")
    say("  runs-on    用哪种机器；ubuntu-latest 是 GitHub 提供的干净 Linux。")
    say("  steps      这个 job 里按顺序执行的步骤。")
    say("  uses       ？用别人写好的 action，比如 checkout 把代码拉下来。")
    say("  run        ？直接执行一条 shell 命令。")


def main() -> None:
    """按故事、角色、词表、最小 YAML、两条路径、看页面的顺序讲 CI。"""
    say("Day62 的 CI 演示假设你见过 Actions；这份从零讲：push 之后发生了什么。")
    say("先记住一句话：CI 是「每次提交，换一台干净机器，按你写的步骤重跑一遍」。")

    say("\n一、为什么需要 CI：本机 ≠ 干净机器")
    say("你的本机有 .venv、.env、下载好的模型、装过的包、改过的 PATH。")
    say("所以「在我电脑上能跑」可能只是这些残留帮你兜住了。")
    say("CI 每次新建一台 Ubuntu，只按仓库里的依赖文件安装，再跑测试。")
    say("它专门用来暴露：漏写依赖、路径写死、只在 Windows 能跑、忘了提交文件。")

    say("\n二、push 之后的时间线")
    say("1. 你 git push 到 GitHub。")
    say("2. GitHub 看仓库里 .github/workflows/ 下的 YAML。")
    say("3. 发现某个 workflow 的 on 包含 push，决定运行它。")
    say("4. 分配一台干净的 Ubuntu runner。")
    say(
        "5. 按 job 里的 steps 顺序执行：checkout → setup-python → pip install → ruff → pytest。"
    )
    say("6. 每步退出码为 0 算通过；任何一步非 0，这个 job 变红，后面的步骤默认不再跑。")
    say("7. Actions 页面留下日志；你可以点开每一步看输出。")

    say("\n三、六个词，先认清角色")
    say("workflow：一份 YAML，放在 .github/workflows/ 下。")
    say("event：什么时候跑，写在 on 下（push / pull_request / workflow_dispatch）。")
    say("job：一份工作，占一台 runner；不同 job 默认并行。")
    say("step：job 里的一步，要么 uses 一个现成 action，要么 run 一条命令。")
    say("runner：GitHub 提供的临时机器；跑完就销毁，不保留你的 .venv。")
    say("secret：仓库设置里加密保存的值，运行时注入，日志里会打码。")

    show_toy_workflow()

    say("\n五、今天这份 workflow 的两条路径")
    say("路径 A：push 或 PR")
    say("  只启动 offline job：装 requirements-ci.txt、ruff、pytest。")
    say("  live job 的 if 条件为假，页面显示 skipped（灰色），不花钱。")
    say("路径 B：Actions 页面手动 Run workflow，勾 run_live")
    say("  启动 live job：注入 secrets，跑 day62_live_smoke.py 一次，最多 1 次调用。")
    say("  它和 offline 是两个 job，互不阻塞；日常提交只走 A。")

    say("\n六、为什么 live 不能挂 push")
    say("1. 每次提交都花钱，额度不可控；")
    say("2. 密钥要暴露给自动运行，风险更大；")
    say("3. 模型慢或限流时，会把日常 CI 拖红，掩盖真正的离线问题。")
    say("所以 live 只留手动按钮，默认 false，必须显式勾选。")

    say("\n七、Actions 页面怎么看")
    say("黄色圆点=正在跑；绿色勾=通过；红色叉=失败；灰色横线=跳过。")
    say("点进一次运行，左侧是两个 job；点 job 展开每一步的日志。")
    say("先看红色那一步的最后 20 行，再往上找第一条报错。")

    say("\n八、本机预演能做什么、不能做什么")
    say("能：把 CI 的命令原样跑一遍，确认 ruff、格式、pytest 本地是绿的。")
    say("不能：完全模拟 GitHub 的干净机器和 secrets；真正的结论要看远端运行。")
    say(f"本机 Python={platform.python_version()}；可执行文件={sys.executable}")
    say("CI 里用 setup-python 装 3.13，不依赖你本机的路径。")

    say("\n九、最容易误解的三件事")
    say("1. CI 不是部署；它只跑检查，不会把服务发到线上。")
    say("2. CI 不读你的 .env；密钥只能从 GitHub Secrets 注入。")
    say("3. 本地 pytest 绿，不等于 CI 绿；依赖、路径、系统差异都可能在远端才暴露。")

    say("\n下一步：先跑这份演示，再按题目说明写 ci.yml；写完先跑检查器。")


if __name__ == "__main__":
    main()
