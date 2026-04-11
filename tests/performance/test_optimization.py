#!/usr/bin/env python3
"""
性能优化测试脚本
测试 Redis 缓存、线程池、任务优先级和批量执行的性能效果
"""

import asyncio
import os
import random
import sys
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))

from src.execution.executor import ToolExecutor
from src.skills.agent_reach.skill import AgentReachSkill


async def test_redis_cache_performance():
    """测试 Redis 缓存性能"""
    print("=== 测试 Redis 缓存性能 ===")
    executor = ToolExecutor()
    
    # 测试缓存命中
    start_time = time.time()
    
    # 第一次执行，应该不命中缓存
    result1 = await executor.execute("web_search", {"query": "AI Agent 2026"})
    time1 = time.time() - start_time
    print(f"第一次执行时间: {time1:.4f} 秒")
    
    # 第二次执行，应该命中缓存
    start_time = time.time()
    result2 = await executor.execute("web_search", {"query": "AI Agent 2026"})
    time2 = time.time() - start_time
    print(f"第二次执行时间: {time2:.4f} 秒")
    print(f"缓存加速比: {time1/time2:.2f}x")
    
    # 获取缓存统计信息
    stats = executor.get_cache_stats()
    print(f"缓存统计: {stats}")
    
    executor.close()

async def test_thread_pool_performance():
    """测试线程池性能"""
    print("\n=== 测试线程池性能 ===")
    executor = ToolExecutor()
    
    # 测试并发执行
    start_time = time.time()
    
    # 创建多个任务
    tasks = []
    for i in range(20):
        task = executor.execute("web_search", {"query": f"test {i}"})
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    print(f"并发执行 20 个任务时间: {total_time:.4f} 秒")
    print(f"平均每个任务时间: {total_time/20:.4f} 秒")
    
    executor.close()

async def test_task_priority():
    """测试任务优先级调度"""
    print("\n=== 测试任务优先级调度 ===")
    executor = ToolExecutor()
    
    # 创建不同优先级的任务
    tasks = []
    for i in range(10):
        priority = random.randint(1, 10)
        task = executor.execute("web_search", {"query": f"priority test {i}"}, priority=priority)
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks)
    print("任务优先级调度测试完成")
    
    executor.close()

async def test_batch_execution():
    """测试批量执行能力"""
    print("\n=== 测试批量执行能力 ===")
    executor = ToolExecutor()
    
    # 创建批量任务
    tool_calls = []
    for i in range(30):
        tool_calls.append({
            "tool_name": "web_search",
            "args": {"query": f"batch test {i}"},
            "priority": random.randint(1, 5)
        })
    
    # 测试普通批量执行
    start_time = time.time()
    results1 = await executor.execute_multiple(tool_calls, max_concurrency=5)
    time1 = time.time() - start_time
    print(f"普通批量执行时间: {time1:.4f} 秒")
    
    # 测试带回调的批量执行
    def callback(progress, total, result):
        if progress % 5 == 0:
            print(f"进度: {progress}/{total}")
    
    start_time = time.time()
    results2 = await executor.execute_batch_with_callback(tool_calls, callback, max_concurrency=5)
    time2 = time.time() - start_time
    print(f"带回调的批量执行时间: {time2:.4f} 秒")
    
    executor.close()

async def test_agent_reach_batch():
    """测试 AgentReachSkill 的批量执行能力"""
    print("\n=== 测试 AgentReachSkill 批量执行能力 ===")
    skill = AgentReachSkill()
    
    # 创建批量任务
    batch_params = []
    for i in range(10):
        batch_params.append({
            "action": "read_webpage",
            "params": {"url": "https://example.com"},
            "priority": random.randint(1, 5)
        })
    
    # 测试普通批量执行
    start_time = time.time()
    results1 = await skill.execute_batch(batch_params, max_concurrency=3)
    time1 = time.time() - start_time
    print(f"AgentReach 普通批量执行时间: {time1:.4f} 秒")
    
    # 测试带优先级的批量执行
    start_time = time.time()
    results2 = await skill.execute_batch_with_priority(batch_params, max_concurrency=3)
    time2 = time.time() - start_time
    print(f"AgentReach 带优先级的批量执行时间: {time2:.4f} 秒")

async def main():
    """主测试函数"""
    await test_redis_cache_performance()
    await test_thread_pool_performance()
    await test_task_priority()
    await test_batch_execution()
    await test_agent_reach_batch()
    print("\n=== 性能测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main())