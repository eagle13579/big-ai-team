#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构核心组件为模块化结构
"""
import os
import shutil

# 核心组件列表
components = ['dispatcher', 'factory', 'planner', 'state']

# 源目录
core_dir = "src/lib/core"

for component in components:
    # 创建组件目录和 source 子目录
    component_dir = os.path.join(core_dir, component)
    source_dir = os.path.join(component_dir, 'source')
    
    # 确保目录存在
    os.makedirs(source_dir, exist_ok=True)
    
    # 源文件路径
    src_file = os.path.join(core_dir, f"{component}.py")
    # 目标文件路径
    dest_file = os.path.join(source_dir, "index.py")
    
    # 移动并重命名文件
    if os.path.exists(src_file):
        shutil.move(src_file, dest_file)
        print(f"移动: {component}.py -> {dest_file}")
    
    # 创建 __init__.py 文件
    init_file = os.path.join(component_dir, "__init__.py")
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write("# Dispatcher module\n")
    
    source_init_file = os.path.join(source_dir, "__init__.py")
    with open(source_init_file, 'w', encoding='utf-8') as f:
        f.write("# Source module\n")

print("\n✅ 重构完成！")
