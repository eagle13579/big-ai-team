import asyncio
import os
import subprocess
import sys
import tempfile

from src.shared.logging import logger
from src.skills.registry import register_skill


class CodeInterpreterSkill:
    """代码解释器技能，用于执行Python代码"""
    
    def __init__(self):
        self.skill_name = "code_interpreter"
        self.description = "执行Python代码并返回结果"
        self.logger = logger.bind(skill=self.skill_name)
    
    async def execute(self, code: str, **kwargs):
        """
        执行Python代码
        
        Args:
            code: 要执行的Python代码
            **kwargs: 额外参数
            
        Returns:
            dict: 执行结果，包含output和error字段
        """
        try:
            self.logger.info(f"执行代码: {code[:100]}...")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # 执行代码
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30  # 30秒超时
                )
                
                output = result.stdout.strip()
                error = result.stderr.strip()
                
                if result.returncode == 0:
                    self.logger.info("代码执行成功")
                    return {
                        "status": "success",
                        "output": output,
                        "error": error
                    }
                else:
                    self.logger.warning(f"代码执行失败: {error}")
                    return {
                        "status": "error",
                        "output": output,
                        "error": error
                    }
            finally:
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except subprocess.TimeoutExpired:
            self.logger.error("代码执行超时")
            return {
                "status": "error",
                "output": "",
                "error": "代码执行超时（30秒）"
            }
        except Exception as e:
            self.logger.error(f"执行代码时发生错误: {str(e)}")
            return {
                "status": "error",
                "output": "",
                "error": str(e)
            }
    
    def get_info(self):
        """
        获取技能信息
        
        Returns:
            dict: 技能信息
        """
        return {
            "name": self.skill_name,
            "description": self.description,
            "parameters": {
                "code": "string, 要执行的Python代码",
                "timeout": "int, 执行超时时间（秒）"
            }
        }


# 注册技能
register_skill("code_interpreter", CodeInterpreterSkill())