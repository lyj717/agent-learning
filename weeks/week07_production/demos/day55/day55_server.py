"""Day55 B：容器入口，把 Day51/Day52 的离线问答应用交给 uvicorn。

镜像里只放运行所需的代码与依赖，不读取密钥、不请求模型。
"""

from weeks.week07_production.demos.day52.day52_app import make_app

app = make_app()
