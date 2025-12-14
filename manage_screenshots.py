#!/usr/bin/env python3
"""
截图管理工具 - 管理Web界面的截图文件
"""
import os
import shutil
import glob
from datetime import datetime, timedelta
from pathlib import Path

class ScreenshotManager:
    def __init__(self):
        self.screenshots_dir = Path("web/static/screenshots")
        self.archive_dir = Path("web/static/screenshots_archive")

    def list_screenshots(self, limit=20):
        """列出最近的截图文件"""
        if not self.screenshots_dir.exists():
            print("❌ 截图目录不存在")
            return

        files = list(self.screenshots_dir.glob("screenshot_*.png"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        print(f"📸 最近 {min(limit, len(files))} 个截图:")
        print("-" * 80)
        for i, file in enumerate(files[:limit]):
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            size = file.stat().st_size / 1024  # KB
            print(f"{i+1:2d}. {file.name:40s} {mtime.strftime('%Y-%m-%d %H:%M:%S')}  {size:8.1f} KB")

        if len(files) > limit:
            print(f"... 还有 {len(files) - limit} 个文件")

        total_size = sum(f.stat().st_size for f in files) / 1024 / 1024  # MB
        print(f"\n📊 总计: {len(files)} 个文件, {total_size:.1f} MB")

    def archive_by_date(self):
        """按日期归档截图"""
        if not self.screenshots_dir.exists():
            print("❌ 截图目录不存在")
            return

        files = list(self.screenshots_dir.glob("screenshot_*.png"))
        if not files:
            print("❌ 没有找到截图文件")
            return

        # 按日期分组
        date_groups = {}
        for file in files:
            # 从文件名提取日期 (格式: screenshot_YYYYMMDD_...)
            parts = file.name.split('_')
            if len(parts) >= 2:
                date_str = parts[1]
                if date_str.isdigit() and len(date_str) == 8:
                    date_groups[date_str] = date_groups.get(date_str, [])
                    date_groups[date_str].append(file)

        # 创建归档目录并移动文件
        archived_count = 0
        for date_str, date_files in date_groups.items():
            date_dir = self.archive_dir / date_str
            date_dir.mkdir(parents=True, exist_ok=True)

            for file in date_files:
                dest = date_dir / file.name
                shutil.move(str(file), str(dest))
                archived_count += 1

        print(f"✅ 已归档 {archived_count} 个截图文件到 {self.archive_dir}")

    def cleanup_old_screenshots(self, days=7):
        """清理超过指定天数的旧截图"""
        if not self.screenshots_dir.exists():
            print("❌ 截图目录不存在")
            return

        cutoff_time = datetime.now() - timedelta(days=days)
        files = list(self.screenshots_dir.glob("screenshot_*.png"))

        deleted_count = 0
        deleted_size = 0

        for file in files:
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime < cutoff_time:
                size = file.stat().st_size
                file.unlink()
                deleted_count += 1
                deleted_size += size

        if deleted_count > 0:
            print(f"✅ 已删除 {deleted_count} 个旧截图文件, 释放 {deleted_size/1024/1024:.1f} MB 空间")
        else:
            print("✅ 没有需要清理的旧截图")

    def create_task_archive(self, task_name):
        """为特定任务创建截图归档"""
        if not self.screenshots_dir.exists():
            print("❌ 截图目录不存在")
            return

        # 获取最新截图
        files = list(self.screenshots_dir.glob("screenshot_*.png"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if not files:
            print("❌ 没有找到截图文件")
            return

        # 创建任务归档目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_dir = Path("screenshots_archive") / f"{task_name}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)

        # 复制最新截图到任务目录
        copied_count = 0
        for file in files[:50]:  # 最多复制50个最新截图
            dest = task_dir / file.name
            shutil.copy2(str(file), str(dest))
            copied_count += 1

        print(f"✅ 已为任务 '{task_name}' 创建截图归档: {copied_count} 个文件")
        print(f"📁 归档位置: {task_dir}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='截图管理工具')
    parser.add_argument('action', choices=['list', 'archive', 'cleanup', 'task'],
                       help='操作类型')
    parser.add_argument('--limit', type=int, default=20,
                       help='列出文件时的限制数量')
    parser.add_argument('--days', type=int, default=7,
                       help='清理多少天前的文件')
    parser.add_argument('--task-name', type=str, default='task',
                       help='任务名称')

    args = parser.parse_args()

    manager = ScreenshotManager()

    if args.action == 'list':
        manager.list_screenshots(args.limit)
    elif args.action == 'archive':
        manager.archive_by_date()
    elif args.action == 'cleanup':
        manager.cleanup_old_screenshots(args.days)
    elif args.action == 'task':
        manager.create_task_archive(args.task_name)

if __name__ == "__main__":
    main()