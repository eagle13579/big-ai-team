#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 __pycache__ 目录
"""
import os
import shutil

def cleanup_pycache():
    """清理所有 __pycache__ 目录"""
    count = 0
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                pycache_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(pycache_path)
                    print(f"删除: {pycache_path}")
                    count += 1
                except Exception as e:
                    print(f"删除失败 {pycache_path}: {e}")
    
    print(f"\n✅ 清理完成！删除了 {count} 个 __pycache__ 目录")

if __name__ == "__main__":
    cleanup_pycache()
