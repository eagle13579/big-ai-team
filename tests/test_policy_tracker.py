import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.model_policy_tracker import policy_tracker, ModelPolicyTracker


def test_basic_features():
    """测试基本功能"""
    print("=" * 60)
    print("🧪 模型政策追踪器测试")
    print("=" * 60)
    print()
    
    # 1. 测试获取所有模型
    print("📊 测试 1: 获取所有模型政策")
    all_policies = policy_tracker.get_all_policies()
    print(f"✅ 共加载 {len(all_policies)} 个模型政策")
    print()
    
    # 2. 测试获取免费模型
    print("🆓 测试 2: 获取免费模型")
    free_models = policy_tracker.get_free_models()
    print(f"✅ 找到 {len(free_models)} 个免费模型:")
    for model in free_models:
        print(f"   - {model.model_name} ({model.provider}): {model.free_quota}")
    print()
    
    # 3. 测试获取最便宜的模型
    print("💰 测试 3: 获取性价比最高的模型")
    cheapest = policy_tracker.get_cheapest_models()
    print("✅ 性价比排序 (前5个):")
    for i, model in enumerate(cheapest[:5]):
        cost_info = "🆓 免费" if model.is_free else f"${(model.cost_per_1k_tokens_input + model.cost_per_1k_tokens_output)/2:.4f}/1K tokens"
        print(f"   {i+1}. {model.model_name} - {cost_info}")
    print()
    
    # 4. 测试成本预估
    print("🧮 测试 4: 成本预估")
    test_cases = [
        ("ollama-llama3", 1000, 500),
        ("deepseek-chat", 2000, 1000),
        ("gpt-4o", 5000, 2500),
        ("glm-4-flash", 10000, 5000),
    ]
    
    for model_name, input_tokens, output_tokens in test_cases:
        estimate = policy_tracker.estimate_cost(model_name, input_tokens, output_tokens)
        print(f"   模型: {model_name}")
        print(f"   预估输入: {input_tokens} tokens, 输出: {output_tokens} tokens")
        if estimate.is_free:
            print(f"   费用: 🆓 免费！({estimate.free_quota_remaining})")
        else:
            print(f"   费用: ${estimate.estimated_cost:.4f}")
            if estimate.warning:
                print(f"   ⚠️  {estimate.warning}")
        print()
    
    # 5. 测试 ROI 报告
    print("📈 测试 5: ROI 报告")
    roi_report = policy_tracker.get_roi_report()
    print(f"✅ 报告生成时间: {roi_report['generated_at']}")
    print(f"✅ 总模型数: {roi_report['total_models']}")
    print(f"✅ 免费模型数: {roi_report['free_models_count']}")
    print(f"✅ 推荐: {roi_report['recommendation']}")
    print()
    
    print("-" * 60)
    print("✨ 国内大模型精选:")
    domestic_providers = ["deepseek", "zhipu", "moonshot", "lingyi", "doubao"]
    for model in all_policies:
        if model.provider in domestic_providers:
            cost_info = "🆓 免费" if model.is_free else f"${(model.cost_per_1k_tokens_input + model.cost_per_1k_tokens_output)/2:.4f}/1K"
            print(f"   - {model.model_name} ({model.provider}): {cost_info}")
            if model.free_quota:
                print(f"     备注: {model.free_quota}")
            if model.notes:
                print(f"     说明: {model.notes}")
    
    print()
    print("=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_features()
