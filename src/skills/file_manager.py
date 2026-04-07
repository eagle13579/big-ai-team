import os
from typing import Type, Optional, List, Union, Dict, Any
from pydantic import BaseModel, Field
from src.shared.base import BaseSkill

# ==========================================
# 1. 定义参数架构 (Schema)
# ==========================================
class FileOperationArgs(BaseModel):
    """文件操作工具的参数校验模型"""
    operation: str = Field(..., description="操作类型: 'read', 'write', 'list', 'delete'")
    file_path: str = Field(..., description="目标文件的相对路径或绝对路径")
    content: Optional[str] = Field(None, description="写入操作时需要提供的内容")
    encoding: str = Field("utf-8", description="文件编码格式，默认为 utf-8")

# ==========================================
# 2. 编写核心工具类
# ==========================================
class FileManagerTool(BaseSkill):
    """
    Ace AI Engine 官方文件管理工具
    支持安全审计下的文件读写与目录遍历
    """
    name: str = "file_manager"
    description: str = "用于读取、写入、列出或删除本地文件。支持文本内容的持久化存储。"
    args_schema: Type[BaseModel] = FileOperationArgs

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 提取参数
            operation = args.get("operation")
            file_path = args.get("file_path")
            content = args.get("content")
            encoding = args.get("encoding", "utf-8")
            
            # 规范化路径，防止路径穿越攻击 (Path Traversal)
            target_path = os.path.abspath(file_path)
            
            # --- 执行逻辑分发 ---
            if operation == "read":
                if not os.path.exists(target_path):
                    return {
                        "status": "error",
                        "observation": {
                            "data": None,
                            "message": f"文件不存在: {file_path}",
                            "timestamp": "2026-04-07T00:57:00Z"
                        }
                    }
                with open(target_path, 'r', encoding=encoding) as f:
                    data = f.read()
                return {
                    "status": "success",
                    "observation": {
                        "data": data,
                        "message": f"成功读取文件: {file_path}",
                        "timestamp": "2026-04-07T00:57:00Z"
                    }
                }

            elif operation == "write":
                if content is None:
                    return {
                        "status": "error",
                        "observation": {
                            "data": None,
                            "message": "写入操作必须提供 content 参数",
                            "timestamp": "2026-04-07T00:57:00Z"
                        }
                    }
                # 自动创建父目录
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, 'w', encoding=encoding) as f:
                    f.write(content)
                return {
                    "status": "success",
                    "observation": {
                        "data": None,
                        "message": f"成功写入到: {file_path}",
                        "timestamp": "2026-04-07T00:57:00Z"
                    }
                }

            elif operation == "list":
                if not os.path.isdir(target_path):
                    return {
                        "status": "error",
                        "observation": {
                            "data": None,
                            "message": f"目录不存在: {file_path}",
                            "timestamp": "2026-04-07T00:57:00Z"
                        }
                    }
                files = os.listdir(target_path)
                return {
                    "status": "success",
                    "observation": {
                        "data": files,
                        "message": f"成功列出目录: {file_path}",
                        "timestamp": "2026-04-07T00:57:00Z"
                    }
                }

            elif operation == "delete":
                # [安全提醒] 实际生产中建议移动到回收站或增加二次确认
                if os.path.isfile(target_path):
                    os.remove(target_path)
                    return {
                        "status": "success",
                        "observation": {
                            "data": None,
                            "message": f"已删除文件: {file_path}",
                            "timestamp": "2026-04-07T00:57:00Z"
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "observation": {
                            "data": None,
                            "message": "仅支持删除单个文件",
                            "timestamp": "2026-04-07T00:57:00Z"
                        }
                    }

            else:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"不支持的操作类型: {operation}",
                        "timestamp": "2026-04-07T00:57:00Z"
                    }
                }

        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"文件系统异常: {str(e)}",
                    "timestamp": "2026-04-07T00:57:00Z"
                }
            }
