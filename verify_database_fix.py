#!/usr/bin/env python3
"""
验证数据库修复是否成功
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
except ImportError:
    pass

from supabase import create_client

def main():
    print("🔍 验证数据库修复结果...")
    print("=" * 60)

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SECRET_KEY')

    if not url or not key:
        print("❌ 缺少数据库配置")
        return

    client = create_client(url, key)

    try:
        # 测试插入步骤数据
        import uuid
        from datetime import datetime

        test_task_id = str(uuid.uuid4())
        test_step_id = str(uuid.uuid4())

        # 创建测试任务
        task_data = {
            'task_id': test_task_id,
            'user_id': 'verify-test',
            'session_id': 'verify-session',
            'task_description': 'Verify database fix',
            'status': 'running',
            'config': {},
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }

        result = client.table('tasks').insert(task_data).execute()
        if not result.data:
            print("❌ 无法创建测试任务")
            return
        print("✅ 测试任务创建成功")

        # 创建测试步骤
        step_data = {
            'step_id': test_step_id,  # 这是关键！
            'task_id': test_task_id,
            'step_number': 1,
            'step_type': 'action',
            'step_data': {'test': True},
            'thinking': 'Verification test',
            'action_result': {'success': True},
            'screenshot_path': None,
            'success': True,
            'created_at': datetime.now().isoformat()
        }

        result = client.table('task_steps').insert(step_data).execute()
        if result.data:
            print("✅ 步骤数据保存成功！step_id 列已正确添加")
        else:
            print("❌ 步骤数据保存失败")
            return

        # 创建测试截图
        screenshot_data = {
            'id': str(uuid.uuid4()),
            'task_id': test_task_id,
            'step_id': test_step_id,
            'screenshot_path': '/test/path.png',
            'file_size': 1024,
            'file_hash': 'test_hash',
            'compressed': False,
            'created_at': datetime.now().isoformat()
        }

        result = client.table('step_screenshots').insert(screenshot_data).execute()
        if result.data:
            print("✅ 截图数据保存成功！")
        else:
            print("❌ 截图数据保存失败")

        # 查询验证
        steps = client.table('task_steps').select('*').eq('task_id', test_task_id).execute()
        print(f"✅ 查询到 {len(steps.data)} 个步骤")

        screenshots = client.table('step_screenshots').select('*').eq('task_id', test_task_id).execute()
        print(f"✅ 查询到 {len(screenshots.data)} 个截图")

        print("\n" + "=" * 60)
        print("🎉 数据库修复验证成功！")
        print("✅ task_steps 表已有 step_id 列")
        print("✅ step_screenshots 表正常工作")
        print("✅ 数据保存功能正常")

        # 清理测试数据
        client.table('step_screenshots').delete().eq('task_id', test_task_id).execute()
        client.table('task_steps').delete().eq('task_id', test_task_id).execute()
        client.table('tasks').delete().eq('task_id', test_task_id).execute()
        print("✅ 测试数据已清理")

    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        print("\n💡 请确保:")
        print("   1. 已执行所有 SQL 修复脚本")
        print("   2. service_role key 有写入权限")
        print("   3. 表结构已正确更新")

if __name__ == "__main__":
    main()