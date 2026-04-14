#!/usr/bin/env python3
"""
测试监控系统初始化
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.shared.monitoring import init_monitoring

if __name__ == "__main__":
    print("测试监控系统初始化...")
    init_monitoring()
    print("测试完成")
