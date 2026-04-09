#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将根目录上的文件移动到正确的位置
"""
import os
import shutil

# 定义目标目录
test_dir = "tests/unit"
scripts_dir = "scripts"

# 确保目标目录存在
os.makedirs(test_dir, exist_ok=True)
os.makedirs(scripts_dir, exist_ok=True)

# 定义文件移动规则
file_mapping = {
    # 测试文件 -> tests/unit/
    "association_retrieval_test.py": test_dir,
    "check_project_z_memory.py": test_dir,
    "conflict_resolution_test.py": test_dir,
    "context_interruption_test.py": test_dir,
    "diagnose_logging_mece.py": test_dir,
    "memory_injection_test.py": test_dir,
    "test_hook.py": test_dir,
    "test_logging_fix.py": test_dir,
    "test_mempalace_integration.py": test_dir,
    "traceability_verification.py": test_dir,
    # TypeScript 和 JavaScript 文件 -> scripts/
    "FileExplorerTool.ts": scripts_dir,
    "search-worker.js": scripts_dir,
    "test_file_explorer_stress.ts": test_dir,
    # 脚本文件 -> scripts/
    "move_scripts.py": scripts_dir,
}

# 移动文件
for file_name, target_dir in file_mapping.items():
    if os.path.exists(file_name):
        target_path = os.path.join(target_dir, file_name)
        # 重命名测试文件，确保以 test_ 开头
        if target_dir == test_dir and not file_name.startswith("test_"):
            new_file_name = f"test_{file_name}"
            target_path = os.path.join(target_dir, new_file_name)
            print(f"移动并重命名: {file_name} -> {target_path}")
            shutil.move(file_name, target_path)
        else:
            print(f"移动: {file_name} -> {target_path}")
            shutil.move(file_name, target_path)
    else:
        print(f"文件不存在: {file_name}")

print("\n文件移动完成！")
