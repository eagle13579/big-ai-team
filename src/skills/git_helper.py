import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Callable, Type
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
import git  # GitPython
from enum import Enum
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential
from src.shared.base import BaseSkill

# 配置日志
logger = logging.getLogger(__name__)

# --- 1. 配置管理 --- 

class GitHelperSettings(BaseSettings):
    """Git工具配置"""
    protected_branches: List[str] = Field(default=["main", "master", "prod"])
    max_retries: int = Field(default=3)
    retry_wait_min: float = Field(default=1.0)
    retry_wait_max: float = Field(default=10.0)
    enable_security_guard: bool = Field(default=True)
    
    model_config = ConfigDict(
        env_prefix="GIT_HELPER_",
        case_sensitive=False
    )

# --- 2. 协议定义层 (Layer 3: Schema) ---

class GitAction(str, Enum):
    STATUS = "status"
    ADD = "add"
    COMMIT = "commit"
    PUSH = "push"
    PULL = "pull"
    BRANCH = "branch"
    TAG = "tag"
    MERGE = "merge"

class GitArgsSchema(BaseModel):
    """Git操作的参数校验架构"""
    action: GitAction = Field(..., description="要执行的Git动作：status, add, commit, push, pull, branch, tag, merge")
    files: Optional[List[str]] = Field(default=None, description="需要add的文件列表，['.'] 表示全部")
    message: Optional[str] = Field(default=None, description="Commit时的提交信息")
    remote: str = Field(default="origin", description="远程仓库名称")
    branch: Optional[str] = Field(default=None, description="目标分支名称")
    branch_name: Optional[str] = Field(default=None, description="新分支名称")
    tag_name: Optional[str] = Field(default=None, description="标签名称")
    merge_branch: Optional[str] = Field(default=None, description="要合并的分支")
    user_role: str = Field(default="user", description="用户角色")

    @field_validator("message", mode="before")
    @classmethod
    def validate_commit_message(cls, v, info):
        action = info.data.get("action")
        # 检查action是否为commit（支持字符串和枚举值）
        if str(action).lower() == "commit" and not v:
            raise ValueError("执行 commit 操作时必须提供提交信息 (message)")
        return v

    @field_validator("branch_name", mode="before")
    @classmethod
    def validate_branch_name(cls, v, info):
        action = info.data.get("action")
        if str(action).lower() == "branch" and not v:
            raise ValueError("执行 branch 操作时必须提供分支名称 (branch_name)")
        return v

    @field_validator("tag_name", mode="before")
    @classmethod
    def validate_tag_name(cls, v, info):
        action = info.data.get("action")
        if str(action).lower() == "tag" and not v:
            raise ValueError("执行 tag 操作时必须提供标签名称 (tag_name)")
        return v

    @field_validator("merge_branch", mode="before")
    @classmethod
    def validate_merge_branch(cls, v, info):
        action = info.data.get("action")
        if str(action).lower() == "merge" and not v:
            raise ValueError("执行 merge 操作时必须提供要合并的分支 (merge_branch)")
        return v

# --- 3. 抽象接口层 --- 

class GitInterface(ABC):
    """Git操作抽象接口"""
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """获取仓库状态"""
        pass
    
    @abstractmethod
    def add(self, files: Optional[List[str]]) -> None:
        """暂存文件"""
        pass
    
    @abstractmethod
    def commit(self, message: str) -> str:
        """提交更改，返回commit hash"""
        pass
    
    @abstractmethod
    def push(self, remote: str, branch: str) -> Dict[str, Any]:
        """推送更改"""
        pass
    
    @abstractmethod
    def pull(self, remote: str, branch: str) -> None:
        """拉取更改"""
        pass
    
    @abstractmethod
    def create_branch(self, branch_name: str) -> None:
        """创建分支"""
        pass
    
    @abstractmethod
    def create_tag(self, tag_name: str, message: Optional[str] = None) -> None:
        """创建标签"""
        pass
    
    @abstractmethod
    def merge(self, branch: str) -> None:
        """合并分支"""
        pass
    
    @abstractmethod
    def get_active_branch(self) -> str:
        """获取当前活跃分支"""
        pass

