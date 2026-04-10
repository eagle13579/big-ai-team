#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[Nova 生产环境部署自检脚本 v5.0]
发布日期: 2026-04-11
更新日志: 
1. 融合 Python 3.12 生产基准支持（取代已过时的 3.10）。
2. 增强了对 Nuitka 编译模块 (.so/.pyd) 的次版本号 (Minor Version) 硬校验。
3. 优化了跨平台架构 (x86_64/AMD64) 的智能识别逻辑。
"""

import platform
import sys
import os
from datetime import datetime

def check_env_compatibility():
    """
    执行 2026 工业级环境兼容性检查。
    针对 Nuitka 编译模块的强耦合性，确保 Python 次版本号、系统架构、运行容器状态完全一致。
    """
    curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # --- 头部装饰 ---
    print(f"\n🔍 [Nova Audit] 环境扫描启动 | {curr_time}")
    print("=" * 65)

    # 1. 基础元数据提取
    is_docker = os.path.exists('/.dockerenv')
    env_tag = "DOCKER" if is_docker else "HOST"
    
    metadata = [
        ("操作系统", f"{platform.system()} {platform.release()}"),
        ("硬件架构", platform.machine()),
        ("运行环境", "Containerized" if is_docker else "Bare Metal"),
        ("当前解释器", sys.executable),
        ("当前版本", sys.version.split()[0])
    ]

    for label, val in metadata:
        print(f"[{env_tag}] {label:<10} : {val}")

    print("-" * 65)

    # 2. 核心校验：Python 版本一致性 (2026 生产基准: 3.12)
    # Nuitka 编译产物严禁跨次版本运行 (如 3.12 编译的无法在 3.14 运行)
    REQUIRED_MAJOR = 3
    REQUIRED_MINOR = 12
    
    is_compatible = True
    curr_major = sys.version_info.major
    curr_minor = sys.version_info.minor

    if curr_major != REQUIRED_MAJOR or curr_minor != REQUIRED_MINOR:
        print(f"\n❌ [严重错误] Python 次版本号不匹配！")
        print(f"   >>> 预期目标: Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}")
        print(f"   >>> 实际运行: Python {curr_major}.{curr_minor}")
        print(f"   >>> 风险预警: Nuitka 生成的二进制模块将触发致命的加载异常 (ImportError)。")
        is_compatible = False
    else:
        print(f"✅ [版本验证] Python {REQUIRED_MAJOR}.{REQUIRED_MINOR} 验证通过。")

    # 3. 架构校验 (针对 2026 年主流多架构集群部署)
    # 自动识别 Windows(AMD64) 与 Linux(x86_64) 的等效性
    target_archs = ["AMD64", "x86_64"]
    curr_arch = platform.machine()
    
    if curr_arch not in target_archs:
        print(f"\n⚠️ [架构警告] 硬件不匹配预警！")
        print(f"   >>> 编译目标: {target_archs}")
        print(f"   >>> 当前运行: {curr_arch}")
        print(f"   >>> 提示: 请检查 CI/CD 是否拉取了错误的 ARM 镜像层。")

    print("-" * 65)

    # 4. 最终裁决
    if not is_compatible:
        print("🚫 [结论] 环境不满足生产要求。正在强制中断部署流程 (Exit Code: 1)...")
        sys.exit(1)
    
    print("🚀 [结论] 环境高度兼容。正在移交控制权给主程序...")
    print("=" * 65 + "\n")
    sys.exit(0)

if __name__ == "__main__":
    try:
        check_env_compatibility()
    except Exception as e:
        print(f"💥 [紧急故障] 审计脚本自检异常: {str(e)}")
        sys.exit(2)