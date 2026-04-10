#!/usr/bin/env python3
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
    "move_scripts.py",
]

dest_dir = "scripts"

# 确保目标目录存在
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# 移动文件
for script in scripts:
    if os.path.exists(script):
        try:
            shutil.move(script, os.path.join(dest_dir, script))
            print(f"移动: {script} -> {dest_dir}/{script}")
        except Exception as e:
            print(f"移动失败 {script}: {e}")
    else:
        print(f"跳过: {script} (文件不存在)")

print("\n🎉 脚本移动完成！")
