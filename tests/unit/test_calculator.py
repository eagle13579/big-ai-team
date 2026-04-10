import os
import sys

# 确保项目根目录在 Python 搜索路径中
# 尝试多种可能的路径组合
possible_roots = [
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),  # 常见情况：tests/ 目录在项目根目录下
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    ),  # 特殊情况：tests/ 目录在更深层
    os.path.abspath("."),  # 当前目录
    os.path.abspath(".."),  # 父目录
]

for root in possible_roots:
    if os.path.exists(os.path.join(root, "src")):
        sys.path.insert(0, root)
        print(f"Added project root to path: {root}")
        break

import pytest

from src.skills.calculator import CalculatorTool


@pytest.fixture
def calculator_tool():
    """创建CalculatorTool实例"""
    return CalculatorTool()


def test_add_operation(calculator_tool):
    """测试加法操作"""
    result = calculator_tool.execute({"operation": "add", "a": 10, "b": 5})

    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "data" in result["observation"]
    assert result["observation"]["data"] == 15
    assert "10 + 5 = 15" in result["observation"]["message"]


def test_subtract_operation(calculator_tool):
    """测试减法操作"""
    result = calculator_tool.execute({"operation": "subtract", "a": 10, "b": 5})

    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "data" in result["observation"]
    assert result["observation"]["data"] == 5
    assert "10 - 5 = 5" in result["observation"]["message"]


def test_multiply_operation(calculator_tool):
    """测试乘法操作"""
    result = calculator_tool.execute({"operation": "multiply", "a": 10, "b": 5})

    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "data" in result["observation"]
    assert result["observation"]["data"] == 50
    assert "10 * 5 = 50" in result["observation"]["message"]


def test_divide_operation(calculator_tool):
    """测试除法操作"""
    result = calculator_tool.execute({"operation": "divide", "a": 10, "b": 5})

    # 验证结果
    assert result["status"] == "success"
    assert "observation" in result
    assert "data" in result["observation"]
    assert result["observation"]["data"] == 2
    assert "10 / 5 = 2" in result["observation"]["message"]


def test_divide_by_zero(calculator_tool):
    """测试除以零的情况"""
    result = calculator_tool.execute({"operation": "divide", "a": 10, "b": 0})

    # 验证结果
    assert result["status"] == "error"
    assert "observation" in result
    assert "除数不能为零" in result["observation"]["message"]


def test_invalid_operation(calculator_tool):
    """测试无效的操作类型"""
    result = calculator_tool.execute({"operation": "invalid", "a": 10, "b": 5})

    # 验证结果
    assert result["status"] == "error"
    assert "observation" in result
    assert "不支持的操作类型" in result["observation"]["message"]


def test_exception_handling(calculator_tool):
    """测试异常处理"""
    # 测试非数字输入
    result = calculator_tool.execute({"operation": "add", "a": "10", "b": 5})

    # 验证结果
    assert result["status"] == "error"
    assert "observation" in result
    assert "操作数必须是数字" in result["observation"]["message"]
