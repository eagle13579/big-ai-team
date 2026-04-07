import sys
import os

# 确保项目根目录在 Python 搜索路径中
# 尝试多种可能的路径组合
possible_roots = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),  # 常见情况：tests/ 目录在项目根目录下
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')),  # 特殊情况：tests/ 目录在更深层
    os.path.abspath('.'),  # 当前目录
    os.path.abspath('..')  # 父目录
]

for root in possible_roots:
    if os.path.exists(os.path.join(root, 'src')):
        sys.path.insert(0, root)
        print(f"Added project root to path: {root}")
        break

import pytest
from unittest.mock import MagicMock, patch
from src.skills.git_helper import GitHelperTool, GitAction
import git


@pytest.fixture
def mock_tool():
    """创建带有mock的GitHelperTool实例"""
    with patch('git.Repo') as mock_repo_class:
        # 创建mock repo实例
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        # 模拟active_branch
        mock_branch = MagicMock()
        mock_branch.name = "feature-branch"
        mock_repo.active_branch = mock_branch
        
        # 模拟is_dirty
        mock_repo.is_dirty.return_value = False
        
        # 模拟index.diff
        mock_index = MagicMock()
        mock_repo.index = mock_index
        
        # 模拟diff返回值
        mock_diff_item1 = MagicMock()
        mock_diff_item1.a_path = "file1.py"
        mock_diff_item2 = MagicMock()
        mock_diff_item2.a_path = "file2.py"
        mock_index.diff.side_effect = lambda x: [mock_diff_item1, mock_diff_item2] if x is None else []
        
        # 模拟untracked_files
        mock_repo.untracked_files = ["new_file.py"]
        
        # 模拟remote
        mock_remote = MagicMock()
        mock_repo.remote.return_value = mock_remote
        
        # 模拟push返回值
        mock_push_info = MagicMock()
        mock_push_info.flags = 0
        mock_remote.push.return_value = [mock_push_info]
        
        # 模拟commit返回值
        mock_commit = MagicMock()
        mock_commit.hexsha = "1234567890abcdef"
        mock_index.commit.return_value = mock_commit
        
        # 模拟GitPythonClient的add方法
        def mock_add(files):
            if "." in files:
                mock_repo.git.add(A=True)
                return {"message": "已暂存所有更改"}
            else:
                mock_repo.index.add(files)
                return {"message": f"已暂存文件: {files}"}
        
        # 模拟GitPythonClient的commit方法
        def mock_commit(message):
            commit_obj = mock_index.commit(message)
            return {"hexsha": commit_obj.hexsha, "message": f"提交成功: {commit_obj.hexsha[:7]}"}
        
        # 模拟GitPythonClient的push方法
        def mock_push(remote, branch):
            remote_obj = mock_repo.remote(name=remote)
            remote_obj.push(branch)
            return {"message": f"成功推送到 {remote}/{branch}"}
        
        # 模拟GitPythonClient的pull方法
        def mock_pull(remote, branch):
            remote_obj = mock_repo.remote(name=remote)
            remote_obj.pull(branch)
            return {"message": f"已从 {remote}/{branch} 拉取更改"}
        
        # 模拟GitPythonClient的status方法
        def mock_status():
            return {
                "branch": mock_repo.active_branch.name,
                "dirty": mock_repo.is_dirty(),
                "modified": [item.a_path for item in mock_repo.index.diff(None)],
                "untracked": mock_repo.untracked_files,
                "staged": [item.a_path for item in mock_repo.index.diff("HEAD")]
            }
        
        # 创建自定义的GitPythonClient mock
        class MockGitPythonClient:
            def __init__(self, repo_path):
                self.repo = mock_repo
            
            def status(self):
                return mock_status()
            
            def add(self, files):
                return mock_add(files)
            
            def commit(self, message):
                return mock_commit(message)
            
            def push(self, remote, branch):
                return mock_push(remote, branch)
            
            def pull(self, remote, branch):
                return mock_pull(remote, branch)
            
            def branch(self, branch_name):
                return {"message": f"成功创建分支: {branch_name}"}
            
            def tag(self, tag_name, message=None):
                return {"message": f"成功创建标签: {tag_name}"}
            
            def merge(self, branch):
                return {"message": f"成功合并分支: {branch}"}
        
        # 创建工具实例（使用admin角色进行测试）
        tool = GitHelperTool(repo_path="/fake/path", git_client_factory=MockGitPythonClient, user_role="admin")
        yield tool, mock_repo


def test_status_success(mock_tool):
    """测试成功获取Git状态"""
    tool, mock_repo = mock_tool
    
    # 执行status操作
    result = tool.execute({
        "action": "status"
    })
    
    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "data" in result["observation"]
    assert "branch" in result["observation"]["data"]
    assert result["observation"]["data"]["branch"] == "feature-branch"
    assert "timestamp" in result["observation"]
    assert "2026-04-07" in result["observation"]["timestamp"]


