#!/usr/bin/env python3
"""
测试 bridge 层和 core 层之间的集成
"""

import os
import sys
import unittest
from unittest.mock import patch

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from bridge.caller import CoreLoader, MemPalaceCaller, run_task


class TestBridgeCoreIntegration(unittest.TestCase):
    """测试 bridge 层和 core 层之间的集成"""

    def test_run_task_add(self):
        """测试 run_task 函数的 add 操作"""
        result = run_task("add", content="集成测试记忆")
        self.assertTrue(result)

    def test_run_task_search(self):
        """测试 run_task 函数的 search 操作"""
        result = run_task("search", query="集成测试")
        self.assertIsInstance(result, list)

    def test_run_task_status(self):
        """测试 run_task 函数的 status 操作"""
        result = run_task("status")
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)

    def test_mempalace_caller(self):
        """测试 MemPalaceCaller 类"""
        caller = MemPalaceCaller()
        
        # 测试添加记忆
        result = caller.add_memory("测试记忆", context={"importance": "high"}, tags=["test"])
        self.assertTrue(result)
        
        # 测试搜索
        result = caller.search("测试")
        self.assertIsInstance(result, list)

    def test_core_loader_singleton(self):
        """测试 CoreLoader 的单例模式"""
        core1 = CoreLoader.get_core()
        core2 = CoreLoader.get_core()
        self.assertIs(core1, core2)

    @patch('importlib.import_module')
    def test_core_loader_error(self, mock_import_module):
        """测试 CoreLoader 加载失败的情况"""
        # 模拟导入失败
        mock_import_module.side_effect = ImportError("模块不存在")
        
        from bridge.caller import LoaderError
        with self.assertRaises(LoaderError):
            CoreLoader.get_core()

    def test_run_task_error_handling(self):
        """测试 run_task 的错误处理"""
        # 传递无效的操作
        result = run_task("invalid_action")
        # 应该返回状态信息，而不是 None
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()