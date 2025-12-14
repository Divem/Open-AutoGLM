#!/usr/bin/env python3
"""
修复数据库表结构
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ 已加载 .env 文件")
except ImportError:
    print("⚠️ python-dotenv 未安装")

from supabase import create_client, Client

def connect_to_supabase() -> Client:
    """连接到 Supabase"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SECRET_KEY')

    if not url or not key:
        raise ValueError("缺少 SUPABASE_URL 或 SUPABASE_SECRET_KEY")

    print(f"连接到: {url[:30]}...")
    print(f"使用密钥: {'service_role' if 'secret' in key.lower() else 'other'}")

    client = create_client(url, key)
    return client

def check_table_structure(client: Client, table_name: str):
    """检查表结构"""
    try:
        # 查询 information_schema
        response = client.rpc(
            'get_table_structure',
            {'table_name': table_name}
        ).execute()

        if response.data:
            print(f"\n表 {table_name} 结构:")
            for col in response.data:
                print(f"  - {col['column_name']}: {col['data_type']}")
        else:
            print(f"\n❌ 表 {table_name} 不存在或无法访问")
    except Exception as e:
        print(f"\n⚠️ 无法检查表 {table_name} 结构: {e}")
        # 尝试简单的 SELECT
        try:
            response = client.table(table_name).select('*').limit(1).execute()
            if response.data:
                print(f"\n表 {table_name} 存在，列: {list(response.data[0].keys())}")
            else:
                print(f"\n表 {table_name} 为空")
        except Exception as e2:
            print(f"\n❌ 表 {table_name} 访问失败: {e2}")

def add_missing_columns(client: Client):
    """添加缺失的列"""
    print("\n开始修复表结构...")

    # 检查 task_steps 表
    print("\n1. 检查 task_steps 表...")
    check_table_structure(client, 'task_steps')

    # 添加 step_id 列（如果不存在）
    try:
        print("\n2. 尝试添加 step_id 列到 task_steps...")
        # 使用原始 SQL，因为 supabase-py 可能不支持 ALTER TABLE
        sql = """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'task_steps'
                AND column_name = 'step_id'
            ) THEN
                ALTER TABLE task_steps ADD COLUMN step_id UUID PRIMARY KEY DEFAULT gen_random_uuid();
                RAISE NOTICE 'Added step_id column to task_steps';
            END IF;
        END $$;
        """

        # 由于 supabase-py 限制，我们使用 RPC
        response = client.rpc('execute_sql', {'sql_query': sql}).execute()
        print("   ✅ step_id 列已添加")
    except Exception as e:
        print(f"   ⚠️ 无法添加 step_id 列: {e}")
        print("   💡 您可能需要在 Supabase Dashboard 的 SQL Editor 中手动执行:")
        print(f"   ALTER TABLE task_steps ADD COLUMN step_id UUID PRIMARY KEY DEFAULT gen_random_uuid();")

    # 检查 step_screenshots 表
    print("\n3. 检查 step_screenshots 表...")
    check_table_structure(client, 'step_screenshots')

def test_data_insertion(client: Client):
    """测试数据插入"""
    print("\n4. 测试数据插入...")
    import uuid
    from datetime import datetime

    # 创建测试数据
    test_task_id = str(uuid.uuid4())
    test_step_id = str(uuid.uuid4())

    try:
        # 首先插入一个测试任务
        task_data = {
            'task_id': test_task_id,
            'user_id': 'test-user',
            'session_id': 'test-session',
            'task_description': 'Test task for data insertion',
            'status': 'completed',
            'config': {'test': True},
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'result': 'Test completed successfully'
        }

        response = client.table('tasks').insert(task_data).execute()
        if response.data:
            print(f"   ✅ 测试任务已创建: {test_task_id}")
        else:
            print(f"   ❌ 测试任务创建失败")
            return

        # 插入测试步骤
        step_data = {
            'step_id': test_step_id,
            'task_id': test_task_id,
            'step_number': 1,
            'step_type': 'action',
            'step_data': {'action': 'test'},
            'thinking': 'Test thinking',
            'action_result': {'success': True},
            'screenshot_path': None,
            'success': True,
            'created_at': datetime.now().isoformat()
        }

        response = client.table('task_steps').insert(step_data).execute()
        if response.data:
            print(f"   ✅ 测试步骤已创建: {test_step_id}")
        else:
            print(f"   ❌ 测试步骤创建失败")

    except Exception as e:
        print(f"   ❌ 数据插入测试失败: {e}")
        print(f"   💡 可能的原因: 表结构不完整或权限不足")

def main():
    """主函数"""
    print("🔧 开始修复数据库结构...")
    print("=" * 60)

    try:
        # 连接到 Supabase
        client = connect_to_supabase()

        # 检查并修复表结构
        add_missing_columns(client)

        # 测试数据插入
        test_data_insertion(client)

        print("\n" + "=" * 60)
        print("✅ 数据库修复完成！")

    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        print("\n💡 请检查:")
        print("   1. SUPABASE_SECRET_KEY 是否正确")
        print("   2. 是否有足够的数据库权限")
        print("   3. Supabase 项目是否正常运行")

if __name__ == "__main__":
    main()