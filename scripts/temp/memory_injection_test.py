#!/usr/bin/env python3
"""
Step 1: Memory Injection Test
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from persistence.mempalace_integration import MemPalaceIntegration


def test_memory_injection():
    """测试记忆注入"""
    print("=== Step 1: Memory Injection ===")
    
    # 初始化MemoryManager
    memory_manager = MemPalaceIntegration()
    print("✓ 初始化MemPalaceIntegration成功")
    
    # 注入项目信息
    project_info = {
        "content": "I am starting a new project called 'Project-Z' in 'D:/Projects/Project-Z'. The primary tech stack is Next.js 14 and the deployment target is Vercel.",
        "metadata": {
            "project_name": "Project-Z",
            "path": "D:/Projects/Project-Z",
            "tech_stack": "Next.js 14",
            "deployment_target": "Vercel"
        },
        "keywords": ["Project-Z", "Next.js", "Vercel", "deployment"]
    }
    
    # 添加记忆
    add_result = memory_manager.add_memory(project_info)
    
    if add_result["success"]:
        print(f"✓ 记忆注入成功: {add_result['memory_id']}")
        print(f"  - 存储到分层: {add_result['tier']}")
        
        # 验证记忆是否存储
        search_results = memory_manager.search("Project-Z")
        print(f"✓ 搜索验证: 找到 {len(search_results)} 条相关记忆")
        
        # 直接检查记忆分层中的内容
        print("✓ 直接检查记忆分层:")
        found = False
        for tier, memories in memory_manager.memory_tiers.items():
            for memory_id, memory in memories.items():
                if "Project-Z" in memory.get("content", "") or "Project-Z" in str(memory.get("context", {})):
                    print(f"  - 在{tier.value}分层中找到记忆: {memory_id}")
                    print(f"  - 内容: {memory['content'][:100]}...")
                    print(f"  - 项目名称: {memory.get('context', {}).get('project_name', 'N/A')}")
                    print(f"  - 路径: {memory.get('context', {}).get('path', 'N/A')}")
                    print(f"  - 技术栈: {memory.get('context', {}).get('tech_stack', 'N/A')}")
                    print(f"  - 部署目标: {memory.get('context', {}).get('deployment_target', 'N/A')}")
                    found = True
                    break
            if found:
                break
        
        if not found:
            print("✗ 未在记忆分层中找到Project-Z相关记忆")
    else:
        print(f"✗ 记忆注入失败: {add_result['error']}")
    
    print("\n=== Step 1 完成 ===")


if __name__ == "__main__":
    test_memory_injection()
