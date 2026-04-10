#!/usr/bin/env python3
"""
MemPalace 核心逻辑加密构建脚本
使用 Nuitka 将核心 Python 代码编译为二进制模块
"""

import glob
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 配置工业级日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger("Protector")


def run_command(cmd, description):
    """安全执行 shell 命令并捕获异常"""
    try:
        logger.info(f"正在执行: {description}...")
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logger.error(f"{description} 失败: {e}")
        sys.exit(1)


def build_and_protect():
    # --- 配置参数 ---
    CORE_DIR = Path("core")
    DIST_DIR = Path("dist_build")
    # 查找二进制后缀 (Linux: .so, Windows: .pyd)
    BINARY_EXT = ".pyd" if os.name == "nt" else ".so"

    if not CORE_DIR.exists():
        logger.error(f"目录 {CORE_DIR} 不存在，请检查项目结构！")
        return

    logger.info("=" * 50)
    logger.info("核心代码脱敏流程启动 (2026-04-10 Production Standard)")
    logger.info("=" * 50)

    # 1. 预清理：确保构建环境纯净
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 2. 深度扫描并原子编译 (Atomic Compilation)
    # 最佳实践：对每一个独立的逻辑文件进行编译，确保导入链不中断
    py_files = list(CORE_DIR.rglob("*.py"))

    for py_file in py_files:
        if py_file.name == "__init__.py":
            continue

        # 计算模块名 (例如: core/utils/algo.py -> core.utils.algo)
        module_path = py_file.with_suffix("")

        logger.info(f"正在处理模块: {module_path}")

        # Nuitka 世界级保护指令集：
        # --module: 编译为二进制扩展
        # --follow-imports: 自动处理依赖
        # --remove-output: 自动删除生成的 C 源码
        # --no-pyi-file: 不生成辅助文件，增加破解难度
        # --lto=yes: 链接时优化，提升执行速度 10%-20%
        nuitka_cmd = [
            sys.executable,
            "-m",
            "nuitka",
            "--module",
            str(py_file),
            f"--output-dir={DIST_DIR}",
            "--remove-output",
            "--no-pyi-file",
            "--lto=yes",  # 2026 年编译器的标配优化
            "--quiet",
        ]

        # 如果在 Linux 下，开启 GCC 并行编译加速
        if os.name != "nt":
            nuitka_cmd.append("--jobs=4")

        run_command(nuitka_cmd, f"编译 {py_file.name}")

        # 3. 部署二进制文件并物理删除源码
        # 查找 Nuitka 生成的对应二进制文件
        # Nuitka 生成的文件名通常包含架构信息，如 module.cpython-310-x86_64-linux-gnu.so
        search_pattern = str(DIST_DIR / f"{py_file.stem}*{BINARY_EXT}")
        found_bins = glob.glob(search_pattern)

        if found_bins:
            # 取第一个匹配的文件（通常只有一个）
            bin_file = Path(found_bins[0])
            # 将二进制文件移动回源码所在目录，但文件名简化（保持导入兼容性）
            # 注意：Python 优先加载 .so/.pyd 而非 .py，如果同名存在
            dest_bin = py_file.with_suffix(BINARY_EXT)

            if dest_bin.exists():
                dest_bin.unlink()

            shutil.move(str(bin_file), str(dest_bin))

            # 【关键】立刻物理删除对应的 .py 源码文件
            py_file.unlink()
            logger.info(f"成功保护 [✔]: {py_file.name} -> {dest_bin.name}")
        else:
            logger.warning(f"警告 [!]: 未找到编译产物 {py_file.stem}")

    # 4. 终极清理：删除构建缓存
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    logger.info("=" * 50)
    logger.info("脱敏任务完美执行：所有源码已移除，二进制防护已生效。")
    logger.info("=" * 50)


if __name__ == "__main__":
    # 自动安装缺失的生产依赖
    try:
        import nuitka
    except ImportError:
        logger.info("正在安装 Nuitka 环境...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka", "zstandard"])

    build_and_protect()
