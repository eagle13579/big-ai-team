import os
from datetime import datetime


def validate_file_locations():
    """验证文件位置并生成报告"""
    report = {"timestamp": datetime.now().isoformat(), "validations": [], "errors": []}

    # 检查核心模块目录结构
    core_modules = ["dispatcher", "factory", "planner", "state", "memory"]
    for module in core_modules:
        module_path = os.path.join("src", "lib", "core", module, "source", "index.py")
        if os.path.exists(module_path):
            report["validations"].append(
                {"module": module, "path": module_path, "status": "✅ 已验证"}
            )
        else:
            report["errors"].append({"module": module, "path": module_path, "status": "❌ 缺失"})

    # 检查脚本文件位置
    scripts_dir = os.path.join("scripts")
    if os.path.exists(scripts_dir):
        report["validations"].append(
            {"module": "scripts", "path": scripts_dir, "status": "✅ 已验证"}
        )
    else:
        report["errors"].append({"module": "scripts", "path": scripts_dir, "status": "❌ 缺失"})

    # 检查验证报告文件
    report_file = os.path.join("memory", "module_validation_report.md")
    if os.path.exists(report_file):
        report["validations"].append(
            {"module": "validation_report", "path": report_file, "status": "✅ 已验证"}
        )
    else:
        report["errors"].append(
            {"module": "validation_report", "path": report_file, "status": "❌ 缺失"}
        )

    return report


def generate_validation_report():
    """生成验证报告"""
    report = validate_file_locations()

    # 生成Markdown报告
    markdown_content = """# 🚀 模块验证与逻辑沉淀报告 (Module Validation Report)
> [!important]
> 本文档是项目的"逻辑真理来源"，记录核心算法、架构变动及验证状态。每次 Feature 完成后需同步更新。

---

## 🏗️ 核心模块状态概览
| 模块名 | 当前路径 | 验证状态 | 最后更新时间 | 核心逻辑摘要 |
| :--- | :--- | :--- | :--- | :--- |
"""

    # 添加核心模块状态
    for validation in report["validations"]:
        module_name = validation["module"].capitalize()
        markdown_content += f"| **{module_name}** | `{validation['path']}` | ✅ 已验证 | {datetime.now().strftime('%Y-%m-%d')} | (待填充) |\n"

    for error in report["errors"]:
        module_name = error["module"].capitalize()
        markdown_content += f"| **{module_name}** | `{error['path']}` | ❌ 缺失 | {datetime.now().strftime('%Y-%m-%d')} | (待填充) |\n"

    # 添加详细改动日志
    markdown_content += """
---

## 📝 详细改动日志 (Feature Log)
### [{}] 自动验证报告生成
- **改动范围：** 自动验证文件位置和目录结构。
- **核心逻辑：** 检查核心模块的 source/index.py 文件是否存在，验证脚本目录和报告文件位置。
- **影响评估：** 确保项目目录结构符合架构规范。

""".format(datetime.now().strftime("%Y-%m-%d"))

    # 写入报告文件
    report_file = os.path.join("memory", "module_validation_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return report


if __name__ == "__main__":
    result = generate_validation_report()
    print("验证报告已生成！")
    print(f"验证通过: {len(result['validations'])}")
    print(f"验证失败: {len(result['errors'])}")
    if result["errors"]:
        print("失败项:")
        for error in result["errors"]:
            print(f"- {error['module']}: {error['path']}")
