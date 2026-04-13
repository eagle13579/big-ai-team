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
    """生成验证报告（支持增量更新）"""
    report = validate_file_locations()
    report_file = os.path.join("memory", "module_validation_report.md")
    
    # 生成新的报告内容
    markdown_content = """# 模块验证报告

"""
    
    # 保留历史记录（如果存在）
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
        
        # 提取历史记录（所有在核心模块状态概览之前的内容）
        if "## 核心模块状态概览" in existing_content:
            history_section = existing_content.split("## 核心模块状态概览")[0]
            # 只保留最近的几个历史记录，避免报告过长
            # 按日期分割历史记录
            history_entries = history_section.strip().split("## [")
            # 保留最新的3个历史记录
            if len(history_entries) > 4:
                recent_history = "## ".join(history_entries[:4])
            else:
                recent_history = history_section.strip()
            markdown_content += recent_history + "\n\n"
    
    # 生成新的核心模块状态概览
    module_status_content = """
## 核心模块状态概览

| 模块名 | 物理路径 | 当前验证状态 | 最后更新时间 | 核心逻辑摘要 |
|-------|---------|------------|------------|------------|
"""
    
    # 添加核心模块状态
    for validation in report["validations"]:
        module_name = validation["module"].capitalize()
        # 格式化路径，使用正斜杠
        formatted_path = validation["path"].replace("\\", "/")
        module_status_content += f"| {module_name} | {formatted_path} | ✅ 已验证 | {datetime.now().strftime('%Y-%m-%d')} | (待填充) |\n"

    for error in report["errors"]:
        module_name = error["module"].capitalize()
        # 格式化路径，使用正斜杠
        formatted_path = error["path"].replace("\\", "/")
        module_status_content += f"| {module_name} | {formatted_path} | ❌ 缺失 | {datetime.now().strftime('%Y-%m-%d')} | (待填充) |\n"

    # 生成新的改动日志条目
    new_log_entry = f"""
## 详细改动日志

### [{datetime.now().strftime('%Y-%m-%d')}] 自动验证报告更新
- **改动范围：** 自动验证文件位置和目录结构。
- **核心逻辑：** 检查核心模块的 source/index.py 文件是否存在，验证脚本目录和报告文件位置。
- **影响评估：** 确保项目目录结构符合架构规范。
- **验证结果：** 通过 {len(report['validations'])} 项，失败 {len(report['errors'])} 项。
"""
    
    # 构建完整的报告内容
    markdown_content += module_status_content
    markdown_content += new_log_entry

    # 写入报告文件
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
