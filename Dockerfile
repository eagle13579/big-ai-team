# ---------------------------------------------------------
# 单阶段构建 - 使用 2026 黄金基准 Python 3.12
# ---------------------------------------------------------
FROM python:3.12-slim

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

# 5. 复制项目所有代码
COPY . .

# 6. 安装项目生产依赖 (跳过开发环境包)
RUN pip install --upgrade setuptools wheel && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only main && \
    # 确保安装opentelemetry-instrumentation-redis
    pip install opentelemetry-instrumentation-redis

# 7. 设置生产环境变量
# 关键修复：确保 PYTHONPATH 包含 /app 以便正确识别 bridge 包
ENV ENV_MODE=production \
    PYTHONPATH=/app:/app/src \
    PYTHONUNBUFFERED=1

# 8. [核心安全策略] 执行 Nova v5.0 环境熔断自检
# 如果容器环境与 Nuitka 编译目标或 3.12 基准不符，构建将在此失败。
RUN python scripts/tools/deploy_check.py

# 9. 暴露服务端口 (根据 bridge.caller 的实际需求调整)
EXPOSE 8000

# 10. 添加健康检查脚本
RUN mkdir -p /app && echo '#!/usr/bin/env python3' > /app/health_check.py && \
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

# 11. [启动命令修复] 使用 -m 参数确保模块寻址正确
# 使用 ENTRYPOINT 配合 -m，能彻底解决 "No module named 'bridge'" 报错
ENTRYPOINT ["python", "-m", "bridge.caller"]