FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 安装 sed，处理 requirements.lock，然后安装 Python 依赖
# 确保 requirements.lock 文件在项目根目录
COPY ./requirements.lock /app/requirements.lock
RUN sed '/^-e/d' /app/requirements.lock > /app/requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

# 复制应用程序代码
# app 目录包含您的 FastAPI 应用代码
COPY ./app /app/app

# 复制初始数据库文件
# 注意：为了数据持久化，请在运行容器时使用数据卷挂载此文件或其所在目录
COPY ./app_database.db /app/app_database.db

# 运行 FastAPI 应用
# 假设 fastapi-cli (提供 fastapi run) 已通过 requirements.txt 安装
# app/main.py 路径是相对于 WORKDIR (/app/) 的，所以它指向 /app/app/main.py
CMD ["fastapi", "run", "app/main.py"]