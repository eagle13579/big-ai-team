<<<<<<< New base: init
import os
import shutil

# 定义根目录和目标目录
root_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(root_dir, "scripts")

# 确保scripts目录存在
if not os.path.exists(scripts_dir):
    os.makedirs(scripts_dir)

# 要移动的脚本文件列表
script_files = [
    "association_retrieval_test.py",
    "check_project_z_memory.py",
    "conflict_resolution_test.py",
    "context_interruption_test.py",
    "diagnose_logging_mece.py",
    "memory_injection_test.py",
    "move_scripts.py",
    "test_hook.py",
    "test_logging_fix.py",
    "test_mempalace_integration.py",
    "traceability_verification.py"
]

# 移动文件
for file_name in script_files:
    src_path = os.path.join(root_dir, file_name)
    dst_path = os.path.join(scripts_dir, file_name)
    
    if os.path.exists(src_path):
        try:
            shutil.move(src_path, dst_path)
            print(f"已移动: {file_name} -> scripts/{file_name}")
        except Exception as e:
            print(f"移动失败 {file_name}: {e}")
    else:
        print(f"文件不存在: {file_name}")

print("\n文件移动完成！")
|||||||
=======
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
>>>>>>> Current commit: init
