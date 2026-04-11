#!/usr/bin/env python3
"""
测试 Agent-Reach 集成功能
"""

import asyncio
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

from src.execution.executor import ToolExecutor
from src.skills.agent_reach import AgentReachSkill


async def test_agent_reach_skill():
    """测试 AgentReachSkill"""
    print("=== 测试 AgentReachSkill ===")
    
    # 创建技能实例
    skill = AgentReachSkill()
    
    # 测试获取技能能力
    capabilities = skill.get_capabilities()
    print(f"技能能力: {capabilities}")
    
    # 测试读取网页
    print("\n测试读取网页...")
    result = await skill._execute_async({
        "action": "read_webpage",
        "params": {"url": "https://example.com"}
    })
    print(f"结果: {result}")
    
    # 测试搜索 Twitter
    print("\n测试搜索 Twitter...")
    result = await skill._execute_async({
        "action": "search_twitter",
        "params": {"query": "AI Agent", "limit": 5}
    })
    print(f"结果: {result}")
    
    # 测试获取 YouTube 字幕
    print("\n测试获取 YouTube 字幕...")
    result = await skill._execute_async({
        "action": "get_youtube_transcript",
        "params": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    })
    print(f"结果: {result}")

async def test_tool_executor():
    """测试 ToolExecutor 集成"""
    print("\n=== 测试 ToolExecutor 集成 ===")
    
    # 创建执行器实例
    executor = ToolExecutor()
    
    # 获取可用工具
    available_tools = executor.get_available_tools()
    print(f"可用工具: {available_tools}")
    
    # 测试通过 ToolExecutor 执行 agent_reach
    print("\n测试通过 ToolExecutor 执行 agent_reach...")
    result = await executor.execute("agent_reach", {
        "action": "read_webpage",
        "params": {"url": "https://example.com"}
    })
    print(f"结果: {result}")

async def main():
    """主测试函数"""
    await test_agent_reach_skill()
    await test_tool_executor()
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main())
