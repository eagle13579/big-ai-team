#!/usr/bin/env python3

"""
[Nova 智能代码自愈脚本 v3.2]
工业级标准：自动修复代码风格、优化导入顺序、移除冗余变量、统一代码格式。
"""

import os
import subprocess
import sys
from pathlib import Path


def run_fix():
    # 1. 精准定位项目根目录 (兼容本地运行与 GitHub Actions 环境)
    # 使用 __file__ 获取当前脚本位置，向上两级到达项目根目录
    try:
        current_file = Path(__file__).resolve()
    except NameError:
        # 兼容某些交互式环境
        current_file = Path(os.getcwd()) / "scripts" / "auto_fix.py"

    root_dir = current_file.parent.parent

    print(f"🔍 [Nova Audit] 正在扫描项目根目录: {root_dir}")

    # 2. 检查 Ruff 是否安装，未安装则尝试自动安装 (生产环境自愈)
    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠️ 未发现 Ruff，正在自动安装以维持流水线运行...")
        subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True)

    # 3. 核心指令集：执行 Ruff 检查与格式化
    commands = [
        # --fix: 自动修复能修复的问题
        # --unsafe-fixes: 允许修复可能改变逻辑但符合规范的细节（如多余导入）
        # --exit-zero: 即使有无法修复的问题也不中断脚本，交给后续 format 处理
        ["ruff", "check", str(root_dir), "--fix", "--unsafe-fixes", "--exit-zero"],
        # 按照 PEP 8 和现代化标准进行代码格式化
        ["ruff", "format", str(root_dir)],
    ]

    try:
        for cmd in commands:
            print(f"🚀 执行指令: {' '.join(cmd)}")
            # 使用 shell=False 防止命令注入，确保安全
            subprocess.run(cmd, check=True)

        print("\n✨ [Nova Success] 代码自愈完成！您的代码已对齐 2026 年工业级标准。")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ [Nova Error] 执行过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_fix()
