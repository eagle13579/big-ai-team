#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日志修复是否成功
"""
import os
import sys
import datetime

print("=" * 80)
print("🧪 测试日志修复")
print("=" * 80)
print()

# 1. 测试导入项目 logging 模块
print("1️⃣  测试导入项目 logging 模块")
print("-" * 60)
try:
    from src.shared.logging import logger
    print("✅ 成功导入 logger")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# 2. 测试写入一些日志
print("2️⃣  测试使用 loguru logger 写入日志")
print("-" * 60)
logger.info("这是一条 INFO 级别日志")
logger.warning("这是一条 WARNING 级别日志")
logger.error("这是一条 ERROR 级别日志")
print("✅ 已写入 3 条 loguru 日志")

print()

# 3. 测试标准库 logging 是否被拦截
print("3️⃣  测试标准库 logging 是否被拦截")
print("-" * 60)
import logging as std_logging
std_logger = std_logging.getLogger("TestStdLogging")
std_logger.info("这是一条标准库 INFO 日志")
std_logger.warning("这是一条标准库 WARNING 日志")
print("✅ 已写入 2 条标准库 logging 日志")

print()

# 4. 检查日志文件
print("4️⃣  检查日志文件")
print("-" * 60)
log_file = os.path.join("logs", f"agent_{datetime.datetime.now().strftime('%Y%m%d')}.log")
if os.path.exists(log_file):
    size = os.path.getsize(log_file)
    print(f"✅ 日志文件存在: {log_file}")
    print(f"   文件大小: {size} bytes")
    
    if size > 0:
        print(f"\n📄 日志文件内容:")
        print("=" * 60)
        with open(log_file, 'r', encoding='utf-8') as f:
            print(f.read())
        print("=" * 60)
        print("\n✅ 日志文件包含内容！修复成功！")
    else:
        print("❌ 日志文件为空")
else:
    print(f"❌ 日志文件不存在: {log_file}")

print()
print("=" * 80)
print("🎉 测试完成！")
print("=" * 80)
