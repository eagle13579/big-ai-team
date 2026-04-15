# ---------------------------------------------------------
# 多阶段构建 - 使用 2026 黄金基准 Python 3.12
# ---------------------------------------------------------

# 第一阶段：构建阶段
FROM python:3.12-slim AS builder

# 1. 设置环境变量
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

# 3. 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. 安装 Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# 5. 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 6. 安装项目依赖
RUN pip install --upgrade setuptools wheel && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only main && \
    pip install opentelemetry-instrumentation-redis

# 7. 复制项目代码
COPY . .

# 8. 执行 Nuitka 编译（如果需要）
RUN if [ -f "build_protect.py" ]; then \
    python build_protect.py; \
else \
    python -m nuitka --module core/ --output-dir=dist --show-progress --remove-output && \
    cp -r dist/core/* core/ 2>/dev/null || true; \
fi

# 9. 执行环境熔断自检
RUN python scripts/tools/deploy_check.py

# 第二阶段：运行阶段
FROM python:3.12-slim

# 1. 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV_MODE=production \
    PYTHONPATH=/app:/app/src

# 2. 设置工作目录
WORKDIR /app

# 3. 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. 创建非特权用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 5. 从构建阶段复制文件
COPY --from=builder /app /app

# 6. 设置文件权限
RUN chown -R appuser:appuser /app

# 7. 暴露服务端口
EXPOSE 8000

# 8. 添加健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 9. 添加健康检查脚本
RUN echo '#!/usr/bin/env python3' > /app/health_check.py && \
    echo 'import http.server' >> /app/health_check.py && \
    echo 'import socketserver' >> /app/health_check.py && \
    echo 'import os' >> /app/health_check.py && \
    echo '' >> /app/health_check.py && \
    echo 'class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):' >> /app/health_check.py && \
    echo '    def do_GET(self):' >> /app/health_check.py && \
    echo '        if self.path == "/health":' >> /app/health_check.py && \
    echo '            self.send_response(200)' >> /app/health_check.py && \
    echo '            self.send_header("Content-type", "text/plain")' >> /app/health_check.py && \
    echo '            self.end_headers()' >> /app/health_check.py && \
    echo '            self.wfile.write(b"OK")' >> /app/health_check.py && \
    echo '        else:' >> /app/health_check.py && \
    echo '            self.send_response(404)' >> /app/health_check.py && \
    echo '            self.end_headers()' >> /app/health_check.py && \
    echo '' >> /app/health_check.py && \
    echo 'if __name__ == "__main__":' >> /app/health_check.py && \
    echo '    port = int(os.getenv("HEALTH_CHECK_PORT", "8000"))' >> /app/health_check.py && \
    echo '    with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:' >> /app/health_check.py && \
    echo '        httpd.serve_forever()' >> /app/health_check.py && \
    chmod +x /app/health_check.py

# 10. 切换到非特权用户
USER appuser

# 11. 启动命令
ENTRYPOINT ["python", "-m", "bridge.caller"]