#!/usr/bin/env python3
"""
启动自动化变更跟踪系统
"""

import os
import sys
import subprocess
import time

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 检查是否已安装必要的依赖
def check_dependencies():
    """检查依赖"""
    try:
        import watchdog
        print("[INFO] watchdog 已安装")
    except ImportError:
        print("[ERROR] 缺少 watchdog 库，正在安装...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'], check=True)

def install_git_hook():
    """安装 Git Hook"""
    git_hooks_dir = os.path.join(PROJECT_ROOT, '.git', 'hooks')
    post_commit_hook = os.path.join(git_hooks_dir, 'post-commit')
    
    if not os.path.exists(git_hooks_dir):
        print(f"[ERROR] Git 钩子目录不存在: {git_hooks_dir}")
        return
    
    hook_content = f"""#!/bin/sh
# 自动记录代码变更到模块验证报告
python3 "{os.path.join(PROJECT_ROOT, 'scripts', 'git_post_commit_hook.py')}"
"""
    
    with open(post_commit_hook, 'w') as f:
        f.write(hook_content)
    
    # 设置执行权限
    os.chmod(post_commit_hook, 0o755)
    print(f"[INFO] Git Post-commit Hook 已安装到: {post_commit_hook}")

def start_tracker():
    """启动变更跟踪器"""
    tracker_script = os.path.join(PROJECT_ROOT, 'scripts', 'change_tracker.py')
    
    print("[INFO] 启动自动化变更跟踪系统...")
    print("[INFO] 系统将实时监控代码变更并自动更新模块验证报告")
    print("[INFO] 按 Ctrl+C 停止监控")
    print()
    
    # 启动监控进程
    subprocess.run([sys.executable, tracker_script, '--daemon'])

def main():
    """主函数"""
    print("=== 自动化变更跟踪系统 ===")
    print()
    
    # 检查依赖
    check_dependencies()
    
    # 安装 Git Hook
    install_git_hook()
    
    # 启动跟踪器
    start_tracker()

if __name__ == '__main__':
    main()