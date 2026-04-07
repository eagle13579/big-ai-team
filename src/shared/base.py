from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from pydantic import BaseModel


class BaseSkill(ABC):
    """
    技能基类，所有技能都应继承此类
    """
    
    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = None
    
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
