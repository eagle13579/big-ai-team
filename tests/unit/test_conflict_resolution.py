#!/usr/bin/env python3
"""
Step 4: Conflict Resolution Test
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from persistence.mempalace_integration import MemoryTier, MemPalaceIntegration


def test_conflict_resolution():
    """测试冲突解决"""
    print("=== Step 4: Conflict Resolution ===")

    # 初始化MemoryManager
    memory_manager = MemPalaceIntegration()
    print("✓ 初始化MemPalaceIntegration成功")

    # 找到Project-Z记忆
    project_z_memory = None
    project_z_memory_id = None

    for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
        memories = memory_manager.memory_tiers.get(tier, {})
        for memory_id, memory in memories.items():
            if "Project-Z" in str(memory.get("content", "")) or "Project-Z" in str(
                memory.get("context", {})
            ):
                project_z_memory = memory
                project_z_memory_id = memory_id
                print(f"✓ 找到Project-Z记忆: {memory_id}")
                print(
                    f"  - 当前部署目标: {memory.get('context', {}).get('deployment_target', 'N/A')}"
                )
                break
        if project_z_memory:
            break

    if not project_z_memory:
        print("✗ 未找到Project-Z记忆")
        return

    # 更新部署目标
    print("\n✓ 开始更新部署目标...")
    print("  输入: Actually, change the deployment target for 'Project-Z' to AWS Amplify.")

    # 更新记忆
    updated_context = project_z_memory.get("context", {})
    updated_context["deployment_target"] = "AWS Amplify"

    update_result = memory_manager.update_memory(
        memory_id=project_z_memory_id, context=updated_context
    )

    if update_result["success"]:
        print(f"✓ 更新成功: {update_result}")
    else:
        print(f"✗ 更新失败: {update_result['error']}")
        return

    # 验证更新
    print("\n✓ 验证更新结果...")
    print("  输入: Where am I deploying 'Project-Z' now?")

    # 重新查找记忆
    updated_memory = None
    for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
        memories = memory_manager.memory_tiers.get(tier, {})
        if project_z_memory_id in memories:
            updated_memory = memories[project_z_memory_id]
            break

    if updated_memory:
        new_deployment_target = updated_memory.get("context", {}).get("deployment_target", "N/A")
        print(f"✓ 当前部署目标: {new_deployment_target}")

        if new_deployment_target == "AWS Amplify":
            print("✓ 验证成功: 部署目标已更新为AWS Amplify")
        else:
            print(f"✗ 验证失败: 部署目标仍然是{new_deployment_target}")
    else:
        print("✗ 未找到更新后的Project-Z记忆")

    # 检查所有Project-Z记忆的部署目标
    print("\n✓ 检查所有Project-Z记忆的部署目标...")
    for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
        memories = memory_manager.memory_tiers.get(tier, {})
        for memory_id, memory in memories.items():
            if "Project-Z" in str(memory.get("content", "")) or "Project-Z" in str(
                memory.get("context", {})
            ):
                deployment_target = memory.get("context", {}).get("deployment_target", "N/A")
                print(f"  - 记忆 {memory_id}: {deployment_target}")

    print("\n=== Step 4 完成 ===")


if __name__ == "__main__":
    test_conflict_resolution()
