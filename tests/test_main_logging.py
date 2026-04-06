import os
import logging
from datetime import datetime

def test_main_logging():
    """
    测试主程序的日志系统
    """
    print("=" * 60)
    print("📋 测试主程序日志系统")
    print("=" * 60)
    print()
    
    # 1. 检查日志目录
    LOG_DIR = "logs"
    print("1. 检查日志目录...")
    if os.path.exists(LOG_DIR):
        print(f"✅ 日志目录已存在: {LOG_DIR}")
    else:
        print(f"❌ 日志目录不存在: {LOG_DIR}")
        return
    print()
    
    # 2. 检查当前日志文件
    log_file = os.path.join(LOG_DIR, f"agent_{datetime.now().strftime('%Y%m%d')}.log")
    print("2. 检查当前日志文件...")
    if os.path.exists(log_file):
        print(f"✅ 日志文件已存在: {log_file}")
        file_size = os.path.getsize(log_file)
        print(f"   文件大小: {file_size} bytes")
    else:
        print(f"❌ 日志文件不存在: {log_file}")
        return
    print()
    
    # 3. 查看日志内容
    print("3. 查看日志内容...")
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            print(f"✅ 日志文件包含 {len(lines)} 行")
            print("   最近的 10 行日志:")
            for line in lines[-10:]:
                print(f"     {line.rstrip()}")
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")
    print()
    
    # 4. 测试直接运行主程序
    print("4. 测试运行主程序...")
    try:
        import subprocess
        result = subprocess.run(
            ["python", "src/main.py", "测试日志系统"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"✅ 主程序运行完成，退出码: {result.returncode}")
        print("   标准输出:")
        print(result.stdout)
        if result.stderr:
            print("   标准错误:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 运行主程序失败: {e}")
    print()
    
    # 5. 再次检查日志文件
    print("5. 再次检查日志文件...")
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        print(f"✅ 日志文件大小: {file_size} bytes")
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            print(f"   日志文件包含 {len(lines)} 行")
            print("   最近的 5 行日志:")
            for line in lines[-5:]:
                print(f"     {line.rstrip()}")
    else:
        print(f"❌ 日志文件不存在: {log_file}")
    print()
    
    print("=" * 60)
    print("✅ 主程序日志系统测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_main_logging()
