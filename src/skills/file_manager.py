import os
import shutil
import stat
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator
from src.shared.base import BaseSkill
from src.shared.utils import sanitize_path
from src.execution.sandbox import SecurityManager


class FileManagerArgsSchema(BaseModel):
    """文件管理操作的参数校验架构"""
    operation: str = Field(..., description="操作类型: read, write, list, delete, copy, move, mkdir, rename, stat")
    file_path: str = Field(..., description="文件或目录路径")
    content: Optional[str] = Field(default=None, description="写入文件的内容")
    target_path: Optional[str] = Field(default=None, description="复制、移动或重命名的目标路径")
    max_size: Optional[int] = Field(default=10485760, description="文件大小限制（字节），默认为10MB")

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v):
        valid_operations = ["read", "write", "list", "delete", "copy", "move", "mkdir", "rename", "stat"]
        if v not in valid_operations:
            raise ValueError(f"不支持的操作类型: {v}，支持的操作类型: {valid_operations}")
        return v

    @field_validator("content", mode='before')
    @classmethod
    def validate_content(cls, v, info):
        if info.data.get("operation") == "write" and v is None:
            raise ValueError("写入操作必须提供 content 参数")
        # 检查内容大小
        max_size = info.data.get("max_size", 10485760)
        if v and len(v.encode('utf-8')) > max_size:
            raise ValueError(f"内容大小超过限制: {len(v.encode('utf-8'))} 字节，最大允许: {max_size} 字节")
        return v

    @field_validator("target_path")
    @classmethod
    def validate_target_path(cls, v, info):
        operation = info.data.get("operation")
        if operation in ["copy", "move", "rename"] and not v:
            raise ValueError(f"{operation} 操作必须提供 target_path 参数")
        return v


class FileManagerTool(BaseSkill):
    """
    Ace AI Engine - 文件管理工具
    用于执行文件系统操作
    """

    name = "file_manager"
    description = "用于执行文件系统操作，支持读取、写入、列出、删除、复制、移动、重命名文件、创建目录和获取文件信息。"
    args_schema = FileManagerArgsSchema

    def __init__(self):
        """初始化文件管理工具"""
        super().__init__()
        # 操作映射表，使用字典替代if-elif链
        self.operations = {
            "read": self._read_file,
            "write": self._write_file,
            "list": self._list_directory,
            "delete": self._delete_file,
            "copy": self._copy_file,
            "move": self._move_file,
            "mkdir": self._create_directory,
            "rename": self._rename_file,
            "stat": self._get_file_stat
        }
        # 初始化安全管理器
        self.security_manager = SecurityManager()

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文件系统操作

        Args:
            args: 操作参数，包含 operation, file_path, content, target_path, max_size

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 验证参数
            validated_args = FileManagerArgsSchema(**args)

            # 执行操作
            operation = validated_args.operation
            file_path = sanitize_path(validated_args.file_path)
            content = validated_args.content
            target_path = sanitize_path(validated_args.target_path) if validated_args.target_path else None
            max_size = validated_args.max_size

            # 规范化路径
            file_path = os.path.abspath(file_path)
            if target_path:
                target_path = os.path.abspath(target_path)

            # 安全检查
            valid, message = self.security_manager.validate_file_operation(operation, file_path, target_path)
            if not valid:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": message,
                        "timestamp": self._get_timestamp()
                    }
                }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"复制失败: {str(e)}",
                    "timestamp": self._get_timestamp()
                }
            }

    def _move_file(self, source_path: str, target_path: str) -> Dict[str, Any]:
        """移动文件"""
        if not os.path.exists(source_path):
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"源文件不存在: {source_path}",
                    "timestamp": self._get_timestamp()
                }
            }

        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.move(source_path, target_path)
            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": f"成功移动: {source_path} -> {target_path}",
                    "timestamp": self._get_timestamp()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"移动失败: {str(e)}",
                    "timestamp": self._get_timestamp()
                }
            }

    def _create_directory(self, directory_path: str) -> Dict[str, Any]:
        """创建目录"""
        try:
            os.makedirs(directory_path, exist_ok=True)
            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": f"成功创建目录: {directory_path}",
                    "timestamp": self._get_timestamp()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"创建目录失败: {str(e)}",
                    "timestamp": self._get_timestamp()
                }
            }

    def _rename_file(self, source_path: str, target_path: str) -> Dict[str, Any]:
        """重命名文件"""
        if not os.path.exists(source_path):
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"源文件不存在: {source_path}",
                    "timestamp": self._get_timestamp()
                }
            }

        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            os.rename(source_path, target_path)
            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": f"成功重命名: {source_path} -> {target_path}",
                    "timestamp": self._get_timestamp()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"重命名失败: {str(e)}",
                    "timestamp": self._get_timestamp()
                }
            }

    def _get_file_stat(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"文件不存在: {file_path}",
                    "timestamp": self._get_timestamp()
                }
            }

        try:
            file_stat = os.stat(file_path)
            stat_info = {
                "path": file_path,
                "type": "directory" if os.path.isdir(file_path) else "file",
                "size": file_stat.st_size,
                "mode": stat.filemode(file_stat.st_mode),
                "uid": file_stat.st_uid,
                "gid": file_stat.st_gid,
                "atime": file_stat.st_atime,
                "mtime": file_stat.st_mtime,
                "ctime": file_stat.st_ctime
            }
            return {
                "status": "success",
                "observation": {
                    "data": stat_info,
                    "message": f"成功获取文件信息: {file_path}",
                    "timestamp": self._get_timestamp()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"获取文件信息失败: {str(e)}",
                    "timestamp": self._get_timestamp()
                }
            }

