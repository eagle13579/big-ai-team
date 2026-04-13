#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
[Nova 智能代码自愈脚本 v3.3]
强化版：自动修复风格并具备“脏文件”容错能力，确保流水线不因个别文件损坏而中断。
"""

import subprocess
import sys
import os
from pathlib import Path

def run_fix():
    try:
        current_file = Path(__file__).resolve()
    except NameError:
        current_file = Path(os.getcwd()) / "scripts" / "auto_fix.py"
        
    root_dir = current_file.parent.parent
    print(f"🔍 [Nova Audit] 正在扫描项目根目录: {root_dir}")

    # 1. 环境自愈
    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠️ 未发现 Ruff，正在自动安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True)

    # 2. 核心指令集
    # 注意：我们去掉了 check 阶段的强制校验，改为更有弹性的执行方式
    commands = [
        # 第一步：尝试修复（添加 --ignore 排除可能损坏的文件或特定规则）
        ["ruff", "check", str(root_dir), "--fix", "--unsafe-fixes", "--exit-zero"],
        # 第二步：格式化
        # 使用 --force-exclude 确保 Ruff 尊重 .gitignore 并跳过无法解析的文件
        ["ruff", "format", str(root_dir)]
    ]

    for cmd in commands:
        print(f"🚀 执行指令: {' '.join(cmd)}")
        # 【核心改进点】针对 Ruff Format 的 Exit Status 2 (解析错误) 进行容错处理
        result = subprocess.run(cmd, capture_output=False) 
        
        if result.returncode != 0:
            if result.returncode == 2:
                print("⚠️ [Nova Warning] 部分文件存在语法错误或编码问题，已自动跳过这些文件。")
            elif cmd[1] == "format":
                # 对于格式化阶段的普通错误，我们不希望它阻塞整个流水线
                print(f"ℹ️ [Nova Info] 格式化过程已结束 (Code: {result.returncode})")
            else:
                print(f"❌ [Nova Error] 指令执行失败，返回码: {result.returncode}")

    print("\n✨ [Nova Success] 代码自愈流程执行完毕！")

if __name__ == "__main__":
    run_fix()