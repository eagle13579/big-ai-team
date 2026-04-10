import logging
import os
from datetime import datetime


def test_logging_system():
    """
    测试日志系统是否正常工作
    """
    print("=" * 60)
    print("📋 测试日志系统")
    print("=" * 60)
    print()

    # 1. 检查日志目录是否存在
    LOG_DIR = "logs"
    print("1. 检查日志目录...")
    if os.path.exists(LOG_DIR):
        print(f"✅ 日志目录已创建: {LOG_DIR}")
    else:
        print("⚠️  日志目录不存在，创建中...")
        os.makedirs(LOG_DIR, exist_ok=True)
        print(f"✅ 日志目录已创建: {LOG_DIR}")
    print()

    # 2. 配置日志
    print("2. 配置日志...")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                os.path.join(LOG_DIR, f"agent_{datetime.now().strftime('%Y%m%d')}.log"),
                encoding="utf-8",  # 指定 UTF-8 编码，解决中文乱码问题
            ),
        ],
    )
    print("✅ 日志配置完成")
    print()

    # 3. 测试日志写入
    print("3. 测试日志写入...")
    test_logger = logging.getLogger("TestLogger")
    test_logger.info("这是一条测试信息日志")
    test_logger.warning("这是一条测试警告日志")
    test_logger.error("这是一条测试错误日志")
    print("✅ 日志写入测试完成")
    print()

    # 4. 检查日志文件
    print("4. 检查日志文件...")
    log_files = [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
    if log_files:
        print(f"✅ 找到 {len(log_files)} 个日志文件:")
        for log_file in log_files:
            file_path = os.path.join(LOG_DIR, log_file)
            file_size = os.path.getsize(file_path)
            print(f"   - {log_file} ({file_size} bytes)")

            # 查看日志文件内容
            print("   最近的日志内容:")
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                for line in lines[-5:]:  # 显示最后5行
                    print(f"     {line.rstrip()}")
    else:
        print("❌ 没有日志文件")
    print()

    print("=" * 60)
    print("✅ 日志系统测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_logging_system()
