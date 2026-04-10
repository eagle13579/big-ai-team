@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ======================================================
echo 🚀 Nova 部署助手 (2026 工业级标准版)
echo ======================================================

:: 1. 检查 Docker 是否运行
docker version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] 错误：Docker 引擎未启动！
    echo [i] 请先打开 Docker Desktop 软件，确保左下角显示为绿色。
    pause
    exit /b
)

:: 2. 检查 Dockerfile
if not exist "Dockerfile" (
    echo [!] 错误：未在 %cd% 找到 Dockerfile
    pause
    exit /b
)

:: 3. 开始构建
echo [1/2] 🛠️ 正在构建镜像 [big-ai-app:latest]...
docker build -t big-ai-app:latest .

if %ERRORLEVEL% NEQ 0 (
    echo [!] 镜像构建失败，请检查 Dockerfile 内容。
    pause
    exit /b
)

:: 4. 运行容器
echo [2/2] 🚀 镜像构建成功，正在启动容器...
echo ------------------------------------------------------
docker run --rm big-ai-app:latest

echo ------------------------------------------------------
echo ✅ 执行完毕！
pause