import hashlib
import hmac
import time
from typing import Dict, Any, Optional
from collections import defaultdict
from .logger import logger


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        初始化速率限制器
        
        Args:
            max_requests: 时间窗口内的最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # key: user/IP, value: list of timestamps
    
    def is_allowed(self, key: str) -> bool:
        """
        检查请求是否允许
        
        Args:
            key: 请求标识（如用户ID或IP地址）
        
        Returns:
            bool: 是否允许请求
        """
        current_time = time.time()
        
        # 清理过期的请求记录
        self.requests[key] = [
            timestamp for timestamp in self.requests[key] 
            if current_time - timestamp < self.window_seconds
        ]
        
        # 检查是否超过限制
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(current_time)
            return True
        else:
            logger.warning(f"Rate limit exceeded for {key}")
            return False
    
    def reset(self, key: Optional[str] = None):
        """
        重置速率限制
        
        Args:
            key: 请求标识，None 表示重置所有
        """
        if key:
            del self.requests[key]
        else:
            self.requests.clear()


class RequestSigner:
    """请求签名器"""
    
    @staticmethod
    def generate_signature(data: Dict[str, Any], secret: str) -> str:
        """
        生成请求签名
        
        Args:
            data: 请求数据
            secret: 签名密钥
        
        Returns:
            str: 签名
        """
        # 按字典序排序键
        sorted_keys = sorted(data.keys())
        # 构建签名字符串
        signature_string = "&".join([f"{key}={data[key]}" for key in sorted_keys])
        # 生成 HMAC SHA256 签名
        signature = hmac.new(
            secret.encode(),
            signature_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(data: Dict[str, Any], signature: str, secret: str) -> bool:
        """
        验证请求签名
        
        Args:
            data: 请求数据
            signature: 待验证的签名
            secret: 签名密钥
        
        Returns:
            bool: 签名是否有效
        """
        expected_signature = RequestSigner.generate_signature(data, secret)
        return hmac.compare_digest(signature, expected_signature)


# 全局速率限制器实例
global_rate_limiter = RateLimiter()
