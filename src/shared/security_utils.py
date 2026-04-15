import re
import html
from typing import Any, Dict, List, Optional, Union


def sanitize_input(input_data: Any) -> Any:
    """
    清理输入数据，防止注入攻击和XSS攻击
    
    Args:
        input_data: 输入数据，可以是字符串、字典、列表等
    
    Returns:
        清理后的数据
    """
    if isinstance(input_data, str):
        # 转义HTML特殊字符，防止XSS攻击
        return html.escape(input_data)
    elif isinstance(input_data, dict):
        # 递归处理字典
        return {key: sanitize_input(value) for key, value in input_data.items()}
    elif isinstance(input_data, list):
        # 递归处理列表
        return [sanitize_input(item) for item in input_data]
    else:
        # 其他类型直接返回
        return input_data


def validate_username(username: str) -> bool:
    """
    验证用户名
    
    Args:
        username: 用户名
    
    Returns:
        验证结果
    """
    # 用户名只能包含字母、数字和下划线，长度3-20
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))


def validate_password(password: str) -> bool:
    """
    验证密码强度
    
    Args:
        password: 密码
    
    Returns:
        验证结果
    """
    # 密码长度至少6位，包含至少一个字母和一个数字
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d).{6,50}$', password))


def validate_task_query(query: str) -> bool:
    """
    验证任务查询
    
    Args:
        query: 任务查询
    
    Returns:
        验证结果
    """
    # 任务查询长度5-1000
    return 5 <= len(query.strip()) <= 1000


def prevent_sql_injection(input_str: str) -> str:
    """
    防止SQL注入攻击
    
    Args:
        input_str: 输入字符串
    
    Returns:
        处理后的字符串
    """
    # 移除或转义SQL特殊字符
    sql_special_chars = ['\'', '"', ';', '--', '/*', '*/', 'xp_', 'exec', 'union', 'select', 'insert', 'update', 'delete', 'drop', 'alter']
    result = input_str
    for char in sql_special_chars:
        result = result.replace(char, '')
    return result


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
    
    Returns:
        验证结果
    """
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def validate_ip_address(ip: str) -> bool:
    """
    验证IP地址格式
    
    Args:
        ip: IP地址
    
    Returns:
        验证结果
    """
    return bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip))


def validate_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL地址
    
    Returns:
        验证结果
    """
    return bool(re.match(r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$', url))


def sanitize_file_name(file_name: str) -> str:
    """
    清理文件名，防止路径遍历攻击
    
    Args:
        file_name: 文件名
    
    Returns:
        清理后的文件名
    """
    # 移除路径分隔符和危险字符
    dangerous_chars = ['/', '\\', '..', '~', '|', '<', '>', ':', '*', '?', '"', '']
    result = file_name
    for char in dangerous_chars:
        result = result.replace(char, '')
    return result
