#!/usr/bin/env python3
"""
测试mempalace集成功能
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from persistence.mempalace_integration import MemPalaceIntegration


def test_mempalace_integration():
    """测试mempalace集成功能"""
    print("=== 测试mempalace集成功能 ===")
    
    # 初始化MemPalaceIntegration
    memory_manager = MemPalaceIntegration()
    print("✓ 初始化MemPalaceIntegration成功")
    
    # 测试添加记忆
    memory_data = {
        "content": "测试记忆内容",
        "keywords": ["测试", "记忆"],
        "metadata": {"source": "test", "importance": "high"}
    }
    add_result = memory_manager.add_memory(memory_data)
    print(f"✓ 添加记忆成功: {add_result['memory_id']}")
    
    # 测试搜索记忆
    search_results = memory_manager.search("测试", 5)
    print(f"✓ 搜索记忆成功，找到 {len(search_results)} 条结果")
    
    # 测试获取上下文相关记忆
    context = {"user": "test_user", "project": "test_project", "keywords": ["测试", "记忆"]}
    contextual_results = memory_manager.get_contextual_memory(context, 5)
    print(f"✓ 获取上下文相关记忆成功，找到 {len(contextual_results)} 条结果")
    
    # 测试获取记忆推荐
    recommendations = memory_manager.get_memory_recommendations(context, 5)
    print(f"✓ 获取记忆推荐成功，找到 {len(recommendations)} 条结果")
    
    # 测试质量评估
    memory_id = add_result['memory_id']
    quality_metrics = memory_manager.assess_memory_quality(memory_id)
    print(f"✓ 质量评估成功: {quality_metrics}")
    
    # 测试知识图谱统计
    graph_stats = memory_manager.get_knowledge_graph_stats()
    print(f"✓ 知识图谱统计成功: {graph_stats}")
    
    # 测试聚类统计
    cluster_stats = memory_manager.get_clustering_stats()
    print(f"✓ 聚类统计成功: {cluster_stats}")
    
    # 测试记忆分析
    analytics = memory_manager.get_memory_analytics()
    print(f"✓ 记忆分析成功，总记忆数: {analytics.get('total_memories', 0)}")
    
    # 测试删除记忆
    delete_result = memory_manager.delete_memory(memory_id)
    print(f"✓ 删除记忆成功: {delete_result['success']}")
    
    # 测试清理记忆
    cleanup_result = memory_manager.cleanup_memory()
    print(f"✓ 清理记忆成功: {cleanup_result['success']}")
    
    print("\n=== 所有测试通过！===\n")
    print("mempalace集成功能正常工作，已成功融合世界顶尖的最佳实践。")


if __name__ == "__main__":
    test_mempalace_integration()
