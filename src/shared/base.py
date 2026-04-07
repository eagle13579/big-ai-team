"""
Ace AI Engine - 基础类模块
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel


class BaseSkill(ABC):
    """
    技能基类
    所有技能都必须继承自此类
    """

    # 技能名称
    name: str = ""
    
    # 技能描述
    description: str = ""
    
    # 参数校验架构
    args_schema: Optional[Type[BaseModel]] = None

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            args: 技能参数
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    def _get_timestamp(self) -> str:
        """
        获取当前时间戳
        
        Returns:
            str: 时间戳字符串
        """
        from datetime import datetime
        return datetime.now().isoformat() + "Z"
