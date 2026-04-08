import os
import logging
from datetime import datetime

# 直接测试日志系统，不依赖其他模块

def test_direct_logging():
    """
    直接测试日志系统，不依赖其他模块
    """
    print("=" * 60)
    print("📋 直接测试日志系统")
    print("=" * 60)
    print()
    
    # 1. 创建日志目录
    LOG_DIR = "logs"
    print("1. 创建日志目录...")
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"✅ 日志目录已创建: {LOG_DIR}")
    print()
    
    # 2. 配置日志
    print("2. 配置日志...")
    log_file = os.path.join(LOG_DIR, f"agent_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 配置日志系统
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    print(f"✅ 日志配置完成，日志文件: {log_file}")
    print()
    
    # 3. 测试日志写入
    print("3. 测试日志写入...")
    logger = logging.getLogger("TestDirectLogger")
    
    # 写入不同级别的日志
    logger.info("这是一条测试信息日志 - 直接测试")
    logger.warning("这是一条测试警告日志 - 直接测试")
    logger.error("这是一条测试错误日志 - 直接测试")
    
    print("✅ 日志写入完成")
    print()
    
    # 4. 检查日志文件
    print("4. 检查日志文件...")
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        print(f"✅ 日志文件大小: {file_size} bytes")
        
        # 读取日志文件内容
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            print(f"   日志文件包含 {len(lines)} 行")
            print("   最近的 10 行日志:")
            for line in lines[-10:]:
                print(f"     {line.rstrip()}")
    else:
        print(f"❌ 日志文件不存在: {log_file}")
    print()
    
    # 5. 测试多次写入
    print("5. 测试多次写入...")
    for i in range(3):
        logger.info(f"这是第 {i+1} 次测试日志 - 时间戳: {datetime.now().isoformat()}")
    
    # 再次检查日志文件
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        print(f"✅ 日志文件大小: {file_size} bytes")
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            print(f"   日志文件包含 {len(lines)} 行")
            print("   最近的 5 行日志:")
            for line in lines[-5:]:
                print(f"     {line.rstrip()}")
    print()
    
    print("=" * 60)
    print("✅ 直接日志系统测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_direct_logging()
