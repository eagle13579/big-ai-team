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
