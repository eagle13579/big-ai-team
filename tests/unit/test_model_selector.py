import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.model_selector import (
    ModelSelector,
    TaskType,
    ComplexityLevel,
    select_model_for_task
)


def test_task_type_detection():
    """测试任务类型检测"""
    selector = ModelSelector()
    
    # 测试不同任务类型
    test_cases = [
        ("帮我写一段 Python 代码来计算斐波那契数列", TaskType.CODE_GENERATION),
        ("分析一下当前市场趋势", TaskType.ANALYSIS),
        ("帮我搜索一下最新的技术新闻", TaskType.SEARCH),
        ("总结一下这篇文章的主要内容", TaskType.SUMMARY),
        ("把这段英文翻译成中文", TaskType.TRANSLATION),
        ("写一篇关于AI未来的科幻小说", TaskType.CREATIVE_WRITING),
        ("计算一下这个数学题的答案", TaskType.REASONING),
        ("帮我调研一下 Ace 浏览器", TaskType.TEXT_GENERATION),
    ]
    
    print("🎯 任务类型检测测试:")
    for task, expected_type in test_cases:
        detected_type = selector.detect_task_type(task)
        status = "✅" if detected_type == expected_type else "❌"
        print(f"{status} 任务: '{task[:40]}...'")
        print(f"   检测结果: {detected_type.value} (期望: {expected_type.value})")
        print()


def test_complexity_estimation():
    """测试复杂度评估"""
    selector = ModelSelector()
    
    test_cases = [
        ("你好", ComplexityLevel.SIMPLE),
        ("帮我写个简单的脚本", ComplexityLevel.MEDIUM),
        ("请帮我分析一下这个项目的架构，包括各个模块的功能", ComplexityLevel.COMPLEX),
        ("请帮我开发一个完整的AI助手，需要包括登录注册、用户管理、数据存储、数据分析等功能，还要考虑性能优化和安全性，写一个详细的技术方案", ComplexityLevel.VERY_COMPLEX),
    ]
    
    print("📊 复杂度评估测试:")
    for task, expected_level in test_cases:
        estimated_level = selector.estimate_complexity(task)
        status = "✅" if estimated_level == expected_level else "❌"
        print(f"{status} 任务长度: {len(task)} 字符")
        print(f"   评估结果: {estimated_level.value} (期望: {expected_level.value})")
        print()


def test_model_selection():
    """测试模型选择"""
    selector = ModelSelector()
    
    test_cases = [
        "你好，简单的简单的简单的简单的简单的简单的简单的简单的简单的简单的",
        "帮我写一段 Python 代码来计算斐波那契数列",
        "请帮我分析一下这个项目的架构",
        "请帮我开发一个完整的AI助手，需要包括登录注册、用户管理、数据存储、数据分析等功能",
        "帮我搜索一下最新的技术新闻",
        "总结一下这篇文章的主要内容",
    ]
    
    print("🤖 模型选择测试（优先免费模型）:")
    for task in test_cases:
        selected_model = selector.select_model(task, prefer_free=True)
        print(f"任务: '{task[:50]}...")
        print(f"选择的模型: {selected_model.name}")
        print(f"成本: {'免费 🆓' if selected_model.cost_per_1k_tokens == 0 else f'${selected_model.cost_per_1k_tokens * 1000:.2f} 每百万 token'}")
        print(f"能力: {', '.join(selected_model.capabilities)}")
        print()
    
    print("-" * 60)
    print("🤖 模型选择测试（不优先免费模型）:")
    for task in test_cases[:2]:
        selected_model = selector.select_model(task, prefer_free=False)
        print(f"任务: '{task[:50]}...")
        print(f"选择的模型: {selected_model.name}")
        print(f"成本: {'免费 🆓' if selected_model.cost_per_1k_tokens == 0 else f'${selected_model.cost_per_1k_tokens * 1000:.2f} 每百万 token'}")
        print(f"能力: {', '.join(selected_model.capabilities)}")
        print()


def test_select_model_for_task_simple():
    """测试简化接口"""
    print("🔧 简化接口测试:")
    task = "帮我写一段 Python 代码来计算斐波那契数列"
    model_name = select_model_for_task(task)
    print(f"任务: '{task}'")
    print(f"选择的模型: {model_name}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 模型选择器测试")
    print("=" * 60)
    print()
    
    test_task_type_detection()
    print("-" * 60)
    test_complexity_estimation()
    print("-" * 60)
    test_model_selection()
    print("-" * 60)
    test_select_model_for_task_simple()
    print("-" * 60)
    print("✅ 所有测试完成!")
