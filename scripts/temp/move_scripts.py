#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动根目录脚本到 scripts/ 目录
"""
import os
import shutil

# 要移动的脚本文件
scripts = [
    "demo_roi_optimizer.py",
    "memory_injection_test.py",
    "traceability_verification.py",
    "cleanup_pycache.py",
    "copy_core_files.py",
    "restructure_core.py",
    "test_refactoring.py"
]

dest_dir = "scripts"

# 确保目标目录存在
os.makedirs(dest_dir, exist_ok=True)

# 移动文件
for script in scripts:
    if os.path.exists(script):
        dest_path = os.path.join(dest_dir, script)
        shutil.move(script, dest_path)
        print(f"移动: {script} -> {dest_path}")
    else:
        print(f"跳过: {script} (文件不存在)")

print("\n✅ 脚本移动完成！")
