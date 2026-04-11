#!/usr/bin/env python3
"""
Nova v5.0 环境熔断自检脚本
用于检查容器环境是否与 Nuitka 编译目标或 3.12 基准相符
"""

import platform
import sys


def check_python_version():
    """检查 Python 版本是否符合要求"""
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    # 检查是否为 Python 3.12 或更高版本
    if version.major == 3 and version.minor >= 12:
        print("✅ Python 版本符合要求 (>= 3.12)")
        return True
    else:
        print("❌ Python 版本不符合要求，需要 3.12 或更高版本")
        return False


def check_platform():
    """检查操作系统平台"""
    system = platform.system()
    print(f"操作系统: {system}")
    
    # 支持的平台
    supported_platforms = ["Linux", "Windows"]
    if system in supported_platforms:
        print(f"✅ 操作系统平台 {system} 受支持")
        return True
    else:
        print(f"❌ 操作系统平台 {system} 不受支持")
        return False


def check_environment():
    """检查环境变量"""
    import os
    
    # 检查必要的环境变量
    required_env_vars = ["PYTHONPATH"]
    all_vars_exist = True
    
    for var in required_env_vars:
        if var in os.environ:
            print(f"✅ 环境变量 {var} 已设置: {os.environ[var]}")
        else:
            print(f"⚠️  环境变量 {var} 未设置")
            all_vars_exist = False
    
    return all_vars_exist


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Nova v5.0 环境熔断自检")
    print("=" * 60)
    
    # 执行各项检查
    checks = [
        ("Python 版本", check_python_version),
        ("操作系统平台", check_platform),
        ("环境变量", check_environment),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n🔍 检查: {check_name}")
        print("-" * 40)
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 环境检查通过，容器环境符合要求")
        return 0
    else:
        print("❌ 环境检查失败，容器环境不符合要求")
        return 1


if __name__ == "__main__":
    sys.exit(main())
