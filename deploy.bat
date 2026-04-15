@echo off
echo 开始执行 deploy.bat...
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ======================================================
echo 🚀 Nova 部署助手 (2026 工业级标准版)
echo ======================================================

:: 1. 检查 Python 是否安装
echo [检查] 正在检查 Python 环境...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [!] 错误：Python 未安装或未添加到环境变量！
    echo [i] 请先安装 Python 3.12 或更高版本。
    pause
    exit /b 1
)

:: 2. 运行部署前自动化测试
echo [检查] 正在运行部署前自动化测试...
echo ------------------------------------------------------
python scripts/tools/pre_deploy_test.py
if %ERRORLEVEL% NEQ 0 (
    echo [!] 部署前测试失败，请检查测试报告并修复问题。
    pause
    exit /b 1
)
echo ------------------------------------------------------

:: 3. 检查 Docker 是否运行
echo [检查] 正在检查 Docker 服务状态...
docker version
if %ERRORLEVEL% NEQ 0 (
    echo [!] 错误：Docker 引擎未启动！
    echo [i] 请先打开 Docker Desktop 软件，确保左下角显示为绿色。
    pause
    exit /b 1
)

:: 4. 检查 Dockerfile
echo [检查] 正在检查 Dockerfile 是否存在...
if not exist "Dockerfile" (
    echo [!] 错误：未在 %cd% 找到 Dockerfile
    pause
    exit /b 1
)

:: 5. 开始构建
echo [1/2] 🛠️ 正在构建镜像 [big-ai-app:latest]...
docker build -t big-ai-app:latest .

if %ERRORLEVEL% NEQ 0 (
    echo [!] 镜像构建失败，请检查 Dockerfile 内容。
    pause
    exit /b 1
)

:: 6. 运行容器
echo [2/2] 🚀 镜像构建成功，正在启动容器...
echo ------------------------------------------------------
docker run --rm big-ai-app:latest

echo ------------------------------------------------------
echo ✅ 执行完毕！
pause
exit /b 0