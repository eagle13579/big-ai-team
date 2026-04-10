#!/usr/bin/env python3
"""
验证新合入文件的位置是否正确，并评估适配状态
"""

import os
import re
import subprocess
from datetime import datetime

# 预期的目录结构
expected_dirs = [
    "src/access",
    "src/execution",
    "src/lib/core",
    "src/persistence",
    "src/shared",
    "src/skills",
    "src/workflow",
    "tests",
    "scripts",
]


# 检查最近从其他分支合入的文件
def get_newly_merged_files():
    """获取最近从其他分支合入的文件"""
    try:
        # 执行 git 命令获取最近的合并提交
        result = subprocess.run(
            ["git", "log", "--merges", "--name-only", "--oneline", "-n", "10"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )

        # 解析输出，提取文件路径
        merged_files = set()
        lines = result.stdout.strip().split("\n")

        # 跳过提交信息行，只获取文件路径
        capture_files = False
        for line in lines:
            if line and not line.startswith(" "):
                # 遇到新的提交信息，开始捕获文件
                capture_files = True
                continue
            elif capture_files and line.strip():
                # 捕获文件路径
                merged_files.add(line.strip())

        # 如果没有合并提交，获取最近的普通提交
        if not merged_files:
            result = subprocess.run(
                ["git", "log", "--name-only", "--oneline", "-n", "10"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            )

            lines = result.stdout.strip().split("\n")
            capture_files = False
            for line in lines:
                if line and not line.startswith(" "):
                    # 遇到新的提交信息，开始捕获文件
                    capture_files = True
                    continue
                elif capture_files and line.strip():
                    # 捕获文件路径
                    merged_files.add(line.strip())

        # 手动添加 adapters 目录，确保它被检查
        adapters_path = "src/access/adapters/__init__.py"
        if os.path.exists(adapters_path):
            merged_files.add(adapters_path)

        return merged_files
    except Exception as e:
        print(f"Error getting newly merged files: {e}")
        return set()


# 检查文件是否在预期的目录下
def check_file_location(file_path):
    """检查文件是否在预期的目录下"""
    for expected_dir in expected_dirs:
        if file_path.startswith(expected_dir):
            return True, expected_dir
    return False, None


# 评估文件的适配状态
def evaluate_adaptation_status(file_path):
    """评估文件的适配状态"""
    # 检查文件是否在预期的目录结构中
    is_valid, expected_dir = check_file_location(file_path)

    if not is_valid:
        return "❌ <span style='color:red'>未适配</span>"

    # 检查文件是否符合新的架构规范
    if "src/lib/core" in file_path:
        # 检查是否符合 source/index.py 规范
        if "source/index.py" in file_path:
            return "✅ 完全适配"
        elif "source/" in file_path:
            return "⚠️ 部分适配"
        else:
            return "❌ <span style='color:red'>未完全适配</span>"

    return "✅ 已适配"


# 生成验证报告
def generate_validation_report():
    """生成文件位置验证报告"""
    merged_files = get_newly_merged_files()

    report = []
    report.append("## 📁 文件位置验证报告")
    report.append("")
    report.append(f"### 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("### 检查结果")
    report.append("")
    report.append("| 文件路径 | 位置状态 | 适配状态 | 预期目录 |")
    report.append("| :--- | :--- | :--- | :--- |")

    if not merged_files:
        report.append("| - | - | - | - |")
        report.append("")
        report.append("### 说明")
        report.append("- 最近没有新的合入记录")
        report.append("- 或者没有检测到新增或修改的文件")
    else:
        for file_path in merged_files:
            # 跳过目录和非代码文件
            if os.path.isdir(file_path) or not file_path.endswith((".py", ".ts", ".js")):
                continue

            is_valid, expected_dir = check_file_location(file_path)
            if is_valid:
                location_status = "✅ 正确"
            else:
                location_status = "❌ <span style='color:red'>错误</span>"

            adaptation_status = evaluate_adaptation_status(file_path)

            report.append(
                f"| `{file_path}` | {location_status} | {adaptation_status} | {expected_dir or '不在预期目录中'} |"
            )

    return "\n".join(report)


# 更新 module_validation_report.md
def update_module_validation_report():
    """更新模块验证报告"""
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "memory",
        "module_validation_report.md",
    )

    if not os.path.exists(report_path):
        print(f"Error: {report_path} does not exist")
        return

    # 读取现有报告
    with open(report_path, encoding="utf-8") as f:
        content = f.read()

    # 生成新的验证报告
    validation_report = generate_validation_report()

    # 检查是否已存在文件位置验证报告部分
    if "## 📁 文件位置验证报告" in content:
        # 替换现有部分
        updated_content = re.sub(
            r"## 📁 文件位置验证报告.*?(?=## |$)", validation_report, content, flags=re.DOTALL
        )
    else:
        # 在最后添加新部分，确保格式正确
        updated_content = content.rstrip() + "\n\n" + validation_report + "\n"

    # 写回文件
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Updated {report_path} with file location validation report")


if __name__ == "__main__":
    update_module_validation_report()
