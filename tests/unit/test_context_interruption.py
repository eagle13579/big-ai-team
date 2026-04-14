#!/usr/bin/env python3
"""
Step 2: Context Interruption Test
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.persistence.mempalace_integration import MemPalaceIntegration


def test_context_interruption():
    """测试上下文中断"""
    print("=== Step 2: Context Interruption ===")

    # 初始化MemoryManager
    memory_manager = MemPalaceIntegration()
    print("✓ 初始化MemPalaceIntegration成功")

    # 注入5个不相关的问题/信息
    unrelated_infos = [
        {
            "content": "What is the syntax for a list comprehension in Python?",
            "metadata": {"topic": "Python", "type": "programming"},
            "keywords": ["Python", "list comprehension", "syntax"],
        },
        {
            "content": "Who won the Nobel Prize in Physics in 2023?",
            "metadata": {"topic": "science", "type": "general knowledge"},
            "keywords": ["Nobel Prize", "Physics", "2023"],
        },
        {
            "content": "How to calculate the factorial of a number in Python?",
            "metadata": {"topic": "Python", "type": "programming"},
            "keywords": ["Python", "factorial", "calculation"],
        },
        {
            "content": "What is the capital of France?",
            "metadata": {"topic": "geography", "type": "general knowledge"},
            "keywords": ["France", "capital", "geography"],
        },
        {
            "content": "What is the difference between a list and a tuple in Python?",
            "metadata": {"topic": "Python", "type": "programming"},
            "keywords": ["Python", "list", "tuple", "difference"],
        },
    ]

    print("✓ 开始注入不相关信息...")
    for i, info in enumerate(unrelated_infos, 1):
        add_result = memory_manager.add_memory(info)
        if add_result["success"]:
            print(f"  ✓ 注入不相关信息 {i}: {add_result['memory_id']}")
        else:
            print(f"  ✗ 注入不相关信息 {i} 失败: {add_result['error']}")

    # 验证短期记忆分层中的记忆数量
    from persistence.mempalace_integration import MemoryTier

    short_term_count = len(memory_manager.memory_tiers.get(MemoryTier.SHORT_TERM, {}))
    medium_term_count = len(memory_manager.memory_tiers.get(MemoryTier.MEDIUM_TERM, {}))
    long_term_count = len(memory_manager.memory_tiers.get(MemoryTier.LONG_TERM, {}))
    total_count = short_term_count + medium_term_count + long_term_count
    print(f"✓ 短期记忆分层中的记忆数量: {short_term_count}")
    print(f"✓ 中期记忆分层中的记忆数量: {medium_term_count}")
    print(f"✓ 长期记忆分层中的记忆数量: {long_term_count}")
    print(f"✓ 总记忆数量: {total_count}")

    print("\n=== Step 2 完成 ===")
    print("✓ 已注入5个不相关信息，短期记忆缓冲区已被填充")


if __name__ == "__main__":
    test_context_interruption()