# --- 4. 具体实现层 --- 

class GitPythonClient(GitInterface):
    """基于GitPython的Git客户端实现"""
    
    def __init__(self, repo_path: str):
        try:
            self.repo = git.Repo(repo_path)
        except git.InvalidGitRepositoryError:
            raise Exception(f"路径 {repo_path} 不是一个有效的 Git 仓库。")
    
    def get_status(self) -> Dict[str, Any]:
        changed_files = [item.a_path for item in self.repo.index.diff(None)]
        untracked_files = self.repo.untracked_files
        staged_files = [item.a_path for item in self.repo.index.diff("HEAD")]
        
        return {
            "branch": self.repo.active_branch.name,
            "is_dirty": self.repo.is_dirty(),
            "staged": staged_files,
            "unstaged": changed_files,
            "untracked": untracked_files
        }
    
    def add(self, files: Optional[List[str]]) -> None:
        if not files or "." in files:
            self.repo.git.add(A=True)
        else:
            self.repo.index.add(files)
    
    def commit(self, message: str) -> str:
        commit = self.repo.index.commit(message)
        return commit.hexsha
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def push(self, remote: str, branch: str) -> Dict[str, Any]:
        origin = self.repo.remote(name=remote)
        info = origin.push(branch)[0]
        return {"flags": info.flags}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def pull(self, remote: str, branch: str) -> None:
        origin = self.repo.remote(name=remote)
        origin.pull(branch)
    
    def create_branch(self, branch_name: str) -> None:
        self.repo.git.checkout('-b', branch_name)
    
    def create_tag(self, tag_name: str, message: Optional[str] = None) -> None:
        self.repo.create_tag(tag_name, message=message)
    
    def merge(self, branch: str) -> None:
        self.repo.git.merge(branch)
    
    def get_active_branch(self) -> str:
        return self.repo.active_branch.name

# --- 5. 安全审计层 --- 

class SecurityManager:
    """Git操作安全管理器"""
    
    def __init__(self, settings: GitHelperSettings):
        self.settings = settings
        self.protected_branches = settings.protected_branches
    
    def check_permission(self, action: GitAction, branch: str, user_role: str) -> bool:
        """检查用户是否有权限执行操作"""
        # 基础权限检查
        permission_matrix = {
            GitAction.STATUS: ["guest", "user", "admin"],
            GitAction.ADD: ["user", "admin"],
            GitAction.COMMIT: ["user", "admin"],
            GitAction.PUSH: ["user", "admin"],
            GitAction.PULL: ["user", "admin"],
            GitAction.BRANCH: ["user", "admin"],
            GitAction.TAG: ["user", "admin"],
            GitAction.MERGE: ["admin"]
        }
        
        required_roles = permission_matrix.get(action, ["admin"])
        if user_role not in required_roles:
            logger.warning(f"权限不足: {user_role} 无法执行 {action} 操作")
            return False
        
        # 受保护分支检查
        if self.settings.enable_security_guard and action in [GitAction.PUSH, GitAction.COMMIT, GitAction.MERGE]:
            if branch in self.protected_branches and user_role != "admin":
                logger.warning(f"安全警告: 非管理员用户 {user_role} 尝试在受保护分支 {branch} 上执行 {action} 操作")
                return False
        
        return True
    
    def validate_input(self, action: GitAction, **kwargs) -> bool:
        """验证输入安全性"""
        # 检查文件路径安全性
        if action == GitAction.ADD and kwargs.get("files"):
            for file_path in kwargs["files"]:
                if ".." in file_path or os.path.isabs(file_path):
                    logger.warning(f"安全警告: 检测到不安全的文件路径: {file_path}")
                    return False
        
        return True

# --- 6. 核心工具实现 (Layer 3: Atomic Tool) ---

