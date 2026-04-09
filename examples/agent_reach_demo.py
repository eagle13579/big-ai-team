# -*- coding: utf-8 -*-
"""
Agent-Reach 集成演示脚本
展示如何在 Big-AI-Team 中使用 Agent-Reach 的互联网能力
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.skills.agent_reach import AgentReachSkill
from src.skills.agent_reach.channels import channel_manager, PlatformType


async def demo_channel_manager():
    """演示渠道管理器功能"""
    print("\n" + "="*60)
    print("📊 渠道管理器演示")
    print("="*60)
    
    channels = channel_manager.get_all_channels()
    print(f"\n✅ 已注册渠道数量: {len(channels)}")
    
    print("\n📂 按类型分类:")
    for ptype in PlatformType:
        type_channels = channel_manager.get_channels_by_type(ptype)
        if type_channels:
            print(f"  {ptype.value}: {len(type_channels)} 个")
            for ch in type_channels:
                auth = "🔐" if ch.requires_auth else "🔓"
                proxy = "🌐" if ch.requires_proxy else ""
                print(f"    {auth} {ch.name} - {ch.description} {proxy}")
    
    stats = channel_manager.get_channel_stats()
    print(f"\n📈 渠道统计:")
    print(f"  总计: {stats['total_channels']} 个渠道")
    print(f"  需要认证: {stats['auth_required']} 个")
    print(f"  需要代理: {stats['proxy_required']} 个")
    print(f"  开箱即用: {stats['no_config_required']} 个")


async def demo_url_detection():
    """演示 URL 渠道检测"""
    print("\n" + "="*60)
    print("🔗 URL 渠道检测演示")
    print("="*60)
    
    test_urls = [
        ("https://twitter.com/elonmusk/status/123456", "Twitter"),
        ("https://x.com/elonmusk/status/123456", "Twitter"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YouTube"),
        ("https://youtu.be/dQw4w9WgXcQ", "YouTube"),
        ("https://github.com/microsoft/vscode", "GitHub"),
        ("https://www.bilibili.com/video/BV1xx411c7mD", "Bilibili"),
        ("https://www.reddit.com/r/Python/", "Reddit"),
        ("https://www.xiaohongshu.com/explore/123456", "小红书"),
        ("https://weibo.com/123456", "微博"),
        ("https://www.v2ex.com/t/123456", "V2EX"),
        ("https://xueqiu.com/S/SH600519", "雪球"),
        ("https://example.com/article", "Web"),
    ]
    
    print("\n")
    for url, expected in test_urls:
        channel = channel_manager.detect_channel_by_url(url)
        if channel:
            status = "✅" if channel.name == expected.lower() or expected.lower() in channel.name else "⚠️"
            print(f"{status} {url}")
            print(f"   检测到: {channel.name} ({channel.description})")
        else:
            print(f"❌ {url}")
            print(f"   未检测到渠道")


async def demo_skill_execution():
    """演示 Skill 执行"""
    print("\n" + "="*60)
    print("🛠️ Skill 执行演示")
    print("="*60)
    
    skill = AgentReachSkill()
    
    print("\n1️⃣ 运行 Agent-Reach 诊断...")
    result = skill.execute({"action": "doctor", "params": {}})
    
    if result["status"] == "success":
        data = result["observation"]["data"]
        print(f"   状态: {data.get('status', 'unknown')}")
        if "output" in data:
            output_lines = data["output"].split("\n")[:10]
            for line in output_lines:
                if line.strip():
                    print(f"   {line}")
    else:
        print(f"   ⚠️ {result['observation']['message']}")
    
    print("\n2️⃣ 读取网页 (example.com)...")
    result = skill.execute({
        "action": "read_webpage",
        "params": {"url": "https://example.com"}
    })
    
    if result["status"] == "success":
        data = result["observation"]["data"]
        content = data.get("content", "")[:200]
        print(f"   ✅ 成功读取")
        print(f"   长度: {data.get('length', 0)} 字符")
        print(f"   内容预览: {content}...")
    else:
        print(f"   ⚠️ {result['observation']['message']}")
    
    print("\n3️⃣ 搜索 GitHub 仓库 (AI Agent)...")
    result = skill.execute({
        "action": "search_github_repos",
        "params": {"query": "AI Agent", "language": "python", "limit": 5}
    })
    
    if result["status"] == "success":
        data = result["observation"]["data"]
        print(f"   ✅ 搜索完成")
        output = data.get("output", "")[:500]
        print(f"   结果预览:\n{output}...")
    else:
        print(f"   ⚠️ {result['observation']['message']}")
        print(f"   💡 提示: 确保已安装 gh CLI (https://cli.github.com)")


async def demo_workflow_integration():
    """演示工作流集成"""
    print("\n" + "="*60)
    print("🔄 工作流集成演示")
    print("="*60)
    
    print("\n📋 模拟研究工作流: '调研 AI Agent 最新趋势'")
    print("-" * 60)
    
    workflow_steps = [
        ("搜索 Twitter 讨论", "search_twitter", {"query": "AI Agent 2026", "limit": 5}),
        ("搜索 GitHub 项目", "search_github_repos", {"query": "AI Agent framework", "language": "python", "limit": 5}),
        ("搜索 Reddit", "search_reddit", {"query": "AI Agent", "limit": 5}),
    ]
    
    skill = AgentReachSkill()
    results = []
    
    for step_name, action, params in workflow_steps:
        print(f"\n🔍 {step_name}...")
        result = skill.execute({"action": action, "params": params})
        
        if result["status"] == "success":
            print(f"   ✅ 完成")
            results.append({"step": step_name, "status": "success", "data": result["observation"]["data"]})
        else:
            print(f"   ⚠️ 跳过: {result['observation']['message']}")
            results.append({"step": step_name, "status": "skipped", "message": result["observation"]["message"]})
    
    print("\n" + "-" * 60)
    print("📊 工作流执行汇总:")
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"   成功: {success_count}/{len(results)} 步骤")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 Big-AI-Team × Agent-Reach 融合演示")
    print("="*60)
    
    await demo_channel_manager()
    await demo_url_detection()
    await demo_skill_execution()
    await demo_workflow_integration()
    
    print("\n" + "="*60)
    print("✨ 演示完成!")
    print("="*60)
    print("\n📚 更多资源:")
    print("   文档: docs/agent_reach_integration.md")
    print("   测试: tests/unit/test_agent_reach_skill.py")
    print("   源码: src/skills/agent_reach/")


if __name__ == "__main__":
    asyncio.run(main())
