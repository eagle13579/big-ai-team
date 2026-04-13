import os
import shutil
from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator

from src.shared.base import BaseSkill
from src.shared.utils import sanitize_path


class FileOpsArgsSchema(BaseModel):
    """文件操作的参数校验架构"""

    operation: str = Field(
        ..., description="操作类型: read, write, list, delete, copy, move, mkdir, rename"
    )
    path: str = Field(..., description="文件或目录路径")
    content: str | None = Field(default=None, description="写入文件的内容")
    target: str | None = Field(default=None, description="复制、移动或重命名的目标路径")

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
        ]
        if v not in valid_operations:
            raise ValueError(f"不支持的操作类型: {v}，支持的操作类型: {valid_operations}")
        return v

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v, info):
        if info.data.get("operation") == "write" and v is None:
            raise ValueError("写入操作必须提供 content 参数")
        return v

    @field_validator("target", mode="before")
    @classmethod
    def validate_target(cls, v, info):
        operation = info.data.get("operation")
        if operation in ["copy", "move", "rename"] and not v:
            raise ValueError(f"{operation} 操作必须提供 target 参数")
        return v


class FileOpsTool(BaseSkill):
    """
    Ace AI Engine - 文件操作工具
    用于执行基本的文件系统操作
    """

    name = "file_ops"
    description = "用于执行基本的文件系统操作，支持读取、写入、列出、删除、复制、移动、重命名文件和创建目录。"
    args_schema = FileOpsArgsSchema

    def __init__(self):
        """初始化文件操作工具"""
        super().__init__()
        # 操作映射表
        self.operations = {
            "read": self._read_file,
            "write": self._write_file,
            "list": self._list_directory,
            "delete": self._delete,
            "copy": self._copy,
            "move": self._move,
            "mkdir": self._mkdir,
            "rename": self._rename,
        }

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        执行文件系统操作

        Args:
            args: 操作参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
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
            
            # 检查复制、移动、重命名操作是否提供 target
            if operation in ["copy", "move", "rename"] and "target" not in args:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"{operation} 操作必须提供 target 参数",
                        "timestamp": self._get_timestamp(),
                    },
                }

            # 安全检查
            if "path" in args:
                self._security_check(args["path"])
            if "target" in args and args["target"]:
                self._security_check(args["target"])

            # 验证参数
            validated_args = FileOpsArgsSchema(**args)

            # 执行操作
            operation = validated_args.operation
            path = sanitize_path(validated_args.path)
            content = validated_args.content
            target = sanitize_path(validated_args.target) if validated_args.target else None

            # 规范化路径
            path = os.path.abspath(path)
            if target:
                target = os.path.abspath(target)

            # 使用映射表执行操作
            if operation in self.operations:
                if operation in ["copy", "move", "rename"]:
                    return self.operations[operation](path, target)
                elif operation == "write":
                    return self.operations[operation](path, content)
                else:
                    return self.operations[operation](path)
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
            # 检查是否是缺少目标路径
            if "expected str, bytes or os.PathLike object, not NoneType" in str(e):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"{operation} 操作必须提供 target 参数",
                        "timestamp": self._get_timestamp(),
                    },
                }
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"操作失败: {str(e)}",
                    "timestamp": self._get_timestamp(),
                },
            }

    def _read_file(self, file_path: str) -> dict[str, Any]:
        """读取文件内容"""
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

            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
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

    def _write_file(self, file_path: str, content: str) -> dict[str, Any]:
        """写入文件内容"""
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
        """列出目录内容"""
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

    def _delete(self, path: str) -> dict[str, Any]:
        """删除文件或目录"""
        try:
            if not os.path.exists(path):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"路径不存在: {path}",
                        "timestamp": self._get_timestamp(),
                    },
                }

            if os.path.isfile(path):
                os.remove(path)
                message = f"文件删除成功: {path}"
            else:
                shutil.rmtree(path)
                message = f"目录删除成功: {path}"

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

    def _copy(self, source_path: str, target_path: str) -> dict[str, Any]:
        """复制文件或目录"""
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

    def _move(self, source_path: str, target_path: str) -> dict[str, Any]:
        """移动文件或目录"""
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

    def _mkdir(self, directory_path: str) -> dict[str, Any]:
        """创建目录"""
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

    def _rename(self, old_path: str, new_path: str) -> dict[str, Any]:
        """重命名文件或目录"""
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

    def _security_check(self, path: str) -> None:
        """安全检查，防止路径遍历攻击"""
        if ".." in path:
            raise ValueError("路径包含不安全的字符")

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
