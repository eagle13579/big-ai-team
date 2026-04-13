import os
import shutil
import stat
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from src.shared.base import BaseSkill
from src.shared.utils import sanitize_path


class FileManagerArgsSchema(BaseModel):
    """文件管理操作的参数校验架构"""

    operation: str = Field(
        ..., description="操作类型: read, write, list, delete, copy, move, mkdir, rename, stat"
    )
    file_path: str = Field(..., description="文件或目录路径")
    content: str | None = Field(default=None, description="写入文件的内容")
    target_path: str | None = Field(default=None, description="复制、移动或重命名的目标路径")
    max_size: int | None = Field(
        default=10485760, description="文件大小限制（字节），默认为10MB"
    )

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v):
        valid_operations = [
            "read",
            "write",
            "list",
            "delete",
            "copy",
            "move",
            "mkdir",
            "rename",
            "stat",
        ]
        if v not in valid_operations:
            raise ValueError(f"不支持的操作类型: {v}，支持的操作类型: {valid_operations}")
        return v

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v, info):
        if info.data.get("operation") == "write" and v is None:
            raise ValueError("写入操作必须提供 content 参数")
        # 检查内容大小
        max_size = info.data.get("max_size", 10485760)
        if v and len(v.encode("utf-8")) > max_size:
            raise ValueError(
                f"内容大小超过限制: {len(v.encode('utf-8'))} 字节，最大允许: {max_size} 字节"
            )
        return v

    @field_validator("target_path", mode="before")
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
            "stat": self._get_file_stat,
        }

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        执行文件系统操作

        Args:
            args: 操作参数，包含 operation, file_path, content, target_path, max_size

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 安全检查原始路径
            if "file_path" in args:
                self._security_check(args["file_path"])
            if "target_path" in args and args["target_path"]:
                self._security_check(args["target_path"])

            # 检查必要参数
            if "operation" not in args:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": "必须提供 operation 参数",
                        "timestamp": self._get_timestamp(),
                    },
                }
            
            operation = args["operation"]
            
            # 检查写入操作是否提供 content
            if operation == "write" and "content" not in args:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": "写入操作必须提供 content 参数",
                        "timestamp": self._get_timestamp(),
                    },
                }
            
            # 检查复制、移动、重命名操作是否提供 target_path
            if operation in ["copy", "move", "rename"] and "target_path" not in args:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"{operation} 操作必须提供 target_path 参数",
                        "timestamp": self._get_timestamp(),
                    },
                }

            # 验证参数
            validated_args = FileManagerArgsSchema(**args)

            # 执行操作
            file_path = sanitize_path(validated_args.file_path)
            content = validated_args.content
            target_path = (
                sanitize_path(validated_args.target_path) if validated_args.target_path else None
            )
            max_size = validated_args.max_size

            # 规范化路径
            file_path = os.path.abspath(file_path)
            if target_path:
                target_path = os.path.abspath(target_path)

            # 使用映射表执行操作
            if operation in self.operations:
                if operation in ["copy", "move", "rename"]:
                    return self.operations[operation](file_path, target_path)
                elif operation == "write":
                    return self.operations[operation](file_path, content, max_size)
                else:
                    return self.operations[operation](file_path)
            else:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"不支持的操作类型: {operation}",
                        "timestamp": self._get_timestamp(),
                    },
                }

        except ValueError as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": str(e),
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            # 检查是否是写入操作时缺少内容
            if "write() argument must be str, not None" in str(e):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": "写入操作必须提供 content 参数",
                        "timestamp": self._get_timestamp(),
                    },
                }
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"文件系统异常: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _read_file(self, file_path: str) -> dict[str, Any]:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            执行结果
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"文件不存在: {file_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            if not os.path.isfile(file_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"路径不是文件: {file_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > 10485760:  # 10MB
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": "文件过大，最大支持10MB",
                        "timestamp": self._get_timestamp(),
                    },
                }

            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()

            return {
                "status": "success",
                "observation": {
                    "data": content,
                    "message": f"文件读取成功: {file_path}",
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"读取文件失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _write_file(self, file_path: str, content: str, max_size: int) -> dict[str, Any]:
        """
        写入文件内容

        Args:
            file_path: 文件路径
            content: 文件内容
            max_size: 最大文件大小

        Returns:
            执行结果
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": f"文件写入成功: {file_path}",
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"写入文件失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _list_directory(self, directory_path: str) -> dict[str, Any]:
        """
        列出目录内容

        Args:
            directory_path: 目录路径

        Returns:
            执行结果
        """
        try:
            if not os.path.exists(directory_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"目录不存在: {directory_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            if not os.path.isdir(directory_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"路径不是目录: {directory_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            items = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                item_info = {
                    "name": item,
                    "path": item_path,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                }
                if os.path.isfile(item_path):
                    item_info["size"] = os.path.getsize(item_path)
                items.append(item_info)

            return {
                "status": "success",
                "observation": {
                    "data": items,
                    "message": f"目录列出成功: {directory_path}",
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"列出目录失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _delete_file(self, file_path: str) -> dict[str, Any]:
        """
        删除文件或目录

        Args:
            file_path: 文件或目录路径

        Returns:
            执行结果
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"路径不存在: {file_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            if os.path.isfile(file_path):
                os.remove(file_path)
                message = f"文件删除成功: {file_path}"
            else:
                shutil.rmtree(file_path)
                message = f"目录删除成功: {file_path}"

            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": message,
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"删除失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _copy_file(self, source_path: str, target_path: str) -> dict[str, Any]:
        """
        复制文件或目录

        Args:
            source_path: 源路径
            target_path: 目标路径

        Returns:
            执行结果
        """
        try:
            if not os.path.exists(source_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"源路径不存在: {source_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            # 确保目标目录存在
            target_directory = os.path.dirname(target_path)
            if target_directory and not os.path.exists(target_directory):
                os.makedirs(target_directory, exist_ok=True)

            if os.path.isfile(source_path):
                shutil.copy2(source_path, target_path)
                message = f"文件复制成功: {source_path} -> {target_path}"
            else:
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                message = f"目录复制成功: {source_path} -> {target_path}"

            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": message,
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"复制失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _move_file(self, source_path: str, target_path: str) -> dict[str, Any]:
        """
        移动文件或目录

        Args:
            source_path: 源路径
            target_path: 目标路径

        Returns:
            执行结果
        """
        try:
            if not os.path.exists(source_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"源路径不存在: {source_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            # 确保目标目录存在
            target_directory = os.path.dirname(target_path)
            if target_directory and not os.path.exists(target_directory):
                os.makedirs(target_directory, exist_ok=True)

            shutil.move(source_path, target_path)

            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": f"移动成功: {source_path} -> {target_path}",
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"移动失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _create_directory(self, directory_path: str) -> dict[str, Any]:
        """
        创建目录

        Args:
            directory_path: 目录路径

        Returns:
            执行结果
        """
        try:
            if os.path.exists(directory_path):
                if os.path.isdir(directory_path):
                    return {
                        "status": "success",
                        "observation": {
                            "data": None,
                            "message": f"目录已存在: {directory_path}",
                            "timestamp": self._get_timestamp(),
                        },
                    }
                else:
                    return {
                        "status": "error",
                        "observation": {
                            "data": None,
                            "message": f"路径已存在但不是目录: {directory_path}",
                            "timestamp": self._get_timestamp(),
                        },
                    }

            os.makedirs(directory_path, exist_ok=True)

            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": f"目录创建成功: {directory_path}",
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"创建目录失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _rename_file(self, old_path: str, new_path: str) -> dict[str, Any]:
        """
        重命名文件或目录

        Args:
            old_path: 原路径
            new_path: 新路径

        Returns:
            执行结果
        """
        try:
            if not os.path.exists(old_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"原路径不存在: {old_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            # 确保目标目录存在
            target_directory = os.path.dirname(new_path)
            if target_directory and not os.path.exists(target_directory):
                os.makedirs(target_directory, exist_ok=True)

            os.rename(old_path, new_path)

            return {
                "status": "success",
                "observation": {
                    "data": None,
                    "message": f"重命名成功: {old_path} -> {new_path}",
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"重命名失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _get_file_stat(self, file_path: str) -> dict[str, Any]:
        """
        获取文件或目录信息

        Args:
            file_path: 文件或目录路径

        Returns:
            执行结果
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"路径不存在: {file_path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            stat_info = os.stat(file_path)
            file_info = {
                "path": file_path,
                "type": "directory" if os.path.isdir(file_path) else "file",
                "size": stat_info.st_size,
                "mode": stat.filemode(stat_info.st_mode),
                "uid": stat_info.st_uid,
                "gid": stat_info.st_gid,
                "atime": stat_info.st_atime,
                "mtime": stat_info.st_mtime,
                "ctime": stat_info.st_ctime,
            }

            return {
                "status": "success",
                "observation": {
                    "data": file_info,
                    "message": f"获取文件信息成功: {file_path}",
                    "timestamp": self._get_timestamp(),
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"获取文件信息失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _security_check(self, path: str) -> None:
        """
        安全检查，防止路径遍历攻击

        Args:
            path: 要检查的路径

        Raises:
            ValueError: 如果路径不安全
        """
        # 基本的路径安全检查
        if ".." in path:
            raise ValueError("路径包含不安全的字符")

    def _get_timestamp(self) -> str:
        """
        获取当前时间戳

        Returns:
            str: 时间戳
        """
        from datetime import datetime
        return datetime.now().isoformat()
