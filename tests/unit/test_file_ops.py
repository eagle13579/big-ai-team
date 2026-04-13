import os
import tempfile

import pytest

from src.skills.file_ops import FileOpsTool


@pytest.fixture
def file_ops_tool():
    """创建 FileOpsTool 实例"""
    return FileOpsTool()


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_file(temp_dir):
    """创建临时文件"""
    file_path = os.path.join(temp_dir, "test.txt")
    with open(file_path, "w") as f:
        f.write("Hello, World!")
    return file_path


def test_read_file(file_ops_tool, temp_file):
    """测试读取文件"""
    result = file_ops_tool.execute({"operation": "read", "path": temp_file})
    assert result["status"] == "success"
    assert "observation" in result
    assert "data" in result["observation"]
    assert result["observation"]["data"] == "Hello, World!"
    assert "文件读取成功" in result["observation"]["message"]


def test_write_file(file_ops_tool, temp_dir):
    """测试写入文件"""
    file_path = os.path.join(temp_dir, "new_file.txt")
    content = "This is a test file"
    result = file_ops_tool.execute({"operation": "write", "path": file_path, "content": content})
    assert result["status"] == "success"
    assert "文件写入成功" in result["observation"]["message"]
    # 验证文件内容
    with open(file_path) as f:
        assert f.read() == content


def test_list_directory(file_ops_tool, temp_dir, temp_file):
    """测试列出目录"""
    result = file_ops_tool.execute({"operation": "list", "path": temp_dir})
    assert result["status"] == "success"
    assert "observation" in result
    assert "data" in result["observation"]
    assert isinstance(result["observation"]["data"], list)
    assert len(result["observation"]["data"]) > 0


def test_delete_file(file_ops_tool, temp_file):
    """测试删除文件"""
    result = file_ops_tool.execute({"operation": "delete", "path": temp_file})
    assert result["status"] == "success"
    assert "文件删除成功" in result["observation"]["message"]
    # 验证文件已删除
    assert not os.path.exists(temp_file)


def test_copy_file(file_ops_tool, temp_file, temp_dir):
    """测试复制文件"""
    target_path = os.path.join(temp_dir, "copy.txt")
    result = file_ops_tool.execute({"operation": "copy", "path": temp_file, "target": target_path})
    assert result["status"] == "success"
    assert "文件复制成功" in result["observation"]["message"]
    # 验证文件已复制
    assert os.path.exists(target_path)
    with open(target_path) as f:
        assert f.read() == "Hello, World!"


def test_move_file(file_ops_tool, temp_file, temp_dir):
    """测试移动文件"""
    target_path = os.path.join(temp_dir, "moved.txt")
    result = file_ops_tool.execute({"operation": "move", "path": temp_file, "target": target_path})
    assert result["status"] == "success"
    assert "移动成功" in result["observation"]["message"]
    # 验证文件已移动
    assert not os.path.exists(temp_file)
    assert os.path.exists(target_path)


def test_mkdir(file_ops_tool, temp_dir):
    """测试创建目录"""
    new_dir = os.path.join(temp_dir, "new_dir")
    result = file_ops_tool.execute({"operation": "mkdir", "path": new_dir})
    assert result["status"] == "success"
    assert "目录创建成功" in result["observation"]["message"]
    # 验证目录已创建
    assert os.path.exists(new_dir)
    assert os.path.isdir(new_dir)


def test_rename_file(file_ops_tool, temp_file, temp_dir):
    """测试重命名文件"""
    new_path = os.path.join(temp_dir, "renamed.txt")
    result = file_ops_tool.execute({"operation": "rename", "path": temp_file, "target": new_path})
    assert result["status"] == "success"
    assert "重命名成功" in result["observation"]["message"]
    # 验证文件已重命名
    assert not os.path.exists(temp_file)
    assert os.path.exists(new_path)


def test_invalid_operation(file_ops_tool, temp_file):
    """测试无效操作"""
    result = file_ops_tool.execute({"operation": "invalid", "path": temp_file})
    assert result["status"] == "error"
    assert "不支持的操作类型" in result["observation"]["message"]


def test_missing_content(file_ops_tool, temp_dir):
    """测试缺少写入内容"""
    file_path = os.path.join(temp_dir, "new_file.txt")
    result = file_ops_tool.execute({"operation": "write", "path": file_path})
    assert result["status"] == "error"
    assert "写入操作必须提供 content 参数" in result["observation"]["message"]


def test_missing_target(file_ops_tool, temp_file, temp_dir):
    """测试缺少目标路径"""
    result = file_ops_tool.execute({"operation": "copy", "path": temp_file})
    assert result["status"] == "error"
    assert "copy 操作必须提供 target 参数" in result["observation"]["message"]
