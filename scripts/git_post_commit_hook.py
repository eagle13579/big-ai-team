#!/usr/bin/env python3
"""
Git Post-commit Hook - 自动记录代码变更到模块验证报告
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from scripts.change_tracker import GitHookHandler

def main():
    """主函数"""
    try:
        GitHookHandler.handle_commit()
        print("[INFO] 代码变更已记录到模块验证报告")
    except Exception as e:
        print(f"[ERROR] 记录变更时出错: {e}")
        # 不阻止提交
        pass

if __name__ == '__main__':
    main()