#!/usr/bin/env python3
"""
检查Mempalace记忆库内容
"""

import sys
import os
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from persistence.mempalace_integration import MemPalaceIntegration, MemoryTier


def check_memory_content():
    """检查记忆内容"""
    print("=== Mempalace记忆库内容检查 ===")
    
    # 初始化MemoryManager
    memory_manager = MemPalaceIntegration()
    print(f"✓ 记忆库路径: {memory_manager.palace_path}")
    
    # 检查各分层的记忆数量
    print("\n=== 记忆分层统计 ===")
    total_memories = 0
    for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
        memories = memory_manager.memory_tiers.get(tier, {})
        count = len(memories)
        total_memories += count
        print(f"  {tier.value}: {count} 条记忆")
    print(f"  总计: {total_memories} 条记忆")
    
    # 显示所有记忆的摘要
    print("\n=== 所有记忆内容摘要 ===")
    memory_count = 0
    for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
        memories = memory_manager.memory_tiers.get(tier, {})
        if memories:
            print(f"\n  【{tier.value} 分层】")
            for memory_id, memory in memories.items():
                memory_count += 1
                content = memory.get("content", "")
                context = memory.get("context", {})
                
                # 显示记忆摘要
                print(f"\n  记忆 {memory_count}:")
                print(f"    ID: {memory_id}")
                print(f"    内容: {content[:100]}...")
                if context:
                    print(f"    上下文: {json.dumps(context, ensure_ascii=False)[:100]}...")
                
                # 只显示前10条记忆
                if memory_count >= 10:
                    print(f"\n  ... 还有 {total_memories - 10} 条记忆未显示")
                    break
        if memory_count >= 10:
            break
    
    # 检查特定项目记忆
    print("\n=== 项目记忆检查 ===")
    project_memories = []
    for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
        memories = memory_manager.memory_tiers.get(tier, {})
        for memory_id, memory in memories.items():
            content = memory.get("content", "")
            context = memory.get("context", {})
            
            # 检查是否包含项目信息
            if any(keyword in str(content) + str(context) for keyword in ["Project-Z", "project", "Next.js", "Vercel", "AWS"]):
                project_memories.append({
                    "id": memory_id,
                    "tier": tier.value,
                    "content": content,
                    "context": context
                })
    
    if project_memories:
        print(f"  找到 {len(project_memories)} 条项目相关记忆:")
        for proj_mem in project_memories:
            print(f"\n    记忆 ID: {proj_mem['id']}")
            print(f"    分层: {proj_mem['tier']}")
            print(f"    内容: {proj_mem['content'][:100]}...")
            if proj_mem['context']:
                print(f"    上下文: {json.dumps(proj_mem['context'], ensure_ascii=False)}")
    else:
        print("  未找到项目相关记忆")
    
    # 检查知识图谱
    print("\n=== 知识图谱统计 ===")
    graph_stats = memory_manager.get_knowledge_graph_stats()
    print(f"  节点总数: {graph_stats.get('nodes', 0)}")
    print(f"  边总数: {graph_stats.get('edges', 0)}")
    print(f"  记忆节点: {graph_stats.get('memory_nodes', 0)}")
    print(f"  关键词节点: {graph_stats.get('keyword_nodes', 0)}")
    
    # 检查聚类
    print("\n=== 聚类统计 ===")
    cluster_stats = memory_manager.get_clustering_stats()
    print(f"  聚类总数: {cluster_stats.get('total_clusters', 0)}")
    print(f"  平均聚类大小: {cluster_stats.get('average_cluster_size', 0)}")
    
    # 评估内容合理性
    print("\n=== 内容合理性评估 ===")
    if total_memories == 0:
        print("  ⚠️ 警告: 记忆库为空！")
        print("  可能原因:")
        print("    1. 记忆文件被删除或损坏")
        print("    2. 记忆库路径错误")
        print("    3. 系统重启后记忆未正确加载")
    elif total_memories < 5:
        print(f"  ⚠️ 警告: 记忆数量较少 ({total_memories} 条)")
        print("  建议: 检查是否有记忆丢失")
    else:
        print(f"  ✅ 记忆数量正常: {total_memories} 条")
    
    # 检查是否有重复记忆
    content_hashes = {}
    duplicates = []
    for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
        memories = memory_manager.memory_tiers.get(tier, {})
        for memory_id, memory in memories.items():
            content = memory.get("content", "")
            if content in content_hashes:
                duplicates.append((memory_id, content_hashes[content]))
            else:
                content_hashes[content] = memory_id
    
    if duplicates:
        print(f"  ⚠️ 发现 {len(duplicates)} 对重复记忆")
    else:
        print("  ✅ 未发现重复记忆")
    
    print("\n=== 检查完成 ===")


if __name__ == "__main__":
    check_memory_content()
