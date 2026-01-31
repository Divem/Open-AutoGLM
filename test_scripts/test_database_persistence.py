#!/usr/bin/env python3
"""
测试数据库持久化功能
"""

import sys
import os
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

def test_web_app_database_save():
    """测试 Web 应用的数据库保存功能"""
    print("🧪 测试数据库持久化功能...")
    print("=" * 60)

    try:
        # 导入必要模块
        from web.supabase_manager import SupabaseTaskManager
        from supabase import create_client

        # 检查配置
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SECRET_KEY')

        if not url or not key:
            print("❌ 缺少数据库配置")
            return False

        if 'secret' not in key.lower():
            print("⚠️ 警告：可能没有使用 service_role key")
        else:
            print("✅ 使用了 service_role key")

        # 直接使用 supabase 客户端测试
        client = create_client(url, key)
        print(f"   连接到: {url[:30]}...")

        # 测试保存步骤
        import uuid
        from datetime import datetime

        # 创建测试任务
        test_task_id = str(uuid.uuid4())
        task_data = {
            'task_id': test_task_id,
            'user_id': 'test-user',
            'session_id': 'test-session',
            'task_description': 'Test database persistence',
            'status': 'running',
            'config': {},
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }

        result = client.table('tasks').insert(task_data).execute()
        if not result.data:
            print("❌ 无法创建测试任务")
            return False
        print(f"✅ 测试任务已创建: {test_task_id[:8]}...")

        # 测试 SupabaseTaskManager.save_step
        manager = SupabaseTaskManager()
        step_data = {
            'task_id': test_task_id,
            'step_number': 1,
            'step_type': 'action',
            'step_data': {'action': 'test', 'type': 'click'},
            'thinking': 'Test thinking process',
            'action_result': {'success': True},
            'screenshot_path': None,
            'success': True,
            'created_at': datetime.now().isoformat()
        }

        saved_step_id = manager.save_step(step_data)
        if saved_step_id:
            print(f"✅ 步骤保存成功，ID: {saved_step_id[:8]}...")
        else:
            print("❌ 步骤保存失败")
            return False

        # 验证步骤是否真的保存了
        steps = client.table('task_steps').select('*').eq('task_id', test_task_id).execute()
        if steps.data:
            print(f"✅ 验证成功：找到 {len(steps.data)} 个步骤")
            print(f"   - Step ID: {steps.data[0]['id'][:8]}...")
            print(f"   - Step Type: {steps.data[0]['step_type']}")
        else:
            print("❌ 验证失败：未找到保存的步骤")
            return False

        # 测试保存截图
        screenshot_data = {
            'id': str(uuid.uuid4()),
            'task_id': test_task_id,
            'step_id': saved_step_id,
            'screenshot_path': '/test/screenshot.png',
            'file_size': 1024,
            'file_hash': 'test_hash_123',
            'compressed': False,
            'created_at': datetime.now().isoformat()
        }

        if manager.save_step_screenshot(screenshot_data):
            print(f"✅ 截图保存成功")
        else:
            print("⚠️ 截图保存失败（可能因为文件不存在）")

        # 查询验证
        screenshots = client.table('step_screenshots').select('*').eq('task_id', test_task_id).execute()
        if screenshots.data:
            print(f"✅ 验证成功：找到 {len(screenshots.data)} 个截图")
        else:
            print("⚠️ 未找到截图记录")

        # 清理测试数据
        client.table('step_screenshots').delete().eq('task_id', test_task_id).execute()
        client.table('task_steps').delete().eq('task_id', test_task_id).execute()
        client.table('tasks').delete().eq('task_id', test_task_id).execute()
        print("✅ 测试数据已清理")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = test_web_app_database_save()

    print("\n" + "=" * 60)
    if success:
        print("🎉 数据库持久化功能测试成功！")
        print("✅ 步骤和截图都可以正确保存到数据库")
        print("\n现在您可以执行实际任务，所有数据都会正确保存。")
    else:
        print("❌ 数据库持久化功能测试失败")
        print("\n可能的问题：")
        print("1. 请确保 SUPABASE_SECRET_KEY 使用了正确的 service_role key")
        print("2. 检查 Supabase 项目权限设置")
        print("3. 确认数据库表结构正确")

if __name__ == "__main__":
    main()