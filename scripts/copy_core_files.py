#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复制 core 目录文件到 lib/core 目录
"""
import os
import shutil

# 源目录和目标目录
src_dir = "src/core"
dest_dir = "src/lib/core"

# 确保目标目录存在
os.makedirs(dest_dir, exist_ok=True)

# 复制所有文件
files = os.listdir(src_dir)
for file in files:
    src_path = os.path.join(src_dir, file)
    dest_path = os.path.join(dest_dir, file)
    if os.path.isfile(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"复制: {file} -> {dest_path}")

print("\n✅ 复制完成！")
