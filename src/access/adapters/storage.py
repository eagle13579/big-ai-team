from typing import Dict, Any, Optional
from abc import abstractmethod
import os
import boto3
from botocore.exceptions import NoCredentialsError
from .base import BaseAdapter, AdapterContext
from .registry import adapter_registry


class StorageAdapter(BaseAdapter[Dict[str, Any]]):
    """存储适配器基类"""
    
    async def execute(self, operation: str, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """执行存储操作"""
        if operation == "read":
            return await self.read(params, context)
        elif operation == "write":
            return await self.write(params, context)
        elif operation == "delete":
            return await self.delete(params, context)
        elif operation == "list":
            return await self.list(params, context)
        elif operation == "health_check":
            return await self._health_check(context)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    @abstractmethod
    async def read(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """读取文件"""
        pass
    
    @abstractmethod
    async def write(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """写入文件"""
        pass
    
    @abstractmethod
    async def delete(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """删除文件"""
        pass
    
    @abstractmethod
    async def list(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """列出文件"""
        pass
    
    async def _health_check(self, context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 尝试列出文件
            await self.list({}, context)
            return {
                "status": "healthy",
                "platform": self.platform,
                "timestamp": context.timestamp.isoformat() if context else None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "platform": self.platform,
                "error": str(e),
                "timestamp": context.timestamp.isoformat() if context else None
            }


class LocalStorageAdapter(StorageAdapter):
    """本地存储适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_path = self.config.config.get("base_path", "./storage")
        # 确保基础路径存在
        os.makedirs(self.base_path, exist_ok=True)
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        # 确保基础路径存在
        os.makedirs(self.base_path, exist_ok=True)
        self._set_initialized(True)
        return True
    
    async def read(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """读取文件"""
        file_path = params.get("path")
        if not file_path:
            raise ValueError("Path is required")
        
        full_path = os.path.join(self.base_path, file_path)
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "content": content
            }
        except Exception as e:
            raise Exception(f"Read operation failed: {str(e)}")
    
    async def write(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """写入文件"""
        file_path = params.get("path")
        content = params.get("content")
        
        if not file_path or content is None:
            raise ValueError("Path and content are required")
        
        full_path = os.path.join(self.base_path, file_path)
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True
            }
        except Exception as e:
            raise Exception(f"Write operation failed: {str(e)}")
    
    async def delete(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """删除文件"""
        file_path = params.get("path")
        if not file_path:
            raise ValueError("Path is required")
        
        full_path = os.path.join(self.base_path, file_path)
        
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                return {
                    "deleted": True
                }
            else:
                return {
                    "deleted": False
                }
        except Exception as e:
            raise Exception(f"Delete operation failed: {str(e)}")
    
    async def list(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """列出文件"""
        directory = params.get("directory", ".")
        full_path = os.path.join(self.base_path, directory)
        
        try:
            files = []
            for root, _, filenames in os.walk(full_path):
                for filename in filenames:
                    relative_path = os.path.relpath(os.path.join(root, filename), self.base_path)
                    files.append(relative_path)
            return {
                "files": files
            }
        except Exception as e:
            raise Exception(f"List operation failed: {str(e)}")
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        self._set_initialized(False)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "base_path": self.base_path,
            "exists": os.path.exists(self.base_path)
        }


class S3Adapter(StorageAdapter):
    """S3 存储适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.bucket_name = self.config.config.get("bucket_name")
        self.aws_access_key_id = self.config.config.get("aws_access_key_id")
        self.aws_secret_access_key = self.config.config.get("aws_secret_access_key")
        self.region_name = self.config.config.get("region_name", "us-east-1")
        self.client = None
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        if not self.bucket_name:
            raise ValueError("Bucket name is required")
        
        try:
            self.client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            # 测试连接
            self.client.head_bucket(Bucket=self.bucket_name)
            self._set_initialized(True)
            return True
        except NoCredentialsError:
            raise Exception("Invalid AWS credentials")
        except Exception as e:
            raise Exception(f"Failed to initialize S3 adapter: {str(e)}")
    
    async def read(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """读取文件"""
        if not self.client:
            await self.initialize(context)
        
        key = params.get("path")
        if not key:
            raise ValueError("Path (key) is required")
        
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            content = response["Body"].read().decode("utf-8")
            return {
                "content": content
            }
        except Exception as e:
            raise Exception(f"Read operation failed: {str(e)}")
    
    async def write(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """写入文件"""
        if not self.client:
            await self.initialize(context)
        
        key = params.get("path")
        content = params.get("content")
        
        if not key or content is None:
            raise ValueError("Path (key) and content are required")
        
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/plain"
            )
            return {
                "success": True
            }
        except Exception as e:
            raise Exception(f"Write operation failed: {str(e)}")
    
    async def delete(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """删除文件"""
        if not self.client:
            await self.initialize(context)
        
        key = params.get("path")
        if not key:
            raise ValueError("Path (key) is required")
        
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return {
                "deleted": True
            }
        except Exception as e:
            raise Exception(f"Delete operation failed: {str(e)}")
    
    async def list(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """列出文件"""
        if not self.client:
            await self.initialize(context)
        
        prefix = params.get("directory", "")
        
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    files.append(obj["Key"])
            return {
                "files": files
            }
        except Exception as e:
            raise Exception(f"List operation failed: {str(e)}")
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        self.client = None
        self._set_initialized(False)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "bucket_name": self.bucket_name,
            "region_name": self.region_name
        }


# 注册存储适配器
adapter_registry.register("local_storage", LocalStorageAdapter)
adapter_registry.register("s3", S3Adapter)
