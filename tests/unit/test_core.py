#!/usr/bin/env python3
"""
测试 MemPalace 核心模块
"""

import os
import sys
import unittest
from unittest.mock import patch

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.algorithm import MemPalaceCore
from core.algorithm import run as core_run


class TestMemPalaceCore(unittest.TestCase):
    """测试 MemPalace 核心模块"""

    def setUp(self):
        """设置测试环境"""
        self.mempalace = MemPalaceCore(palace_path="./test_mempalace")

    def tearDown(self):
        """清理测试环境"""
        import shutil
        if os.path.exists("./test_mempalace"):
            shutil.rmtree("./test_mempalace")

    def test_initialization(self):
        """测试初始化功能"""
        self.assertTrue(os.path.exists("./test_mempalace"))
        self.assertEqual(self.mempalace.palace_path, os.path.abspath("./test_mempalace"))

    def test_add_memory(self):
        """测试添加记忆功能"""
        # 测试基本添加
        result = self.mempalace.add_memory("测试记忆内容")
        self.assertTrue(result)

        # 测试带上下文和标签的添加
        result = self.mempalace.add_memory(
            "测试记忆内容2",
            context={"importance": "high", "project": "test"},
            tags=["test", "example"]
        )
        self.assertTrue(result)

    def test_search(self):
        """测试搜索功能"""
        # 测试基本搜索
        results = self.mempalace.search("测试")
        self.assertIsInstance(results, list)

        # 测试带限制和上下文的搜索
        results = self.mempalace.search(
            "测试",
            limit=10,
            context={"project": "test"}
        )
        self.assertIsInstance(results, list)

    def test_run_add_action(self):
        """测试 run 方法的 add 操作"""
        params = {
            "action": "add",
            "content": "测试内容",
            "context": {"importance": "high"},
            "tags": ["test"]
        }
        result = self.mempalace.run(params)
        self.assertTrue(result)

    def test_run_search_action(self):
        """测试 run 方法的 search 操作"""
        params = {
            "action": "search",
            "query": "测试",
            "limit": 5
        }
        result = self.mempalace.run(params)
        self.assertIsInstance(result, list)

    def test_run_status_action(self):
        """测试 run 方法的默认状态操作"""
        params = {}
        result = self.mempalace.run(params)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("path", result)
        self.assertIn("version", result)

    def test_functional_run(self):
        """测试函数式调用入口"""
        params = {
            "action": "status"
        }
        result = core_run(params)
        self.assertIsInstance(result, dict)

    @patch('os.makedirs')
    def test_initialization_error(self, mock_makedirs):
        """测试初始化失败的情况"""
        # 模拟 os.makedirs 抛出异常
        mock_makedirs.side_effect = Exception("权限错误")
        # 初始化应该不会抛出异常，只会记录错误
        mempalace = MemPalaceCore(palace_path="./test_mempalace")
        self.assertIsInstance(mempalace, MemPalaceCore)


if __name__ == "__main__":
    unittest.main()
