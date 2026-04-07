from typing import Dict, Any, Type
from pydantic import BaseModel, Field
from src.shared.base import BaseSkill


class CalculatorArgs(BaseModel):
    """计算器工具的参数校验模型"""
    operation: str = Field(..., description="操作类型: 'add', 'subtract', 'multiply', 'divide'")
    a: float = Field(..., description="第一个数字")
    b: float = Field(..., description="第二个数字")


class CalculatorTool(BaseSkill):
    """
    Ace AI Engine 官方计算器工具
    支持基本的数学运算
    """
    name: str = "calculator"
    description: str = "用于执行基本的数学运算，如加法、减法、乘法和除法。"
    args_schema: Type[BaseModel] = CalculatorArgs

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 提取参数
            operation = args.get("operation")
            a = args.get("a")
            b = args.get("b")
            
            # 执行计算
            if operation == "add":
                result = a + b
                message = f"{a} + {b} = {result}"
            elif operation == "subtract":
                result = a - b
                message = f"{a} - {b} = {result}"
            elif operation == "multiply":
                result = a * b
                message = f"{a} * {b} = {result}"
            elif operation == "divide":
                if b == 0:
                    return {
                        "status": "error",
                        "observation": {
                            "data": None,
                            "message": "除数不能为零",
                            "timestamp": "2026-04-07T00:57:00Z"
                        }
                    }
                result = a / b
                message = f"{a} / {b} = {result}"
            else:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"不支持的操作类型: {operation}",
                        "timestamp": "2026-04-07T00:57:00Z"
                    }
                }
            
            return {
                "status": "success",
                "observation": {
                    "data": result,
                    "message": message,
                    "timestamp": "2026-04-07T00:57:00Z"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"计算异常: {str(e)}",
                    "timestamp": "2026-04-07T00:57:00Z"
                }
            }
