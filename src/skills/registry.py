import importlib
import inspect
import os

from src.shared.base import BaseSkill


class SkillRegistry:
    """
    技能注册表，负责自动发现和注册技能
    """

    def __init__(self):
        self.skills: dict[str, type[BaseSkill]] = {}
        self._discover_skills()

    def _discover_skills(self):
        """
        自动发现技能
        """
        # 获取skills目录路径
        skills_dir = os.path.dirname(os.path.abspath(__file__))

        # 递归遍历skills目录及其子目录
        for root, _dirs, files in os.walk(skills_dir):
            # 跳过__pycache__目录
            if "__pycache__" in root:
                continue

            # 计算相对路径，用于构建模块名
            relative_path = os.path.relpath(root, skills_dir)
            if relative_path == ".":
                module_prefix = "src.skills"
            else:
                # 将路径分隔符替换为点
                module_prefix = f"src.skills.{relative_path.replace(os.path.sep, '.')}"

            # 遍历当前目录中的文件
            for filename in files:
                # 跳过__init__.py和registry.py
                if filename == "__init__.py" or (
                    relative_path == "." and filename == "registry.py"
                ):
                    continue

                # 只处理.py文件
                if not filename.endswith(".py"):
                    continue

                # 提取模块名
                module_name = filename[:-3]  # 移除.py后缀
                full_module_name = f"{module_prefix}.{module_name}"

                try:
                    # 导入模块
                    module = importlib.import_module(full_module_name)

                    # 遍历模块中的所有类
                    for _name, obj in inspect.getmembers(module, inspect.isclass):
                        # 检查是否是BaseSkill的子类且不是BaseSkill本身
                        if issubclass(obj, BaseSkill) and obj != BaseSkill:
                            # 注册技能
                            if hasattr(obj, "name") and obj.name:
                                skill_name = obj.name
                            else:
                                skill_name = module_name

                            self.skills[skill_name] = obj
                            print(f"Registered skill: {skill_name} ({obj.__name__})")

                except Exception as e:
                    print(f"Error importing skill module {full_module_name}: {e}")

    def get_skill(self, name: str) -> type[BaseSkill]:
        """
        获取技能类

        Args:
            name: 技能名称

        Returns:
            Type[BaseSkill]: 技能类
        """
        return self.skills.get(name)

    def get_all_skills(self) -> dict[str, type[BaseSkill]]:
        """
        获取所有技能

        Returns:
            Dict[str, Type[BaseSkill]]: 技能字典
        """
        return self.skills

    def get_skill_names(self) -> list[str]:
        """
        获取所有技能名称

        Returns:
            List[str]: 技能名称列表
        """
        return list(self.skills.keys())


# 创建全局技能注册表实例
skill_registry = SkillRegistry()
