import os
import shutil
import tempfile
import unittest

from src.skills.git_helper import GitHelperTool


class TestGitHelperTool(unittest.IsolatedAsyncioTestCase):
    """测试 Git 助手工具"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录作为测试 Git 仓库
        self.temp_dir = tempfile.mkdtemp()
        # 初始化 Git 仓库
        import git
        self.repo = git.Repo.init(self.temp_dir)
        
        # 设置 Git 用户名和邮箱
        with self.repo.config_writer() as config:
            config.set_value('user', 'name', 'Test User')
            config.set_value('user', 'email', 'test@example.com')
        
        # 创建初始提交
        test_file = os.path.join(self.temp_dir, 'README.md')
        with open(test_file, 'w') as f:
            f.write('# Test Repository')
        self.repo.index.add([test_file])
        self.repo.index.commit('Initial commit')
        
        # 创建 GitHelperTool 实例
        self.tool = GitHelperTool(repo_path=self.temp_dir)
    
    def tearDown(self):
        """清理测试环境"""
        # 清理临时目录
        import gc
        # 确保 Git 仓库连接被释放
        if hasattr(self, 'repo'):
            del self.repo
        if hasattr(self, 'tool'):
            del self.tool
        # 强制垃圾回收
        gc.collect()
        # 延迟一下，确保文件锁被释放
        import time
        time.sleep(0.5)
        # 清理临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_status(self):
        """测试获取 Git 状态"""
        args = {
            "action": "status"
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result["observation"])
        self.assertIn("branch", result["observation"]["data"])
    
    def test_add(self):
        """测试添加文件到暂存区"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        args = {
            "action": "add",
            "files": ["test.txt"]
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        self.assertIn("已暂存文件", result["observation"]["message"])
    
    def test_commit(self):
        """测试提交更改"""
        # 创建测试文件并添加到暂存区
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        # 添加到暂存区
        add_args = {
            "action": "add",
            "files": ["test.txt"]
        }
        self.tool.execute(add_args)
        
        # 提交
        commit_args = {
            "action": "commit",
            "message": "Initial commit"
        }
        
        result = self.tool.execute(commit_args)
        self.assertEqual(result["status"], "success")
        self.assertIn("提交成功", result["observation"]["message"])
    
    def test_branch(self):
        """测试分支操作"""
        # 列出分支
        list_args = {
            "action": "branch"
        }
        result = self.tool.execute(list_args)
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result["observation"])
        self.assertIn("branches", result["observation"]["data"])
    
    def test_stash(self):
        """测试暂存更改"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        # 暂存更改
        stash_args = {
            "action": "stash",
            "message": "Test stash"
        }
        
        result = self.tool.execute(stash_args)
        self.assertEqual(result["status"], "success")
        self.assertIn("成功暂存更改", result["observation"]["message"])
    
    def test_stash_list(self):
        """测试列出暂存"""
        # 列出暂存
        list_args = {
            "action": "stash_list"
        }
        
        result = self.tool.execute(list_args)
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result["observation"])
    
    def test_hooks_list(self):
        """测试列出钩子"""
        # 列出钩子
        list_args = {
            "action": "hooks_list"
        }
        
        result = self.tool.execute(list_args)
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result["observation"])
    
    def test_invalid_action(self):
        """测试无效操作"""
        args = {
            "action": "invalid"
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "error")
        self.assertIn("validation error", result["observation"]["message"])
    
    def test_missing_message(self):
        """测试缺少提交消息"""
        args = {
            "action": "commit"
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "error")
        self.assertIn("执行 commit 操作时必须提供提交信息", result["observation"]["message"])
    
    def test_missing_tag_name(self):
        """测试缺少标签名称"""
        args = {
            "action": "tag"
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "error")
        self.assertIn("执行 tag 操作时必须提供标签名称", result["observation"]["message"])
    
    def test_missing_target_branch(self):
        """测试缺少目标分支"""
        args = {
            "action": "merge"
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "error")
        self.assertIn("执行 merge 操作时必须提供目标分支", result["observation"]["message"])
    
    def test_get_available_actions(self):
        """测试获取可用操作"""
        actions = self.tool.get_available_actions()
        self.assertIsInstance(actions, list)
        self.assertIn("status", actions)
        self.assertIn("add", actions)
        self.assertIn("commit", actions)
    
    def test_get_metrics(self):
        """测试获取性能指标"""
        metrics = self.tool.get_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_operations", metrics)
        self.assertIn("successful_operations", metrics)
        self.assertIn("failed_operations", metrics)
    
    def test_reset_metrics(self):
        """测试重置性能指标"""
        # 执行一些操作
        self.tool.execute({"action": "status"})
        # 重置指标
        self.tool.reset_metrics()
        metrics = self.tool.get_metrics()
        self.assertEqual(metrics["total_operations"], 0)
        self.assertEqual(metrics["successful_operations"], 0)
        self.assertEqual(metrics["failed_operations"], 0)


if __name__ == "__main__":
    unittest.main()