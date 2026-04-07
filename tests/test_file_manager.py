import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch, mock_open
from src.skills.file_manager import FileManagerTool


@pytest.fixture
def file_manager_tool():
    """创建FileManagerTool实例"""
    return FileManagerTool()


def test_read_file_success(file_manager_tool):
    """测试成功读取文件"""
    # 模拟文件存在且可读
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data='test content')) as mock_file:
            result = file_manager_tool.execute({
                "operation": "read",
                "file_path": "test.txt"
            })
            
            # 验证结果
            assert result["status"] == "success"
            assert "observation" in result
            assert "data" in result["observation"]
            assert result["observation"]["data"] == "test content"
            assert "成功读取文件" in result["observation"]["message"]
            assert "2026-04-07" in result["observation"]["timestamp"]


def test_read_file_not_exists(file_manager_tool):
    """测试读取不存在的文件"""
    # 模拟文件不存在
    with patch('os.path.exists', return_value=False):
        result = file_manager_tool.execute({
            "operation": "read",
            "file_path": "non_existent.txt"
        })
        
        # 验证结果
        assert result["status"] == "error"
        assert "observation" in result
        assert "文件不存在" in result["observation"]["message"]


def test_write_file_success(file_manager_tool):
    """测试成功写入文件"""
    # 模拟文件路径
    with patch('os.makedirs', return_value=None):
        with patch('builtins.open', mock_open()) as mock_file:
            result = file_manager_tool.execute({
                "operation": "write",
                "file_path": "test.txt",
                "content": "test content"
            })
            
            # 验证结果
            assert result["status"] == "success"
            assert "observation" in result
            assert "成功写入到" in result["observation"]["message"]
            # 验证文件被打开并写入
            mock_file.assert_called_once_with(os.path.abspath("test.txt"), 'w', encoding="utf-8")
            mock_file().write.assert_called_once_with("test content")


def test_write_file_no_content(file_manager_tool):
    """测试写入文件时缺少内容"""
    result = file_manager_tool.execute({
        "operation": "write",
        "file_path": "test.txt"
    })
    
    # 验证结果
    assert result["status"] == "error"
    assert "observation" in result
    assert "写入操作必须提供 content 参数" in result["observation"]["message"]


def test_list_directory_success(file_manager_tool):
    """测试成功列出目录"""
    # 模拟目录存在且包含文件
    with patch('os.path.isdir', return_value=True):
        with patch('os.listdir', return_value=["file1.txt", "file2.txt"]):
            result = file_manager_tool.execute({
                "operation": "list",
                "file_path": "."
            })
            
            # 验证结果
            assert result["status"] == "success"
            assert "observation" in result
            assert "data" in result["observation"]
            assert result["observation"]["data"] == ["file1.txt", "file2.txt"]
            assert "成功列出目录" in result["observation"]["message"]


def test_list_directory_not_exists(file_manager_tool):
    """测试列出不存在的目录"""
    # 模拟目录不存在
    with patch('os.path.isdir', return_value=False):
        result = file_manager_tool.execute({
            "operation": "list",
            "file_path": "non_existent_dir"
        })
        
        # 验证结果
        assert result["status"] == "error"
        assert "observation" in result
        assert "目录不存在" in result["observation"]["message"]


def test_delete_file_success(file_manager_tool):
    """测试成功删除文件"""
    # 模拟文件存在
    with patch('os.path.isfile', return_value=True):
        with patch('os.remove', return_value=None) as mock_remove:
            result = file_manager_tool.execute({
                "operation": "delete",
                "file_path": "test.txt"
            })
            
            # 验证结果
            assert result["status"] == "success"
            assert "observation" in result
            assert "已删除文件" in result["observation"]["message"]
            # 验证文件被删除
            mock_remove.assert_called_once_with(os.path.abspath("test.txt"))


def test_delete_file_not_exists(file_manager_tool):
    """测试删除不存在的文件"""
    # 模拟文件不存在
    with patch('os.path.isfile', return_value=False):
        result = file_manager_tool.execute({
            "operation": "delete",
            "file_path": "non_existent.txt"
        })
        
        # 验证结果
        assert result["status"] == "error"
        assert "observation" in result
        assert "仅支持删除单个文件" in result["observation"]["message"]


def test_invalid_operation(file_manager_tool):
    """测试无效的操作类型"""
    result = file_manager_tool.execute({
        "operation": "invalid",
        "file_path": "test.txt"
    })
    
    # 验证结果
    assert result["status"] == "error"
    assert "observation" in result
    assert "不支持的操作类型" in result["observation"]["message"]


def test_exception_handling(file_manager_tool):
    """测试异常处理"""
    # 模拟读取文件时发生异常
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', side_effect=Exception("File read error")):
            result = file_manager_tool.execute({
                "operation": "read",
                "file_path": "test.txt"
            })
            
            # 验证结果
            assert result["status"] == "error"
            assert "observation" in result
            assert "文件系统异常" in result["observation"]["message"]
            assert "File read error" in result["observation"]["message"]