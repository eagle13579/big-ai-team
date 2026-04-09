#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MECE诊断脚本：日志不显示问题
覆盖所有可能的原因分类
"""
import os
import sys
import datetime
import importlib.util


def diagnose_logging():
    print("=" * 80)
    print("🔍 MECE 诊断：日志系统问题")
    print("=" * 80)
    print()
    
    # MECE 分类1：基础环境检查
    print("📁 分类1：基础环境检查")
    print("-" * 60)
    
    # 检查 logs 目录
    log_dir = "logs"
    print(f"1.1 检查 logs 目录:")
    if os.path.exists(log_dir):
        print(f"    ✅ 目录存在: {os.path.abspath(log_dir)}")
        files = os.listdir(log_dir)
        print(f"    目录内容: {files}")
    else:
        print(f"    ❌ 目录不存在")
        try:
            os.makedirs(log_dir, exist_ok=True)
            print(f"    ✅ 已创建目录")
        except Exception as e:
            print(f"    ❌ 创建目录失败: {e}")
    
    # 检查今天的日期
    today = datetime.datetime.now().strftime("%Y%m%d")
    print(f"\n1.2 今天的日期: {today}")
    
    # 检查文件权限
    print(f"\n1.3 检查文件权限:")
    test_file = os.path.join(log_dir, f"test_{today}.log")
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试写入\n")
        print(f"    ✅ 可以写入文件: {test_file}")
        os.remove(test_file)
    except Exception as e:
        print(f"    ❌ 写入文件失败: {e}")
    
    print()
    
    # MECE 分类2：loguru 基础功能
    print("🔧 分类2：loguru 基础功能测试")
    print("-" * 60)
    
    try:
        from loguru import logger
        
        print("2.1 直接测试 loguru (无配置):")
        # 临时添加简单的文件输出
        test_log_file = os.path.join(log_dir, "loguru_test.log")
        logger.add(test_log_file, format="{time} | {level} | {message}")
        
        test_message = "loguru 直接测试消息"
        logger.info(test_message)
        print(f"    ✅ 已写入测试消息: {test_message}")
        
        # 检查文件
        if os.path.exists(test_log_file):
            size = os.path.getsize(test_log_file)
            print(f"    ✅ 测试文件大小: {size} bytes")
            with open(test_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"    内容:\n{content}")
            os.remove(test_log_file)
        else:
            print(f"    ❌ 测试文件未创建")
        
        # 移除临时处理器
        logger.remove()
        
    except ImportError as e:
        print(f"    ❌ loguru 导入失败: {e}")
        return
    except Exception as e:
        print(f"    ❌ loguru 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # MECE 分类3：项目日志模块
    print("📦 分类3：项目日志模块检查")
    print("-" * 60)
    
    # 测试导入 logging.py
    print("3.1 导入 src.shared.logging:")
    try:
        # 清除可能已导入的模块
        if 'src.shared.logging' in sys.modules:
            del sys.modules['src.shared.logging']
        
        spec = importlib.util.spec_from_file_location(
            "src.shared.logging", 
            os.path.join(os.getcwd(), "src", "shared", "logging.py")
        )
        logging_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(logging_module)
        
        print(f"    ✅ 导入成功")
        
        # 检查初始化
        print(f"\n3.2 检查 logging_config:")
        if hasattr(logging_module, 'logging_config'):
            print(f"    ✅ logging_config 存在")
            print(f"    log_dir: {logging_module.logging_config.log_dir}")
            print(f"    log_level: {logging_module.logging_config.log_level}")
        
        # 检查 logger 对象
        print(f"\n3.3 检查 logger:")
        if hasattr(logging_module, 'logger'):
            print(f"    ✅ logger 存在")
            
            # 测试写入日志
            test_msg = "项目日志模块测试消息"
            logging_module.logger.info(test_msg)
            print(f"    ✅ 已调用 logger.info: {test_msg}")
            
            # 再次检查日志文件
            current_log_file = os.path.join(
                logging_module.logging_config.log_dir, 
                f"agent_{datetime.datetime.now().strftime('%Y%m%d')}.log"
            )
            print(f"\n3.4 检查日志文件: {current_log_file}")
            if os.path.exists(current_log_file):
                size = os.path.getsize(current_log_file)
                print(f"    ✅ 文件大小: {size} bytes")
                if size > 0:
                    with open(current_log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"    内容:\n{content}")
                else:
                    print(f"    ⚠️  文件大小为 0！")
            else:
                print(f"    ❌ 文件不存在")
                
    except Exception as e:
        print(f"    ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # MECE 分类4：检查 main.py 的使用方式
    print("🚀 分类4：检查主程序")
    print("-" * 60)
    
    main_py = os.path.join(os.getcwd(), "src", "main.py")
    if os.path.exists(main_py):
        print(f"4.1 main.py 存在: {main_py}")
        
        # 读取 main.py 的内容（前50行）
        with open(main_py, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"4.2 main.py 前 50 行:")
        for i, line in enumerate(lines[:50], 1):
            print(f"    {i:3d}: {line.rstrip()}")
    
    print()
    print("=" * 80)
    print("✅ 诊断完成！")
    print("=" * 80)


if __name__ == "__main__":
    diagnose_logging()
