import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.model_selector import model_selector, select_model_for_task
from src.shared.model_policy_tracker import policy_tracker


def demo_roi_optimizer():
    """演示 ROI 优化器的完整功能"""
    print("=" * 70)
    print("🚀 Big AI Team - 智能 ROI 优化系统演示")
    print("=" * 70)
    print()
    
    # 1. 显示 ROI 报告
    print("📈 第一步：查看当前 ROI 报告")
    print("-" * 70)
    roi_report = policy_tracker.get_roi_report()
    print(f"📊 总模型数: {roi_report['total_models']}")
    print(f"🆓 免费模型数: {roi_report['free_models_count']}")
    print(f"💡 推荐策略: {roi_report['recommendation']}")
    print()
    
    # 2. 列出免费模型
    print("🆓 第二步：查看所有免费模型")
    print("-" * 70)
    free_models = policy_tracker.get_free_models()
    for i, model in enumerate(free_models, 1):
        print(f"{i}. {model.model_name}")
        print(f"   提供商: {model.provider}")
        print(f"   额度: {model.free_quota}")
        if model.notes:
            print(f"   说明: {model.notes}")
        if model.source_url:
            print(f"   链接: {model.source_url}")
        print()
    
    # 3. 演示不同任务的模型选择
    print("🎯 第三步：演示不同任务的智能模型选择")
    print("-" * 70)
    
    test_tasks = [
        {
            "name": "简单问候",
            "task": "你好，请介绍一下你自己",
            "description": "简单对话任务"
        },
        {
            "name": "代码生成",
            "task": "帮我写一段 Python 代码，实现一个快速排序算法，并添加详细注释",
            "description": "代码生成任务"
        },
        {
            "name": "复杂分析",
            "task": "请分析当前 AI 大模型市场的竞争格局，包括主要参与者、技术路线、定价策略，并预测未来 2 年的发展趋势",
            "description": "复杂分析任务"
        },
        {
            "name": "技术搜索",
            "task": "搜索一下最新的大模型技术新闻，特别是关于 GPT-5、Gemini 2.0 和国内大模型的最新动态",
            "description": "搜索任务"
        }
    ]
    
    for test_case in test_tasks:
        print(f"\n📝 任务: {test_case['name']}")
        print(f"📋 描述: {test_case['description']}")
        print(f"💬 任务内容: {test_case['task'][:80]}...")
        
        # 选择模型
        selected_model = model_selector.select_model(
            test_case['task'],
            prefer_free=True,
            estimated_input_tokens=500,
            estimated_output_tokens=1000,
            warn_before_pay=True
        )
        
        print(f"🤖 选择的模型: {selected_model.name}")
        print(f"🏢 提供商: {selected_model.provider}")
        
        # 获取成本预估
        estimate = policy_tracker.estimate_cost(
            selected_model.name,
            500,
            1000
        )
        
        if estimate.is_free:
            print(f"💰 费用: 🆓 免费！({estimate.free_quota_remaining})")
        else:
            print(f"💰 预估费用: ${estimate.estimated_cost:.4f}")
            if estimate.warning:
                print(f"⚠️  {estimate.warning}")
        
        print(f"⚡ 能力: {', '.join(selected_model.capabilities)}")
    
    print()
    print("-" * 70)
    
    # 4. 性价比排行
    print("\n💰 第四步：查看性价比排行榜")
    print("-" * 70)
    cheapest = policy_tracker.get_cheapest_models()
    print("📊 性价比 TOP 10:")
    for i, model in enumerate(cheapest[:10], 1):
        if model.is_free:
            cost_str = "🆓 免费"
        else:
            avg_cost = (model.cost_per_1k_tokens_input + model.cost_per_1k_tokens_output) / 2
            cost_str = f"${avg_cost:.4f}/1K tokens"
        print(f"{i:2d}. {model.model_name:20s} - {cost_str}")
    
    print()
    print("=" * 70)
    print("✅ ROI 优化系统演示完成！")
    print("=" * 70)
    print()
    print("📌 核心特性总结:")
    print("   1. 🆓 优先使用免费模型（GLM-4-Flash、Ollama 本地模型）")
    print("   2. 💰 实时成本预估，花钱前预警")
    print("   3. 🎯 根据任务类型智能匹配模型")
    print("   4. 📊 追踪 17+ 主流模型的定价和政策")
    print("   5. 🇨🇳 特别关注国内大模型（DeepSeek、智谱、月之暗面等）")


if __name__ == "__main__":
    demo_roi_optimizer()
