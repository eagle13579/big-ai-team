from typing import Dict, Any, Callable
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Type
from pydantic import BaseModel, Field
from src.shared.base import BaseSkill
import math


class CalculatorArgsSchema(BaseModel):
    """计算器操作的参数校验架构"""
    operation: str = Field(..., description="操作类型: add, subtract, multiply, divide, power, sqrt, sin, cos, tan, log, log10, exp, abs")
    a: float = Field(..., description="第一个操作数")
    b: float = Field(default=0.0, description="第二个操作数，某些操作不需要")

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v):
        valid_operations = ["add", "subtract", "multiply", "divide", "power", "sqrt", "sin", "cos", "tan", "log", "log10", "exp", "abs"]
        if v not in valid_operations:
            raise ValueError(f"不支持的操作类型: {v}，支持的操作类型: {valid_operations}")
        return v

    @field_validator("b")
    @classmethod
    def validate_divisor(cls, v, info):
        operation = info.data.get("operation")
        if operation == "divide" and v == 0:
            raise ValueError("除数不能为零")
        return v

    @field_validator("a")
    @classmethod
    def validate_arguments(cls, v, info):
        operation = info.data.get("operation")
        if operation == "sqrt" and v < 0:
            raise ValueError("平方根操作的参数不能为负数")
        elif operation == "log" and v <= 0:
            raise ValueError("自然对数操作的参数必须大于零")
        elif operation == "log10" and v <= 0:
            raise ValueError("常用对数操作的参数必须大于零")
        return v


class CalculatorTool(BaseSkill):
    """
    Ace AI Engine - 计算器工具
    用于执行基本的数学运算
    """

    name = "calculator"
    description = "用于执行基本的数学运算，支持加法、减法、乘法、除法、幂运算、平方根、三角函数、对数函数和指数函数等操作。"
    args_schema = CalculatorArgsSchema

    def __init__(self):
        """初始化计算器工具"""
        super().__init__()
        # 操作映射表，使用字典替代if-elif链
        self.operations: Dict[str, Callable[[float, float], float]] = {
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "multiply": lambda a, b: a * b,
            "divide": lambda a, b: a / b,
            "power": lambda a, b: a ** b,
            "sqrt": lambda a, _: math.sqrt(a),
            "sin": lambda a, _: math.sin(a),
            "cos": lambda a, _: math.cos(a),
            "tan": lambda a, _: math.tan(a),
            "log": lambda a, _: math.log(a),
            "log10": lambda a, _: math.log10(a),
            "exp": lambda a, _: math.exp(a),
            "abs": lambda a, _: abs(a)
        }

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数学运算

        Args:
            args: 操作参数，包含 operation, a, b

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 验证参数类型
            if not isinstance(args.get("a"), (int, float)) or not isinstance(args.get("b"), (int, float)):
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": "操作数必须是数字",
                        "timestamp": self._get_timestamp()
                    }
                }
            
            # 验证参数
            validated_args = CalculatorArgsSchema(**args)

            # 执行运算
            operation = validated_args.operation
            a = validated_args.a
            b = validated_args.b

            # 使用映射表执行操作
            if operation in self.operations:
                result = self.operations[operation](a, b)
                # 格式化结果消息
                message = self._format_result_message(operation, a, b, result)
            else:
                return {
                    "status": "error",
                    "observation": {
                        "data": None,
                        "message": f"不支持的操作类型: {operation}",
                        "timestamp": self._get_timestamp()
                    }
                }

            return {
                "status": "success",
                "observation": {
                    "data": result,
                    "message": message,
                    "timestamp": self._get_timestamp()
                }
            }

        except ValueError as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": str(e),
                    "timestamp": self._get_timestamp()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "observation": {
                    "data": None,
                    "message": f"计算异常: {str(e)}",
                    "timestamp": self._get_timestamp()
                }
            }

    def _format_result_message(self, operation: str, a: float, b: float, result: float) -> str:
        """
        格式化结果消息

        Args:
            operation: 操作类型
            a: 第一个操作数
            b: 第二个操作数
            result: 计算结果

        Returns:
            str: 格式化的结果消息
        """
        # 辅助函数：将数字转换为整数（如果可能）
        def format_number(num):
            if num.is_integer():
                return int(num)
            return num
        
        # 单参数操作
        single_arg_ops = ["sqrt", "sin", "cos", "tan", "log", "log10", "exp", "abs"]
        if operation in single_arg_ops:
            if operation == "sqrt":
                return f"√{format_number(a)} = {result}"
            elif operation == "sin":
                return f"sin({format_number(a)}) = {result}"
            elif operation == "cos":
                return f"cos({format_number(a)}) = {result}"
            elif operation == "tan":
                return f"tan({format_number(a)}) = {result}"
            elif operation == "log":
                return f"ln({format_number(a)}) = {result}"
            elif operation == "log10":
                return f"log10({format_number(a)}) = {result}"
            elif operation == "exp":
                return f"e^{format_number(a)} = {result}"
            elif operation == "abs":
                return f"|{format_number(a)}| = {result}"
        # 双参数操作
        else:
            symbol = self._get_operation_symbol(operation)
            return f"{format_number(a)} {symbol} {format_number(b)} = {format_number(result)}"

    def _get_operation_symbol(self, operation: str) -> str:
        """
        获取操作的符号

        Args:
            operation: 操作类型

        Returns:
            str: 操作符号
        """
        symbols = {
            "add": "+",
            "subtract": "-",
            "multiply": "*",
            "divide": "/",
            "power": "^"
        }
        return symbols.get(operation, operation)

