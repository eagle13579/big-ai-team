#!/usr/bin/env python3
"""
验证 adapters 目录的状态
"""

import os


# 检查 adapters 目录是否存在
def validate_adapters():
    """验证 adapters 目录的状态"""
    adapters_dir = os.path.join(os.path.dirname(__file__), "src", "access", "adapters")

    if not os.path.exists(adapters_dir):
        print("❌ adapters 目录不存在")
        return False

    # 检查 adapters 目录中的文件
    adapter_files = os.listdir(adapters_dir)
    required_files = ["__init__.py", "base.py", "registry.py"]

    print("📋 adapters 目录验证报告")
    print("-" * 50)
    print(f"📁 目录位置: {adapters_dir}")
    print(f"📄 文件数量: {len(adapter_files)}")
    print("\n📋 核心文件检查:")

    all_passed = True
    for file in required_files:
        if file in adapter_files:
            print(f"✅ {file} - 存在")
        else:
            print(f"❌ {file} - 缺失")
            all_passed = False

    print("\n📋 适配器文件检查:")
    adapter_types = [
        "cli_adapter.py",
        "database.py",
        "llm.py",
        "messaging.py",
        "mobile_adapter.py",
        "monitoring.py",
        "platforms.py",
        "sandbox.py",
        "storage.py",
        "web_adapter.py",
    ]

    for adapter in adapter_types:
        if adapter in adapter_files:
            print(f"✅ {adapter} - 存在")
        else:
            print(f"⚠️ {adapter} - 缺失 (可选)")

    print("\n📋 验证结果:")
    if all_passed:
        print("🎉 所有核心文件验证通过！")
        print("✅ adapters 目录状态: 验证通过")
    else:
        print("❌ 部分核心文件缺失，验证未通过")
        print("❌ adapters 目录状态: 验证失败")

    return all_passed


if __name__ == "__main__":
    validate_adapters()
