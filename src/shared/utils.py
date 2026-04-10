import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt

from .config import settings

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4())


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict[str, Any]]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def setup_logger() -> logging.Logger:
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logger


def safe_json_loads(data: str) -> Optional[dict[str, Any]]:
    """安全地解析JSON"""
    import json

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def sanitize_path(path: str) -> str:
    """安全处理路径

    Args:
        path: 原始路径

    Returns:
        安全处理后的路径
    """
    # 规范化路径
    path = os.path.normpath(path)
    # 移除路径中的危险字符
    path = path.replace("..", "")
    return path
