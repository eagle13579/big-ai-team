#!/usr/bin/env python3
"""
MemPalace 核心逻辑加密构建脚本
使用 Nuitka 将核心 Python 代码编译为二进制模块
"""

import os
import sys
import shutil
import subprocess
import platform


def check_requirements():
    """检查并生成 requirements.txt 文件"""
    requirements = [
        "nuitka",
        "zstandard",
        "numpy",
        "scikit-learn",
        "networkx",
        "mempalace"
    ]
    
    # 生成 requirements.txt 文件
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("# MemPalace 依赖包\n")
        for req in requirements:
            f.write(f"{req}\n")
    
    print("✓ 生成 requirements.txt 文件成功")
    
    # 检查是否安装了 nuitka
    try:
        subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            check=True
        )
        print("✓ Nuitka 已安装")
    except subprocess.CalledProcessError:
        print("⚠️ Nuitka 未安装，正在尝试安装...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "nuitka", "zstandard"],
                check=True
            )
            print("✓ Nuitka 安装成功")
        except subprocess.CalledProcessError:
            print("✗ 安装 Nuitka 失败，请手动安装")
            return False
    
    return True


def build_core():
    """构建核心模块"""
    print("\n开始构建核心模块...")
    
    # 构建命令
    cmd = [
        sys.executable,
        "-m", "nuitka",
        "--module", "core",
        "--include-package=core",
        "--output-dir=dist",
        "--remove-output",
        "--no-pyi-file"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ 构建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 构建失败: {e}")
        return False


def move_binary_files():
    """将生成的二进制文件移回 core/ 目录"""
    print("\n移动二进制文件...")
    
    # 确定二进制文件扩展名
    if platform.system() == "Windows":
        ext = ".pyd"
    else:
        ext = ".so"
    
    # 查找生成的二进制文件
    dist_dir = "dist"
    binary_files = []
    
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            if file.endswith(ext):
                binary_files.append(os.path.join(root, file))
    
    if not binary_files:
        print("✗ 未找到生成的二进制文件")
        return False
    
    # 移动二进制文件到 core/ 目录
    for binary_file in binary_files:
        dest_file = os.path.join("core", os.path.basename(binary_file))
        try:
            shutil.move(binary_file, dest_file)
            print(f"✓ 移动 {binary_file} 到 {dest_file}")
        except Exception as e:
            print(f"✗ 移动文件失败: {e}")
            return False
    
    return True


def clean_up():
    """清理临时文件"""
    print("\n清理临时文件...")
    
    # 删除 dist 目录
    if os.path.exists("dist"):
        try:
            shutil.rmtree("dist")
            print("✓ 删除 dist 目录")
        except Exception as e:
            print(f"✗ 删除 dist 目录失败: {e}")
    
    # 删除核心源码文件（保留 __init__.py）
    core_dir = "core"
    for file in os.listdir(core_dir):
        if file.endswith(".py") and file != "__init__.py":
            try:
                os.remove(os.path.join(core_dir, file))
                print(f"✓ 删除 {file} 源码文件")
            except Exception as e:
                print(f"✗ 删除文件失败: {e}")
    
    return True


def main():
    """主函数"""
    print("🚀 MemPalace 核心逻辑加密构建脚本")
    print("=" * 50)
    
    # 步骤 1: 检查环境
    if not check_requirements():
        print("\n❌ 环境检查失败，退出构建")
        return 1
    
    # 步骤 2: 构建核心模块
    if not build_core():
        print("\n❌ 构建失败，退出")
        return 1
    
    # 步骤 3: 移动二进制文件
    if not move_binary_files():
        print("\n❌ 移动二进制文件失败，退出")
        return 1
    
    # 步骤 4: 清理
    if not clean_up():
        print("\n⚠️ 清理失败，但构建过程已完成")
    
    print("\n" + "=" * 50)
    print("🎉 构建完成！核心逻辑已成功转换为二进制黑盒")
    print("\n使用方法:")
    print("from bridge.caller import MemPalaceIntegration")
    print("mempalace = MemPalaceIntegration()")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
