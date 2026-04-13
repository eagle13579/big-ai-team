#!/usr/bin/env python3
"""
测试技能注册表是否能够正确发现和注册技能
"""

from src.skills import skill_registry

print("=== 技能注册表测试 ===")
print(f"可用技能数量: {len(skill_registry.get_all_skills())}")
print(f"技能列表: {skill_registry.get_skill_names()}")

# 测试获取单个技能
print("\n=== 测试获取单个技能 ===")
for skill_name in skill_registry.get_skill_names():
    skill_class = skill_registry.get_skill(skill_name)
    if skill_class:
        print(f"技能: {skill_name}")
        print(f"  类名: {skill_class.__name__}")
        print(f"  描述: {skill_class.description}")
        if hasattr(skill_class, 'args_schema') and skill_class.args_schema:
            print(f"  参数架构: {skill_class.args_schema.__name__}")
        else:
            print(f"  参数架构: None")
    else:
        print(f"技能 {skill_name} 未找到")

print("\n=== 测试完成 ===")
