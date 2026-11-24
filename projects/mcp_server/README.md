# notes MCP Server

## 给谁用、解决什么问题

一个可以安装、配置、真正用起来的 MCP Server

## 安装
在仓库根目录执行（需要 Python 3.11+）:

```powershell
pip install -e .
```

装完会得到 notes-mcp-server 命令

## 配置到宿主

### Claude Desktop
配置文件在 `%APPDATA%\Claude\claude_desktop_config.json`：

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
### Cursor
项目根放 .cursor/mcp.json
```json
    {
        "mcpServers": {
            "notes": {
                "command": "C:\\path\\to\\notes-mcp-server.exe",
                "args": [],
                "env": {"NOTES_ROOT": "C:\\path\\to\\notes"}
            }
        }
    }
```
### VS Code
```json
    {
        "servers": {
            "notes": {
                "type": "stdio",
                "command": "C:\\path\\to\\notes-mcp-server.exe",
                "args": [],
                "env": {"NOTES_ROOT": "C:\\path\\to\\notes"}
            }
        }
    }
```
## 可用能力

TOOL:
search_text 按行检索关键词，返回命中的行号与原文。
search_notes 在本地 Markdown 笔记本里按关键词检索，返回来源文件、行号与原文。
read_note 按名字读一篇笔记的全文，名字写错返回错误。
RESOURCES:
note://index 列出所有相对路径，用一个换行符连接。
note://{+path} 按相对路径读一篇笔记的全文。
PROMPTS:
review_note 返回一段让模型复盘当前文件的提示词。


## 环境变量

读环境变量 NOTES_ROOT，不设默认值时用仓库里的 notes/ 目录

## 已知限制

只支持检索Markdown格式文件
不支持写入文件
不支持远程多用户
坏编码会静默跳过

## 许可证

MIT 理由：希望别人零门槛复用和修改，这个规模的项目不需要额外的专利条款
