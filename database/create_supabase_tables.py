#!/usr/bin/env python3
"""
Supabase 数据库初始化脚本
用于创建 tasks 表和索引
"""

import os
import sys
from supabase import create_client

# 设置环境变量
SUPABASE_URL = "https://obkstdzogheljzmxtfvh.supabase.co"
SUPABASE_KEY = "sb_publishable_aTUvZmIbjn12UiLGSOMsoA_pDeiiKB9"

def create_tables():
    """创建 tasks 表和索引"""
    try:
        # 连接到 Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ 成功连接到 Supabase")

        # 创建表的 SQL
        create_table_sql = """
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
        """

        print("\n=== 请在 Supabase Dashboard 的 SQL 编辑器中执行以下 SQL ===")
        print(create_table_sql)

        # 创建索引的 SQL
        create_indexes_sql = """
        -- 创建索引以提高查询性能
        CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON tasks(session_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
        CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
        """

        print(create_indexes_sql)
        print("\n=== SQL 执行完成后，按回车继续测试 ===")
        input()

        # 测试表是否创建成功
        print("\n=== 测试表访问 ===")
        try:
            result = supabase.table('tasks').select('id').limit(1).execute()
            if result.data is not None:
                print("✅ tasks 表创建成功，可以正常访问")
                return True
            else:
                print("❌ tasks 表创建失败或无法访问")
                return False
        except Exception as e:
            print(f"❌ 表访问测试失败: {e}")
            return False

    except Exception as e:
        print(f"❌ 连接 Supabase 失败: {e}")
        return False

def test_task_operations():
    """测试任务操作"""
    try:
        import sys
        sys.path.append('web')
        from supabase_manager import SupabaseTaskManager
        from datetime import datetime
        import uuid

        manager = SupabaseTaskManager()
        print("✅ SupabaseTaskManager 初始化成功")

        # 测试创建任务
        test_task_id = str(uuid.uuid4())
        task = manager.create_task(
            task_id=test_task_id,
            session_id='test_session',
            user_id='test_user',
            task_description='测试 Supabase 集成',
            config={'test': True}
        )
        print(f"✅ 测试任务创建成功: {test_task_id}")

        # 测试获取任务
        retrieved_task = manager.get_task(test_task_id)
        if retrieved_task:
            print(f"✅ 任务检索成功: {retrieved_task.task_description}")
        else:
            print("❌ 任务检索失败")

        # 测试获取所有任务
        all_tasks = manager.get_all_tasks()
        print(f"✅ 当前任务总数: {len(all_tasks)}")

        # 清理测试任务
        if manager.delete_task(test_task_id):
            print(f"✅ 测试任务删除成功: {test_task_id}")
        else:
            print(f"❌ 测试任务删除失败: {test_task_id}")

        return True

    except Exception as e:
        print(f"❌ 任务操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=== Supabase 数据库初始化脚本 ===\n")

    # 步骤 1: 创建表
    print("步骤 1: 创建数据库表")
    if not create_tables():
        print("❌ 数据库表创建失败，脚本终止")
        return

    # 步骤 2: 测试任务操作
    print("\n步骤 2: 测试任务操作")
    if test_task_operations():
        print("\n🎉 Supabase 数据库初始化完成！")
        print("现在可以启动 web 服务，任务将持久化存储到 Supabase 数据库")
    else:
        print("\n❌ 任务操作测试失败，请检查配置")

if __name__ == "__main__":
    main()