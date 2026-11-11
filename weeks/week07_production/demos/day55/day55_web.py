"""Day55 C：最简页面入口，返回 HTML 并复用已有的 /ask 路由。

页面只是把 /ask 的 JSON 显示出来；服务端不渲染、不调用模型。
"""

from pathlib import Path

from fastapi.responses import FileResponse

from weeks.week07_production.demos.day52.day52_app import make_app

STATIC_DIR = Path(__file__).resolve().parent / "static"
app = make_app()


@app.get("/")
def page() -> FileResponse:
    """返回最简页面。"""
    return FileResponse(STATIC_DIR / "index.html")
