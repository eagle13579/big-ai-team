# 使用官方 Python 3.12 镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 pyproject.toml 和 poetry.lock 文件
COPY pyproject.toml poetry.lock* /app/

# 安装 Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# 将 Poetry 加入 PATH
ENV PATH="/root/.local/bin:$PATH"

# 安装项目依赖
RUN poetry config virtualenvs.create false && poetry install --no-root --no-dev

# 复制项目代码
COPY . /app/

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV ENV_MODE=production
ENV PYTHONUNBUFFERED=1

# 启动应用
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
