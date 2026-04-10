# ---------------------------------------------------------
# [Stage 1: 构建环境] - 使用 2026 黄金基准 Python 3.12
# ---------------------------------------------------------
FROM python:3.12-slim AS builder

# 1. 设置环境变量，确保输出不被缓冲，提升日志实时性
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# 将 Poetry 加入系统路径
ENV PATH="$POETRY_HOME/bin:$PATH"

# 2. 设置工作目录
WORKDIR /app

# 3. 安装系统依赖 (build-essential 为 Nuitka 编译/本地扩展预留)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. 安装 Poetry (2026 官方推荐安装方式)
RUN curl -sSL https://install.python-poetry.org | python3 -

# 5. 复制依赖描述文件（优先利用 Docker 缓存层）
COPY pyproject.toml poetry.lock* ./

# 6. 安装项目生产依赖 (跳过开发环境包)
RUN poetry config virtualenvs.create false && \
    (poetry install --no-root --without dev || poetry install --no-root --no-dev)


# ---------------------------------------------------------
# [Stage 2: 最终生产镜像]
# ---------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# 从构建阶段复制已安装的包 (Site-packages)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 7. 复制项目所有代码
COPY . .

# 8. 设置生产环境变量
# 关键修复：确保 PYTHONPATH 包含 /app 以便正确识别 bridge 包
ENV ENV_MODE=production \
    PYTHONPATH=/app:/app/src \
    PYTHONUNBUFFERED=1

# ---------------------------------------------------------
# 9. [核心安全策略] 执行 Nova v5.0 环境熔断自检
# 如果容器环境与 Nuitka 编译目标或 3.12 基准不符，构建将在此失败。
# ---------------------------------------------------------
RUN python scripts/deploy_check.py

# 10. 暴露服务端口 (根据 bridge.caller 的实际需求调整)
EXPOSE 8000

# ---------------------------------------------------------
# 11. [启动命令修复] 使用 -m 参数确保模块寻址正确
# ---------------------------------------------------------
# 使用 ENTRYPOINT 配合 -m，能彻底解决 "No module named 'bridge'" 报错
ENTRYPOINT ["python", "-m", "bridge.caller"]