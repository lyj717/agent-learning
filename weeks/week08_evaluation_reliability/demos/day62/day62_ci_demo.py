"""Day62 演示：把离线检查接进 GitHub Actions，真实调用留手动入口。

前面 Day61 已经有确定性检查；今天让它们在每次 push 时自动跑，
但把花钱的真实模型调用挡在手动按钮后面。
本演示不调用模型，只讲 workflow 的结构、边界与预算。
"""


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def main() -> None:
    """按用途、触发、两个 job、密钥、预算、坑的顺序讲一次 CI。"""
    say("Day61 的检查在本机能跑；今天要回答：换一台干净机器，push 后还能不能跑。")
    say("目标：push 自动跑离线检查，真实模型只在手动点击时跑一次。")

    say("\n一、CI 是什么")
    say("CI 是每次提交后，由远端拉一份干净代码、按固定步骤安装和测试。")
    say("它不依赖你的本机环境，所以能发现「只在我电脑上能跑」的问题。")

    say("\n二、什么时候触发")
    say("push：提交到 main 时跑离线检查。")
    say("pull_request：有人提 PR 时也跑离线检查。")
    say("workflow_dispatch：网页上手动点按钮，才允许跑真实模型。")
    say("三者的区别要写进 `on:`；不要把 live 放到 push 上。")

    say("\n三、两个 job 的分工")
    say("offline：checkout → setup-python → 安装依赖 → ruff → pytest。")
    say("  0 次模型调用，不需要密钥，失败会阻断合并。")
    say("live：只在 workflow_dispatch 且输入 run_live=true 时运行。")
    say("  1 次最小调用（day62_live_smoke.py），用 secrets 注入密钥，失败不重试。")
    say("两个 job 分开，离线失败不会花额度，live 失败也不会拖住日常提交。")

    say("\n四、密钥怎么进来")
    say(
        "仓库 Settings → Secrets and variables → Actions 里存 LLM_API_KEY、LLM_BASE_URL。"
    )
    say("workflow 里写 `${{ secrets.LLM_API_KEY }}`，不要写明文。")
    say("PR 来自 fork 时拿不到 secrets；所以 live 不放 pull_request。")

    say("\n五、预算的几道闸")
    say("1. live 只挂在 workflow_dispatch，不挂 push/PR；")
    say("2. 手动输入默认 false，必须显式勾选；")
    say("3. 脚本只发 1 次请求，max_tokens=32，超时 30 秒；")
    say("4. job 设 timeout-minutes，防止卡死；")
    say("5. 客户端 max_retries=0，失败不自动重试。")

    say("\n六、YAML 上容易踩的坑")
    say(
        "1. `on:` 在 YAML 1.1 里可能被解析成布尔 True；检查器会兼容，但你自己读时要留意。"
    )
    say("2. `${{ }}` 是 GitHub 表达式，不要被引号或缩进拆开。")
    say("3. job 的 `if:` 是字符串，别写成 YAML 布尔。")
    say("4. `run:` 里多行用 `|`，每行命令缩进一致。")
    say("5. 依赖装 `requirements-ci.txt`，不要把本地向量模型和 Qdrant 拖进 CI。")

    say("\n七、本地能验到哪一步")
    say("能验 YAML 结构、命令和离线测试；真正的 Actions 运行要 push 后在仓库页看。")
    say("在没看到远端绿灯之前，不说「CI 已通过」。")

    say("\n下一步：写 .github/workflows/ci.yml，跑检查器，再 push 观察一次。")


if __name__ == "__main__":
    main()