def test_add_success(mock_tool):
    """测试成功暂存文件"""
    tool, mock_repo = mock_tool
    
    # 执行add操作
    result = tool.execute({
        "action": "add",
        "files": ["file1.py", "file2.py"]
    })
    
    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "message" in result["observation"]
    assert "已暂存文件" in result["observation"]["message"]
    # 验证调用
    mock_repo.index.add.assert_called_once_with(["file1.py", "file2.py"])


def test_add_all_success(mock_tool):
    """测试成功暂存所有文件"""
    tool, mock_repo = mock_tool
    
    # 执行add操作（添加所有文件）
    result = tool.execute({
        "action": "add",
        "files": ["."]
    })
    
    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "message" in result["observation"]
    assert "已暂存所有更改" in result["observation"]["message"]
    # 验证调用
    mock_repo.git.add.assert_called_once_with(A=True)


def test_commit_success(mock_tool):
    """测试成功提交"""
    tool, mock_repo = mock_tool
    
    # 执行commit操作
    result = tool.execute({
        "action": "commit",
        "message": "Test commit message"
    })
    
    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "data" in result["observation"]
    assert "hexsha" in result["observation"]["data"]
    assert "message" in result["observation"]
    assert "提交成功" in result["observation"]["message"]
    # 验证调用
    mock_repo.index.commit.assert_called_once_with("Test commit message")


def test_commit_validation_error(mock_tool):
    """测试提交时缺少message参数的验证错误"""
    tool, mock_repo = mock_tool
    
    # 执行commit操作（缺少message）
    result = tool.execute({
        "action": "commit"
    })
    
    # 验证结果
    assert result["status"] == "error"
    assert "observation" in result
    assert "执行 commit 操作时必须提供提交信息" in result["observation"]["message"]


def test_push_success(mock_tool):
    """测试成功推送"""
    tool, mock_repo = mock_tool
    
    # 执行push操作
    result = tool.execute({
        "action": "push",
        "remote": "origin",
        "branch": "feature-branch"
    })
    
    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "message" in result["observation"]
    assert "成功推送到" in result["observation"]["message"]
    # 验证调用
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_repo.remote.return_value.push.assert_called_once_with("feature-branch")


def test_pull_success(mock_tool):
    """测试成功拉取"""
    tool, mock_repo = mock_tool
    
    # 执行pull操作
    result = tool.execute({
        "action": "pull",
        "remote": "origin",
        "branch": "feature-branch"
    })
    
    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "message" in result["observation"]
    assert "已从" in result["observation"]["message"]
    # 验证调用
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_repo.remote.return_value.pull.assert_called_once_with("feature-branch")


def test_git_command_error(mock_tool):
    """测试Git命令执行错误的处理"""
    tool, mock_repo = mock_tool

    # 模拟push操作失败
    mock_repo.remote.return_value.push.side_effect = git.GitCommandError("push", "Network error")

    # 执行push操作
    result = tool.execute({
        "action": "push",
        "remote": "origin",
        "branch": "feature-branch"
    })

    # 验证结果
    assert result["status"] == "error"
    assert "observation" in result
    assert "执行失败" in result["observation"]["message"] or "推送失败" in result["observation"]["message"]


def test_security_guard_protected_branch():
    """测试安全防护：操作受保护分支的警告"""

    with patch('git.Repo') as mock_repo_class:
        # 创建mock repo实例
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        # 模拟active_branch
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_repo.active_branch = mock_branch
        
        # 模拟commit返回值
        mock_commit = MagicMock()
        mock_commit.hexsha = "1234567890abcdef"
        mock_repo.index = MagicMock()
        mock_repo.index.commit.return_value = mock_commit
        
        # 模拟GitPythonClient的方法
        class MockGitPythonClient:
            def __init__(self, repo_path):
                self.repo = mock_repo
            
            def status(self):
                return {"branch": "main"}
            
            def commit(self, message):
                return {"hexsha": "1234567890abcdef", "message": "提交成功: 1234567"}
        
        # 创建工具实例（使用user角色进行测试）
        tool = GitHelperTool(repo_path="/fake/path", git_client_factory=MockGitPythonClient, user_role="user")

        # 执行commit操作（user角色在受保护分支上执行commit应该被拒绝）
        result = tool.execute({
            "action": "commit",
            "message": "Test commit on main branch"
        })

        # 验证结果
        assert result["status"] == "error"
        assert "observation" in result
        assert "权限不足" in result["observation"]["message"]
        assert "main" in result["observation"]["message"]


def test_invalid_git_repository():
    """测试无效的Git仓库路径"""
    with patch('git.Repo') as mock_repo_class:
        # 模拟无效的Git仓库
        mock_repo_class.side_effect = git.InvalidGitRepositoryError
        
        # 验证异常
        with pytest.raises(Exception) as excinfo:
            GitHelperTool(repo_path="/invalid/path")
        
        assert "不是一个有效的 Git 仓库" in str(excinfo.value)