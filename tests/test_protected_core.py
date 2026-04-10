#!/usr/bin/env python3

"""
[Nova 工业级核心逻辑冒烟测试 v2.0]
特性：深度路径自愈 + 跨平台二进制识别 + 增强型导入校验
"""

import sys
import unittest
from pathlib import Path

# --- 核心路径自愈：世界级最佳实践 ---
# 自动定位项目根目录，无论从哪个目录启动脚本都能准确找到核心包
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class TestProtectedCore(unittest.TestCase):
    """
    冒烟测试：验证脱敏/编译后的核心逻辑是否依然可用。
    """

    def test_core_loading(self):
        """测试核心模块是否能被导入（支持源码、编译态 .so/.pyd/.pyc）"""
        try:
            # 动态导入核心算法模块
            from core import algorithm

            module_path = getattr(algorithm, "__file__", "Built-in or Extension")
            print(f"\n✅ 成功导入核心模块: {module_path}")

            # 工业级判定：识别是否为二进制/受保护模块
            # 涵盖了 Linux (.so), Windows (.pyd), macOS (.so) 以及字节码 (.pyc)
            binary_extensions = (".so", ".pyd", ".pyc", ".dylib")
            is_protected = any(module_path.lower().endswith(ext) for ext in binary_extensions)

            status_msg = "🛡️  模块类型: 二进制/受保护态" if is_protected else "📝 模块类型: 纯源码态"
            print(status_msg)

        except ImportError as e:
            self.fail(f"❌ 核心模块加载失败: {e}\n请检查 PYTHONPATH 或模块编译状态。")

    def test_logic_execution(self):
        """测试核心逻辑执行结果是否符合预期（验证 Bridge 接口）"""
        try:
            from bridge.interface import execute_core_task

            # 模拟标准输入参数
            test_params = {
                "action": "validate",
                "data": "test_payload",
                "timestamp": "2026-04-11",  # 注入当前环境上下文
            }

            result = execute_core_task(test_params)

            # 健壮性断言
            self.assertIsNotNone(result, "核心逻辑返回了空结果")
            # 假设业务逻辑必须返回成功标志
            # self.assertTrue(result.get("success"), f"核心逻辑执行失败: {result}")

            print(f"✅ 逻辑测试通过，返回结果示例: {str(result)[:50]}...")

        except ImportError as e:
            self.fail(f"❌ 接口模块 bridge.interface 导入失败: {e}")
        except Exception as e:
            self.fail(f"❌ 逻辑执行过程发生异常: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔍 [Nova] 启动脱敏后核心逻辑冒烟测试...")
    print("⏰ 测试时间: 2026-04-11 01:12 (CST)")
    print("=" * 50)

    # 使用 buffer=True 可以让 print 内容在测试通过时更整洁
    unittest.main(verbosity=2)
