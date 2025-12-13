#!/usr/bin/env python3
"""
Supabase 数据库设置脚本
提供创建表的 SQL 和测试连接
"""

import os
from supabase import create_client

# Supabase 配置
SUPABASE_URL = "https://obkstdzogheljzmxtfvh.supabase.co"
SUPABASE_KEY = "sb_publishable_aTUvZmIbjn12UiLGSOMsoA_pDeiiKB9"

def main():
    print("=== Supabase 数据库设置指南 ===\n")

    print("1. 请访问 Supabase Dashboard: https://app.supabase.com")
    print("2. 选择您的项目: obkstdzogheljzmxtfvh")
    print("3. 进入 SQL 编辑器")
    print("4. 执行以下 SQL 代码:\n")

    sql_code = """
-- 创建 tasks 表
CREATE TABLE IF NOT EXISTS tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id TEXT NOT NULL UNIQUE,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    task_description TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_activity TIMESTAMPTZ NOT NULL,
    config JSONB NOT NULL,
    thread_id TEXT,
    error_message TEXT,
    end_time TIMESTAMPTZ,
    result TEXT
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
"""

    print(sql_code)

    print("\n" + "="*60)
    print("执行完 SQL 后，运行以下命令测试连接:")
    print("python3 test_supabase_connection.py")
    print("="*60)

    # 立即测试连接
    print("\n=== 测试当前连接状态 ===")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        result = supabase.table('tasks').select('id').limit(1).execute()
        print("✅ tasks 表已存在且可访问")

        # 测试任务管理器
        import sys
        sys.path.append('web')
        from supabase_manager import SupabaseTaskManager

        manager = SupabaseTaskManager()
        tasks = manager.get_all_tasks()
        print(f"✅ 当前数据库中有 {len(tasks)} 个任务")

    except Exception as e:
        if "Could not find the table" in str(e):
            print("❌ tasks 表尚未创建，请先执行上述 SQL")
        else:
            print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    main()