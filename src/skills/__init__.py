from .registry import skill_registry, SkillRegistry
from .git_helper import GitHelperTool
from .file_manager import FileManagerTool
from .calculator import CalculatorTool

__all__ = [
    "skill_registry",
    "SkillRegistry",
    "GitHelperTool",
    "FileManagerTool",
    "CalculatorTool",
    "get_all_skills"
]

def get_all_skills():
    """
    获取所有技能
    
    Returns:
        Dict[str, Type[BaseSkill]]: 技能字典
    """
    return skill_registry.get_all_skills()