class GitHelperTool(BaseSkill):
    """
    Ace AI Engine - Git原子化工具
    遵循 PRD v2.0 Layer 3 规范，负责物理层面的Git操作
    """
    
    name = "git_helper"
    description = "用于管理本地Git仓库的原子化工具，支持状态查看、暂存、提交、拉取、推送、分支管理、标签管理和合并操作。"
    args_schema = GitArgsSchema

    def __init__(self, repo_path: str = ".", git_client: Optional[GitInterface] = None, settings: Optional[GitHelperSettings] = None):
        """
        初始化GitHelperTool
        
        Args:
            repo_path: Git仓库路径
            git_client: Git客户端实例，用于依赖注入
            settings: 配置实例
        """
        self.repo_path = repo_path
        self.settings = settings or GitHelperSettings()
        self.git_client = git_client or GitPythonClient(repo_path)
        self.security_manager = SecurityManager(self.settings)
        self._operation_cache: Dict[str, Dict[str, Any]] = {}
    
    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行入口，集成了安全审计逻辑
        
        Args:
            args: 操作参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 实例化校验参数
            validated_args = GitArgsSchema(**args)
            
            # 额外验证：确保commit操作时必须提供message参数
            if validated_args.action == GitAction.COMMIT and not validated_args.message:
                raise ValueError("执行 commit 操作时必须提供提交信息 (message)")
            
            # 安全审计
            current_branch = self.git_client.get_active_branch()
            if not self.security_manager.check_permission(
                validated_args.action, 
                current_branch, 
                validated_args.user_role
            ):
                return self._create_observation("error", None, "权限不足，无法执行操作")
            
            if not self.security_manager.validate_input(
                validated_args.action, 
                files=validated_args.files
            ):
                return self._create_observation("error", None, "输入验证失败，无法执行操作")

            # 路由到具体逻辑
            if validated_args.action == GitAction.STATUS:
                return self._get_status()
            elif validated_args.action == GitAction.ADD:
                return self._add(validated_args.files)
            elif validated_args.action == GitAction.COMMIT:
                return self._commit(validated_args.message)
            elif validated_args.action == GitAction.PUSH:
                return self._push(validated_args.remote, validated_args.branch)
            elif validated_args.action == GitAction.PULL:
                return self._pull(validated_args.remote, validated_args.branch)
            elif validated_args.action == GitAction.BRANCH:
                return self._create_branch(validated_args.branch_name)
            elif validated_args.action == GitAction.TAG:
                return self._create_tag(validated_args.tag_name, validated_args.message)
            elif validated_args.action == GitAction.MERGE:
                return self._merge(validated_args.merge_branch)
            else:
                return self._create_observation("error", None, f"不支持的操作类型: {validated_args.action}")
                
        except ValueError as e:
            logger.error(f"参数验证错误: {str(e)}")
            return self._create_observation("error", None, str(e))
        except git.GitCommandError as e:
            logger.error(f"Git命令执行错误: {str(e)}")
            return self._create_observation("error", None, f"Git命令执行失败: {str(e)}")
        except Exception as e:
            logger.error(f"执行错误: {str(e)}", exc_info=True)
            return self._create_observation("error", None, f"执行失败: {str(e)}")

    # --- 7. 内部原子逻辑 ---

    def _get_status(self) -> Dict[str, Any]:
        """获取Git仓库状态"""
        try:
            # 检查缓存
            cache_key = "status"
            if cache_key in self._operation_cache:
                cached_data = self._operation_cache[cache_key]
                if (datetime.now().timestamp() - cached_data["timestamp"]) < 5:  # 5秒缓存
                    logger.info("从缓存获取状态信息")
                    return self._create_observation("success", cached_data["data"], "成功获取Git状态（从缓存）")
            
            # 获取状态
            data = self.git_client.get_status()
            
            # 更新缓存
            self._operation_cache[cache_key] = {
                "data": data,
                "timestamp": datetime.now().timestamp()
            }
            
            return self._create_observation("success", data, "成功获取Git状态")
        except Exception as e:
            logger.error(f"获取状态失败: {str(e)}")
            raise

    def _add(self, files: Optional[List[str]]) -> Dict[str, Any]:
        """暂存文件"""
        try:
            self.git_client.add(files)
            if not files or "." in files:
                msg = "已暂存所有更改"
            else:
                msg = f"已暂存文件: {', '.join(files)}"
            
            # 清除状态缓存
            if "status" in self._operation_cache:
                del self._operation_cache["status"]
            
            return self._create_observation("success", None, msg)
        except Exception as e:
            logger.error(f"暂存文件失败: {str(e)}")
            raise

    def _commit(self, message: str) -> Dict[str, Any]:
        """提交更改"""
        try:
            hexsha = self.git_client.commit(message)
            
            # 清除状态缓存
            if "status" in self._operation_cache:
                del self._operation_cache["status"]
            
            return self._create_observation("success", {"hexsha": hexsha}, f"提交成功，Hash: {hexsha[:7]}")
        except Exception as e:
            logger.error(f"提交失败: {str(e)}")
            raise

    def _push(self, remote: str, branch: Optional[str]) -> Dict[str, Any]:
        """推送更改"""
        try:
            target_branch = branch or self.git_client.get_active_branch()
            info = self.git_client.push(remote, target_branch)
            return self._create_observation("success", info, f"成功推送到 {remote}/{target_branch}")
        except Exception as e:
            logger.error(f"推送失败: {str(e)}")
            raise

    def _pull(self, remote: str, branch: Optional[str]) -> Dict[str, Any]:
        """拉取更改"""
        try:
            target_branch = branch or self.git_client.get_active_branch()
            self.git_client.pull(remote, target_branch)
            
            # 清除状态缓存
            if "status" in self._operation_cache:
                del self._operation_cache["status"]
            
            return self._create_observation("success", None, f"已从 {remote}/{target_branch} 拉取最新代码")
        except Exception as e:
            logger.error(f"拉取失败: {str(e)}")
            raise

    def _create_branch(self, branch_name: str) -> Dict[str, Any]:
        """创建分支"""
        try:
            self.git_client.create_branch(branch_name)
            return self._create_observation("success", None, f"成功创建分支: {branch_name}")
        except Exception as e:
            logger.error(f"创建分支失败: {str(e)}")
            raise

    def _create_tag(self, tag_name: str, message: Optional[str] = None) -> Dict[str, Any]:
        """创建标签"""
        try:
            self.git_client.create_tag(tag_name, message)
            return self._create_observation("success", None, f"成功创建标签: {tag_name}")
        except Exception as e:
            logger.error(f"创建标签失败: {str(e)}")
            raise

    def _merge(self, branch: str) -> Dict[str, Any]:
        """合并分支"""
        try:
            self.git_client.merge(branch)
            return self._create_observation("success", None, f"成功合并分支: {branch}")
        except Exception as e:
            logger.error(f"合并分支失败: {str(e)}")
            raise

    # --- 8. 辅助与反馈机制 (Layer 5: Observation) ---

    def _create_observation(self, status: str, data: Any, message: str = "") -> Dict[str, Any]:
        """生成符合 Layer 5 标准的反馈对象"""
        from datetime import datetime
        return {
            "status": status,  # "success" | "error"
            "observation": {
                "data": data,
                "message": message,
                "timestamp": datetime.now().isoformat() + "Z" # 遵循当前上下文时间格式
            },
            "metadata": {
                "repo_path": self.repo_path,
                "client_type": type(self.git_client).__name__
            }
        }

    # --- 9. 工具管理方法 ---

    def get_available_actions(self) -> List[str]:
        """获取可用的Git操作列表"""
        return [action.value for action in GitAction]

    def clear_cache(self):
        """清除操作缓存"""
        self._operation_cache.clear()
        logger.info("已清除操作缓存")

# --- 10. 工厂方法 --- 

def create_git_helper(repo_path: str = ".", **kwargs) -> GitHelperTool:
    """
    创建GitHelperTool实例的工厂方法
    
    Args:
        repo_path: Git仓库路径
        **kwargs: 其他参数
        
    Returns:
        GitHelperTool: 实例
    """
    return GitHelperTool(repo_path, **kwargs)
