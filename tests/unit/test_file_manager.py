import unittest
import os
import tempfile
from src.skills.file_manager import FileManagerTool, FileManagerArgsSchema


class TestFileManagerTool(unittest.IsolatedAsyncioTestCase):
    """测试文件管理工具"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录作为测试工作目录
        self.temp_dir = tempfile.mkdtemp()
        self.tool = FileManagerTool()
    
    def tearDown(self):
        """清理测试环境"""
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_write_file(self):
        """测试写入文件"""
        file_path = os.path.join(self.temp_dir, "test.txt")
        content = "Hello, World!"
        
        args = {
            "operation": "write",
            "file_path": file_path,
            "content": content
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        
        # 验证文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)
    
    def test_read_file(self):
        """测试读取文件"""
        file_path = os.path.join(self.temp_dir, "test.txt")
        content = "Hello, World!"
        
        # 先写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        args = {
            "operation": "read",
            "file_path": file_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["observation"]["data"], content)
    
    def test_list_directory(self):
        """测试列出目录"""
        # 创建测试文件
        file1 = os.path.join(self.temp_dir, "file1.txt")
        file2 = os.path.join(self.temp_dir, "file2.txt")
        
        with open(file1, "w") as f:
            f.write("content1")
        with open(file2, "w") as f:
            f.write("content2")
        
        args = {
            "operation": "list",
            "file_path": self.temp_dir
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        items = result["observation"]["data"]
        self.assertEqual(len(items), 2)
    
    def test_delete_file(self):
        """测试删除文件"""
        file_path = os.path.join(self.temp_dir, "test.txt")
        
        # 先创建文件
        with open(file_path, "w") as f:
            f.write("content")
        
        args = {
            "operation": "delete",
            "file_path": file_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        
        # 验证文件已删除
        self.assertFalse(os.path.exists(file_path))
    
    def test_create_directory(self):
        """测试创建目录"""
        dir_path = os.path.join(self.temp_dir, "test_dir")
        
        args = {
            "operation": "mkdir",
            "file_path": dir_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        
        # 验证目录已创建
        self.assertTrue(os.path.exists(dir_path))
        self.assertTrue(os.path.isdir(dir_path))
    
    def test_rename_file(self):
        """测试重命名文件"""
        old_path = os.path.join(self.temp_dir, "old.txt")
        new_path = os.path.join(self.temp_dir, "new.txt")
        
        # 先创建文件
        with open(old_path, "w") as f:
            f.write("content")
        
        args = {
            "operation": "rename",
            "file_path": old_path,
            "target_path": new_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        
        # 验证文件已重命名
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(new_path))
    
    def test_copy_file(self):
        """测试复制文件"""
        source_path = os.path.join(self.temp_dir, "source.txt")
        target_path = os.path.join(self.temp_dir, "target.txt")
        
        # 先创建源文件
        with open(source_path, "w") as f:
            f.write("content")
        
        args = {
            "operation": "copy",
            "file_path": source_path,
            "target_path": target_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        
        # 验证文件已复制
        self.assertTrue(os.path.exists(source_path))
        self.assertTrue(os.path.exists(target_path))
        with open(target_path, "r") as f:
            self.assertEqual(f.read(), "content")
    
    def test_move_file(self):
        """测试移动文件"""
        source_path = os.path.join(self.temp_dir, "source.txt")
        target_path = os.path.join(self.temp_dir, "target.txt")
        
        # 先创建源文件
        with open(source_path, "w") as f:
            f.write("content")
        
        args = {
            "operation": "move",
            "file_path": source_path,
            "target_path": target_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        
        # 验证文件已移动
        self.assertFalse(os.path.exists(source_path))
        self.assertTrue(os.path.exists(target_path))
    
    def test_get_file_stat(self):
        """测试获取文件信息"""
        file_path = os.path.join(self.temp_dir, "test.txt")
        
        # 先创建文件
        with open(file_path, "w") as f:
            f.write("content")
        
        args = {
            "operation": "stat",
            "file_path": file_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "success")
        self.assertIn("path", result["observation"]["data"])
        self.assertIn("size", result["observation"]["data"])
    
    def test_invalid_operation(self):
        """测试无效操作"""
        args = {
            "operation": "invalid",
            "file_path": self.temp_dir
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "error")
        self.assertIn("不支持的操作类型", result["observation"]["message"])
    
    def test_missing_content(self):
        """测试缺少内容"""
        file_path = os.path.join(self.temp_dir, "test.txt")
        
        args = {
            "operation": "write",
            "file_path": file_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "error")
        self.assertIn("写入操作必须提供 content 参数", result["observation"]["message"])
    
    def test_missing_target_path(self):
        """测试缺少目标路径"""
        file_path = os.path.join(self.temp_dir, "test.txt")
        
        args = {
            "operation": "copy",
            "file_path": file_path
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "error")
        self.assertIn("copy 操作必须提供 target_path 参数", result["observation"]["message"])
    
    def test_security_check(self):
        """测试安全检查"""
        # 尝试使用相对路径
        args = {
            "operation": "read",
            "file_path": "../test.txt"
        }
        
        result = self.tool.execute(args)
        self.assertEqual(result["status"], "error")
        self.assertIn("路径包含不安全的字符", result["observation"]["message"])


if __name__ == "__main__":
    unittest.main()