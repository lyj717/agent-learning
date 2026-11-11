# Day55 B：把 Week07 的离线问答服务打进镜像。
# 镜像只包含运行所需代码与依赖，不含密钥、虚拟环境、运行日志和 outputs。
FROM python:3.13-slim

# 不写 .pyc、日志立刻刷新、pip 不留缓存，减小镜像体积。
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先装依赖，再拷代码：改代码时不会让依赖层缓存失效。
COPY requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY weeks ./weeks

EXPOSE 8000

# 0.0.0.0 才能从容器外访问；127.0.0.1 只会在容器内部监听。
CMD ["uvicorn", "weeks.week07_production.demos.day55.day55_server:app", "--host", "0.0.0.0", "--port", "8000"]
