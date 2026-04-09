from typing import Dict, List, Optional, Tuple, Pattern
import re
import os
from pydantic import BaseModel
from src.shared.logging import logger


class SecurityConfig(BaseModel):
    """安全配置"""
    # 受保护的分支
    protected_branches: List[str] = ["main", "master", "develop"]
    # 权限矩阵
    permission_matrix: Dict[str, List[str]] = {
        "admin": ["status", "add", "commit", "push", "pull", "branch", "tag", "merge", "stash", "hooks"],
        "user": ["status", "add", "commit", "branch", "tag", "stash"],
        "guest": ["status"]
    }
    # 敏感命令模式
    sensitive_commands: List[str] = [
        r"rm\s+-rf",
        r"sudo",
        r"chmod\s+777",
        r"format",
        r"shutdown",
        r"reboot"
    ]
    # 敏感文件路径
    sensitive_files: List[str] = [
        ".env",
        ".env.*",
        "secret.*",
        "password.*",
        "key.*",
        "token.*"
    ]
    # 敏感词列表
    sensitive_words: List[str] = [
        "password",
        "secret",
        "key",
        "token",
        "credential",
        "api_key",
        "access_token",
        "secret_key"
    ]


class SecurityManager:
    """安全管理器"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """初始化安全管理器"""
        self.config = config or SecurityConfig()
        # 编译敏感命令正则表达式
        self.sensitive_command_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.config.sensitive_commands
        ]
        # 编译敏感文件路径正则表达式
        self.sensitive_file_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.config.sensitive_files
        ]
        logger.info("安全管理器初始化完成")
    
    def validate_command(self, command: str, user_role: str) -> Tuple[bool, str]:
        """验证命令是否安全"""
        # 检查命令是否包含敏感操作
        for pattern in self.sensitive_command_patterns:
            if pattern.search(command):
                return False, f"命令包含敏感操作: {command}"
        
        # 检查用户权限
        if user_role not in self.config.permission_matrix:
            return False, f"未知的用户角色: {user_role}"
        
        # 提取命令类型
        command_type = command.split()[0] if command else ""
        if command_type and command_type not in self.config.permission_matrix[user_role]:
            return False, f"权限不足，无法执行操作: {command_type}"
        
        return True, "命令验证通过"
    
    def validate_file_path(self, file_path: str) -> Tuple[bool, str]:
        """验证文件路径是否安全"""
        # 检查路径穿越攻击
        if ".." in file_path:
            return False, f"危险的文件路径: {file_path}"
        
        # 检查是否访问敏感文件
        file_name = os.path.basename(file_path)
        for pattern in self.sensitive_file_patterns:
            if pattern.match(file_name):
                return False, f"禁止访问敏感文件: {file_path}"
        
        return True, "文件路径验证通过"
    
    def validate_input(self, input_text: str) -> Tuple[bool, str]:
        """验证输入是否包含敏感信息"""
        # 检查输入是否包含敏感词
        for word in self.config.sensitive_words:
            if word.lower() in input_text.lower():
                return False, f"输入包含敏感信息: {word}"
        
        return True, "输入验证通过"
    
    def check_permission(self, action: str, user_role: str, branch: Optional[str] = None) -> Tuple[bool, str]:
        """检查用户权限"""
        # 检查用户角色是否存在
        if user_role not in self.config.permission_matrix:
            return False, f"未知的用户角色: {user_role}"
        
        # 检查用户是否有权限执行该操作
        if action not in self.config.permission_matrix[user_role]:
            return False, f"权限不足，无法执行操作: {action}"
        
        # 检查是否操作受保护分支
        if branch and branch in self.config.protected_branches and action in ["push", "commit", "merge"]:
            if user_role != "admin":
                return False, f"权限不足，无法对受保护分支 {branch} 执行 {action} 操作"
        
        return True, "权限检查通过"
    
    def validate_git_operation(self, action: str, files: Optional[List[str]], user_role: str, branch: str) -> Tuple[bool, str]:
        """验证 Git 操作"""
        # 检查权限
        perm_ok, perm_msg = self.check_permission(action, user_role, branch)
        if not perm_ok:
            return False, perm_msg
        
        # 检查文件路径
        if files:
            for file_path in files:
                path_ok, path_msg = self.validate_file_path(file_path)
                if not path_ok:
                    return False, path_msg
        
        return True, "Git 操作验证通过"
    
    def validate_file_operation(self, operation: str, file_path: str, target_path: Optional[str] = None) -> Tuple[bool, str]:
        """验证文件操作"""
        # 检查文件路径
        path_ok, path_msg = self.validate_file_path(file_path)
        if not path_ok:
            return False, path_msg
        
        # 检查目标路径
        if target_path:
            target_ok, target_msg = self.validate_file_path(target_path)
            if not target_ok:
                return False, target_msg
        
        # 检查危险操作
        if operation == "delete":
            # 禁止删除敏感文件
            file_name = os.path.basename(file_path)
            for pattern in self.sensitive_file_patterns:
                if pattern.match(file_name):
                    return False, f"禁止删除敏感文件: {file_path}"
        
        return True, "文件操作验证通过"
    
    def add_sensitive_word(self, word: str):
        """添加敏感词"""
        if word not in self.config.sensitive_words:
            self.config.sensitive_words.append(word)
            logger.info(f"添加敏感词: {word}")
    
    def remove_sensitive_word(self, word: str):
        """移除敏感词"""
        if word in self.config.sensitive_words:
            self.config.sensitive_words.remove(word)
            logger.info(f"移除敏感词: {word}")
    
    def add_protected_branch(self, branch: str):
        """添加受保护分支"""
        if branch not in self.config.protected_branches:
            self.config.protected_branches.append(branch)
            logger.info(f"添加受保护分支: {branch}")
    
    def remove_protected_branch(self, branch: str):
        """移除受保护分支"""
        if branch in self.config.protected_branches:
            self.config.protected_branches.remove(branch)
            logger.info(f"移除受保护分支: {branch}")