#!/usr/bin/env python3
"""
测试 MemPalace 核心模块
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bridge.caller import MemPalaceIntegration


def test_core_module():
    """测试核心模块"""
    print("🚀 测试 MemPalace 核心模块")
    print("=" * 50)

    try:
        # 初始化核心模块
        mempalace = MemPalaceIntegration()
        print("✓ 核心模块初始化成功")

        # 测试添加记忆
        print("\n测试添加记忆...")
        result = mempalace.add_memory(
            "测试记忆内容",
            context={"importance": "high", "project": "test"},
            tags=["test", "example"],
        )
        print(f"✓ 添加记忆结果: {result}")

        # 测试搜索
        print("\n测试搜索记忆...")
        search_results = mempalace.search("测试")
        print(f"✓ 搜索结果: {search_results}")

        # 测试获取统计信息
        print("\n测试获取统计信息...")
        stats = mempalace.get_memory_stats()
        print(f"✓ 记忆统计: {stats}")

        # 测试清理重复记忆
        print("\n测试清理重复记忆...")
        cleanup_result = mempalace.cleanup_duplicates()
        print(f"✓ 清理结果: {cleanup_result}")

        print("\n" + "=" * 50)
        print("🎉 所有测试通过！核心模块工作正常")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


if __name__ == "__main__":
    test_core_module()
