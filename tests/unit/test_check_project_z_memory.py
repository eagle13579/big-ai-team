#!/usr/bin/env python3
"""
Check if Project-Z memory exists in any memory tier
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from persistence.mempalace_integration import MemPalaceIntegration, MemoryTier


def check_project_z_memory():
    """检查Project-Z记忆是否存在"""
    print("=== 检查Project-Z记忆 ===")
    
    # 初始化MemoryManager
    memory_manager = MemPalaceIntegration()
    print("✓ 初始化MemPalaceIntegration成功")
    
    # 检查所有记忆分层
    found = False
    for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
        memories = memory_manager.memory_tiers.get(tier, {})
        print(f"\n✓ 检查{tier.value}分层，共{len(memories)}条记忆")
        
        for memory_id, memory in memories.items():
            content = memory.get("content", "")
            context = memory.get("context", {})
            
            # 检查是否包含Project-Z
            if "Project-Z" in content or "Project-Z" in str(context):
                print(f"  ✓ 找到Project-Z记忆: {memory_id}")
                print(f"    - 内容: {content[:100]}...")
                print(f"    - 项目名称: {context.get('project_name', 'N/A')}")
                print(f"    - 路径: {context.get('path', 'N/A')}")
                print(f"    - 技术栈: {context.get('tech_stack', 'N/A')}")
                print(f"    - 部署目标: {context.get('deployment_target', 'N/A')}")
                found = True
    
    if not found:
        print("\n✗ 未找到Project-Z相关记忆")
    else:
        print("\n✓ 找到Project-Z相关记忆")
    
    # 尝试使用不同的搜索词
    print("\n=== 尝试不同的搜索词 ===")
    search_terms = ["Project-Z", "Next.js", "Vercel", "D:/Projects/Project-Z"]
    
    for term in search_terms:
        results = memory_manager.search(term, limit=3)
        print(f"  - 搜索 '{term}': 找到 {len(results)} 条结果")
        if results:
            for i, result in enumerate(results[:2], 1):
                print(f"    {i}. {result.get('content', '')[:50]}...")


if __name__ == "__main__":
    check_project_z_memory()
