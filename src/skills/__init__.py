"""
Ace AI Engine - 技能模块
"""

from typing import Dict, Type, List
from src.shared.base import BaseSkill
import importlib
import os
import logging

# 配置日志
logger = logging.getLogger("AceAgent.Skills")


class SkillRegistry:
    """
    技能注册表
    用于自动发现和注册技能
    """

    def __init__(self):
        self.skills: Dict[str, Type[BaseSkill]] = {}
        self._discover_skills()

    def _discover_skills(self):
        """
        自动发现技能
        扫描 src/skills/ 目录及其子目录，发现所有继承自 BaseSkill 的类
        """
        skills_dir = os.path.dirname(__file__)
        
        # 遍历所有 .py 文件
        for root, _, files in os.walk(skills_dir):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    # 计算模块路径
                    relative_path = os.path.relpath(os.path.join(root, file), skills_dir)
                    module_path = relative_path.replace(os.path.sep, '.').replace('.py', '')
                    full_module_path = f'src.skills.{module_path}'
                    
                    try:
                        # 导入模块
                        module = importlib.import_module(full_module_path)
                        
                        # 查找继承自 BaseSkill 的类
                        for name, obj in module.__dict__.items():
                            if (
                                isinstance(obj, type) and
                                issubclass(obj, BaseSkill) and
                                obj != BaseSkill
                            ):
                                # 注册技能
                                skill_name = getattr(obj, 'name', name.lower())
                                self.skills[skill_name] = obj
                                logger.info(f"Registered skill: {skill_name} ({name})")
                    except Exception as e:
                        logger.error(f"Error importing module {full_module_path}: {e}")

    def get_skill(self, name: str) -> Type[BaseSkill]:
        """
        获取技能类
        
        Args:
            name: 技能名称
        
        Returns:
            Type[BaseSkill]: 技能类
        
        Raises:
            ValueError: 如果技能不存在
        """
        if name not in self.skills:
            raise ValueError(f"Skill not found: {name}")
        return self.skills[name]

    def get_skill_names(self) -> List[str]:
        """
        获取所有技能名称
        
        Returns:
            List[str]: 技能名称列表
        """
        return list(self.skills.keys())

    def get_all_skills(self) -> Dict[str, Type[BaseSkill]]:
        """
        获取所有技能
        
        Returns:
            Dict[str, Type[BaseSkill]]: 技能字典
        """
        return self.skills


# 创建全局技能注册表实例
skill_registry = SkillRegistry()


# 导出函数
def get_all_skills() -> Dict[str, Type[BaseSkill]]:
    """
    获取所有技能
    
    Returns:
        Dict[str, Type[BaseSkill]]: 技能字典
    """
    return skill_registry.get_all_skills()


# 导出技能类
try:
    from src.skills.calculator import CalculatorTool
    from src.skills.file_manager import FileManagerTool
    from src.skills.git_helper import GitHelperTool
    
    __all__ = [
        'CalculatorTool',
        'FileManagerTool',
        'GitHelperTool',
        'skill_registry',
        'get_all_skills'
    ]
except ImportError as e:
    logger.error(f"Error importing skills: {e}")
    __all__ = ['skill_registry', 'get_all_skills']

