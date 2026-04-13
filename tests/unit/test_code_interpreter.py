import asyncio
import unittest

from src.skills.code_interpreter import CodeInterpreterSkill


class TestCodeInterpreterSkill(unittest.IsolatedAsyncioTestCase):
    """测试代码解释器技能"""
    
    def setUp(self):
        """设置测试环境"""
        self.skill = CodeInterpreterSkill()
    
    async def test_execute_simple_code(self):
        """测试执行简单代码"""
        code = "print('Hello, World!')"
        result = await self.skill.execute(code)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "Hello, World!")
        self.assertEqual(result["error"], "")
    
    async def test_execute_calculation(self):
        """测试执行计算代码"""
        code = "print(1 + 2 + 3)"
        result = await self.skill.execute(code)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "6")
    
    async def test_execute_error_code(self):
        """测试执行错误代码"""
        code = "print(undefined_variable)"
        result = await self.skill.execute(code)
        self.assertEqual(result["status"], "error")
        self.assertIn("NameError", result["error"])
    
    async def test_execute_complex_code(self):
        """测试执行复杂代码"""
        code = """
for i in range(3):
    print(f"Iteration {i}")
print("Done")
"""
        result = await self.skill.execute(code)
        self.assertEqual(result["status"], "success")
        self.assertIn("Iteration 0", result["output"])
        self.assertIn("Iteration 1", result["output"])
        self.assertIn("Iteration 2", result["output"])
        self.assertIn("Done", result["output"])
    
    async def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        self.assertEqual(info["name"], "code_interpreter")
        self.assertEqual(info["description"], "执行Python代码并返回结果")
        self.assertIn("code", info["parameters"])
        self.assertIn("timeout", info["parameters"])
    
    def test_sync(self):
        """同步测试入口"""
        asyncio.run(self.test_execute_simple_code())
        asyncio.run(self.test_execute_calculation())
        asyncio.run(self.test_execute_error_code())
        asyncio.run(self.test_execute_complex_code())
        asyncio.run(self.test_get_info())


if __name__ == "__main__":
    unittest.main()