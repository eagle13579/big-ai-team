#!/usr/bin/env python3
"""
自动化变更跟踪系统 - 实时监控代码变更并更新模块验证报告
"""

import os
import time
import datetime
import subprocess
import json
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
# 模块验证报告路径
REPORT_PATH = os.path.join(PROJECT_ROOT, 'memory', 'module_validation_report.md')
# 监控目录
MONITOR_DIRS = [
    PROJECT_ROOT  # 监控整个项目根目录
]
# 忽略的文件和目录
IGNORE_PATTERNS = [
    '__pycache__',
    '.git',
    '*.pyc',
    '*.pyo',
    '.DS_Store',
    'Thumbs.db'
]

class ChangeTracker:
    """变更跟踪器"""
    
    def __init__(self):
        self.changes = {
            'modified': [],
            'created': [],
            'deleted': []
        }
        self.lock = threading.Lock()
        self.last_update = time.time()
    
    def add_change(self, change_type, path):
        """添加变更记录"""
        with self.lock:
            relative_path = os.path.relpath(path, PROJECT_ROOT)
            if relative_path not in self.changes[change_type]:
                self.changes[change_type].append(relative_path)
            self.last_update = time.time()
    
    def get_changes(self):
        """获取变更记录"""
        with self.lock:
            return self.changes.copy()
    
    def clear_changes(self):
        """清空变更记录"""
        with self.lock:
            self.changes = {
                'modified': [],
                'created': [],
                'deleted': []
            }

class ChangeHandler(FileSystemEventHandler):
    """文件系统变更处理器"""
    
    def __init__(self, tracker):
        self.tracker = tracker
    
    def on_modified(self, event):
        """处理文件修改"""
        if not event.is_directory and self._should_process(event.src_path):
            self.tracker.add_change('modified', event.src_path)
    
    def on_created(self, event):
        """处理文件创建"""
        if not event.is_directory and self._should_process(event.src_path):
            self.tracker.add_change('created', event.src_path)
    
    def on_deleted(self, event):
        """处理文件删除"""
        if not event.is_directory and self._should_process(event.src_path):
            self.tracker.add_change('deleted', event.src_path)
    
    def _should_process(self, path):
        """判断是否应该处理该文件"""
        relative_path = os.path.relpath(path, PROJECT_ROOT)
        for pattern in IGNORE_PATTERNS:
            if pattern in relative_path:
                return False
        return True

class ReportUpdater:
    """报告更新器"""
    
    @staticmethod
    def update_report(changes):
        """更新模块验证报告"""
        if not any(changes.values()):
            return
        
        today = datetime.date.today().isoformat()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 生成变更摘要
        summary = []
        if changes['created']:
            summary.append(f"- **新增文件**: {', '.join(changes['created'])}")
        if changes['modified']:
            summary.append(f"- **修改文件**: {', '.join(changes['modified'])}")
        if changes['deleted']:
            summary.append(f"- **删除文件**: {', '.join(changes['deleted'])}")
        
        # 读取当前报告
        with open(REPORT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成新的变更记录
        change_entry = f"""
### [{today}] 代码变更自动记录
- **改动范围：** 自动监控到的代码变更。
- **核心逻辑：** 
{chr(10).join(summary)}
- **影响评估：** 代码变更可能影响系统功能。
- **验证结果：** 待验证。
- **记录时间：** {timestamp}
"""
        
        # 插入到详细改动日志部分
        if '## 详细改动日志' in content:
            content = content.replace(
                '## 详细改动日志',
                f'## 详细改动日志{change_entry}'
            )
        
        # 更新验证报告的最后更新时间
        content = content.replace(
            'Validation_report | memory/module_validation_report.md | ✅ 已验证 | 2026-04-14',
            f'Validation_report | memory/module_validation_report.md | ✅ 已验证 | {today}'
        )
        
        # 写入更新后的报告
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[INFO] 模块验证报告已更新 ({timestamp})")

class GitHookHandler:
    """Git Hook处理器"""
    
    @staticmethod
    def handle_commit():
        """处理Git提交"""
        # 获取提交信息
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=format:%B'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        commit_message = result.stdout.strip()
        
        # 获取变更文件
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        if changed_files:
            changes = {
                'modified': changed_files,
                'created': [],
                'deleted': []
            }
            ReportUpdater.update_report(changes)
            print(f"[INFO] Git提交变更已记录到验证报告")

def start_monitoring():
    """启动监控"""
    tracker = ChangeTracker()
    event_handler = ChangeHandler(tracker)
    
    observer = Observer()
    for directory in MONITOR_DIRS:
        if os.path.exists(directory):
            observer.schedule(event_handler, directory, recursive=True)
    
    observer.start()
    print(f"[INFO] 开始监控代码变更...")
    
    try:
        while True:
            time.sleep(60)  # 每分钟检查一次
            changes = tracker.get_changes()
            if any(changes.values()):
                ReportUpdater.update_report(changes)
                tracker.clear_changes()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自动化变更跟踪系统')
    parser.add_argument('--git-hook', action='store_true', help='作为Git Hook运行')
    parser.add_argument('--daemon', action='store_true', help='以守护进程方式运行')
    
    args = parser.parse_args()
    
    if args.git_hook:
        GitHookHandler.handle_commit()
    elif args.daemon:
        start_monitoring()
    else:
        # 手动触发更新
        tracker = ChangeTracker()
        # 这里可以添加手动扫描逻辑
        ReportUpdater.update_report(tracker.get_changes())

if __name__ == '__main__':
    main()