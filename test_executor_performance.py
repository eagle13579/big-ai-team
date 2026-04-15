#!/usr/bin/env python3
"""
测试执行器性能
"""

import asyncio
import time
from src.execution.executor import ToolExecutor

async def test_thread_pool_management():
    """
    测试线程池管理
    """
    print("=== 测试线程池管理 ===")
    executor = ToolExecutor()
    
    # 等待线程池监控启动
    await asyncio.sleep(2)
    
    # 获取初始线程池大小
    initial_size = executor._thread_pool._max_workers
    print(f"初始线程池大小: {initial_size}")
    
    # 执行一些任务，触发线程池调整
    tasks = []
    for i in range(10):
        task = executor.execute("get_system_status", {})
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # 等待线程池调整
    await asyncio.sleep(5)
    
    # 获取调整后的线程池大小
    adjusted_size = executor._thread_pool._max_workers
    print(f"调整后的线程池大小: {adjusted_size}")
    
    # 获取性能统计
    performance_stats = executor.get_performance_stats()
    print(f"线程池性能统计: {performance_stats['thread_pool']}")
    
    executor.close()
    return initial_size != adjusted_size

async def test_cache_performance():
    """
    测试缓存性能
    """
    print("\n=== 测试缓存性能 ===")
    executor = ToolExecutor()
    
    # 执行相同的任务多次，测试缓存命中
    start_time = time.time()
    
    for i in range(5):
        result = await executor.execute("web_search", {"query": "AI 技术发展"})
        print(f"执行 {i+1} 次: 耗时 {time.time() - start_time:.2f}s, 缓存命中: {result.get('from_cache', False)}")
        start_time = time.time()
    
    # 获取缓存统计
    cache_stats = executor.get_cache_stats()
    print(f"缓存统计: {cache_stats}")
    
    # 获取性能统计
    performance_stats = executor.get_performance_stats()
    print(f"缓存性能统计: {performance_stats['cache']}")
    
    executor.close()
    return cache_stats.get('cache_hit_rate', 0) > 0

async def test_concurrent_execution():
    """
    测试并发执行能力
    """
    print("\n=== 测试并发执行能力 ===")
    executor = ToolExecutor()
    
    # 创建多个任务
    tool_calls = []
    for i in range(20):
        tool_calls.append({
            "tool_name": "web_search",
            "args": {"query": f"测试查询 {i}"},
            "priority": i % 5
        })
    
    # 测试批量执行
    start_time = time.time()
    results = await executor.execute_multiple(tool_calls, max_concurrency=10)
    total_time = time.time() - start_time
    
    print(f"批量执行 {len(tool_calls)} 个任务，耗时: {total_time:.2f}s")
    print(f"平均每个任务耗时: {total_time / len(tool_calls):.2f}s")
    
    # 获取性能统计
    performance_stats = executor.get_performance_stats()
    print(f"并发性能统计: {performance_stats['concurrency']}")
    print(f"执行性能统计: {performance_stats['execution']}")
    
    executor.close()
    return total_time < 10  # 20个任务在10秒内完成

async def test_system_resources():
    """
    测试系统资源使用情况
    """
    print("\n=== 测试系统资源使用情况 ===")
    executor = ToolExecutor()
    
    # 执行一些任务
    tasks = []
    for i in range(15):
        task = executor.execute("web_search", {"query": f"系统资源测试 {i}"})
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # 获取系统资源统计
    performance_stats = executor.get_performance_stats()
    print(f"系统资源使用情况: {performance_stats['system']}")
    
    executor.close()
    return True

async def main():
    """
    主测试函数
    """
    print("开始测试执行器性能...\n")
    
    # 测试线程池管理
    thread_pool_test = await test_thread_pool_management()
    print(f"线程池管理测试: {'通过' if thread_pool_test else '失败'}\n")
    
    # 测试缓存性能
    cache_test = await test_cache_performance()
    print(f"缓存性能测试: {'通过' if cache_test else '失败'}\n")
    
    # 测试并发执行能力
    concurrent_test = await test_concurrent_execution()
    print(f"并发执行测试: {'通过' if concurrent_test else '失败'}\n")
    
    # 测试系统资源使用情况
    system_test = await test_system_resources()
    print(f"系统资源测试: {'通过' if system_test else '失败'}\n")
    
    print("性能测试完成!")

if __name__ == "__main__":
    asyncio.run(main())
