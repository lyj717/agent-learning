# Day70 口头解释：三件套（各 60～90 秒）

先写提纲（关键词即可），然后对着提纲讲一遍，录音或讲给 AI 听都可以。
目标不是背稿，是面试官追问两层还能接住。

## 1. 给谁用

提纲：

- 谁：___个人在资料中查询关键词___（具体到人和应用）
- 不装它现在怎么做：___打开文件夹 Ctrl+F，复制段落给模型___
- 一句话价值：___能够让模型调用工具来检索关键词___

## 2. 怎么用

提纲：

- 安装：___pip install -e .___（命令）
- 配进宿主：___### Claude Desktop___

```json
{
  "mcpServers": {
    "notes": {
      "command": "C:\\path\\to\\python.exe",
      "args": ["-m", "projects.mcp_server.server"],
      "env": {"NOTES_ROOT": "C:\\path\\to\\notes"}
    }
  }
}
```
- 能力：工具 ___search_text,search_notes,read_note ___、资源 ___note://index,note://{+path} ___、提示词 ___review_note___
- 语料怎么指定：___读环境变量 NOTES_ROOT，不设默认值时用仓库里的 notes/ 目录___

## 3. 出问题怎么办

提纲（按「现象 → 先看哪 → 怎么定位」）：

- 工具调用失败：___result.is_error为true_看is_error信息__
- 资源读不到：___mcperror 错误码-32602_看mcperror信息__
- 模型不调工具 / 调错：___tool_calls信息有误 看tool_calls的信息___
- 真实返回不对：___answer不符合事实，先核对引用/原文，再怀疑模型___

## 追问预备（各 1～2 句）

1. MCP 解决什么问题、不解决什么问题？
    解决模型与工具的连接，不解决模型回答的质量
2. 为什么用官方 SDK 的 `MCPServer`，而不是自己手写 JSON-RPC？
    官方SDK能处理 JSON-RPC 帧、初始化握手、schema 生成与校验、版本兼容等；手写这些容易错、难升级
3. 这套东西上生产还差什么？
    功能太过单一，不支持远程多用户以及HTTP 部署、认证、限流、日志观测、安全边界等都需要完善