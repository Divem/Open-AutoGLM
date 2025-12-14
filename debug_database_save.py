#!/usr/bin/env python3
"""
诊断数据库保存问题
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
    else:
        print("⚠️ .env 文件未找到")
except ImportError:
    print("⚠️ python-dotenv 未安装")

def check_supabase_config():
    """检查 Supabase 配置"""
    print("1. 检查 Supabase 配置...")

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SECRET_KEY')

    print(f"   SUPABASE_URL: {url[:30]}..." if url else "   SUPABASE_URL: None")
    print(f"   SUPABASE_SECRET_KEY: {'已设置' if key else '未设置'}")
    if key:
        print(f"   Key 类型: {'service_role' if 'service' in key.lower() else 'publishable'}")

    return url, key

def check_supabase_connection():
    """检查 Supabase 连接"""
    print("\n2. 检查 Supabase 连接...")

    try:
        from web.supabase_manager import SupabaseTaskManager
        manager = SupabaseTaskManager()
        print("   ✅ SupabaseTaskManager 初始化成功")

        # 测试基本连接
        result = manager.supabase.table('tasks').select('count', count='exact').execute()
        print(f"   ✅ 基本连接成功，tasks 表数量: {result.count}")

        # 检查步骤相关表
        try:
            result = manager.supabase.table('task_steps').select('count', count='exact').execute()
            print(f"   ✅ task_steps 表可访问，数量: {result.count}")
        except Exception as e:
            print(f"   ❌ task_steps 表访问失败: {e}")

        try:
            result = manager.supabase.table('step_screenshots').select('count', count='exact').execute()
            print(f"   ✅ step_screenshots 表可访问，数量: {result.count}")
        except Exception as e:
            print(f"   ❌ step_screenshots 表访问失败: {e}")

        return manager
    except Exception as e:
        print(f"   ❌ Supabase 连接失败: {e}")
        return None

def test_step_save(manager):
    """测试步骤保存"""
    print("\n3. 测试步骤保存...")

    if not manager:
        print("   ❌ 无法测试，manager 为 None")
        return False

    import uuid
    from datetime import datetime

    # 创建测试步骤数据
    test_step = {
        'step_id': str(uuid.uuid4()),
        'task_id': str(uuid.uuid4()),
        'step_number': 1,
        'step_type': 'action',
        'step_data': {
            'action': {'type': 'click'},
            'result': {'success': True}
        },
        'thinking': 'Test thinking',
        'action_result': {'success': True},
        'screenshot_path': '/test/path.png',
        'success': True,
        'created_at': datetime.now().isoformat()
    }

    try:
        # 尝试保存
        result = manager.save_step(test_step)
        if result:
            print("   ✅ 步骤保存测试成功")
            return True
        else:
            print("   ❌ 步骤保存测试失败")
            return False
    except Exception as e:
        print(f"   ❌ 步骤保存测试异常: {e}")
        return False

def test_screenshot_save(manager):
    """测试截图保存"""
    print("\n4. 测试截图保存...")

    if not manager:
        print("   ❌ 无法测试，manager 为 None")
        return False

    import uuid
    from datetime import datetime

    # 创建测试截图数据
    test_screenshot = {
        'id': str(uuid.uuid4()),
        'task_id': str(uuid.uuid4()),
        'step_id': str(uuid.uuid4()),
        'screenshot_path': '/test/screenshot.png',
        'file_size': 1024,
        'file_hash': 'test_hash',
        'compressed': False,
        'created_at': datetime.now().isoformat()
    }

    try:
        # 尝试保存
        result = manager.save_step_screenshot(test_screenshot)
        if result:
            print("   ✅ 截图保存测试成功")
            return True
        else:
            print("   ❌ 截图保存测试失败")
            return False
    except Exception as e:
        print(f"   ❌ 截图保存测试异常: {e}")
        return False

def check_web_app_logic():
    """检查 Web 应用逻辑"""
    print("\n5. 检查 Web 应用逻辑...")

    try:
        # Import from web directory
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'web'))
        from supabase_manager import SUPABASE_AVAILABLE
        print(f"   SUPABASE_AVAILABLE: {SUPABASE_AVAILABLE}")

        if SUPABASE_AVAILABLE:
            print("   ✅ Web 应用检测到 Supabase 可用")
        else:
            print("   ❌ Web 应用认为 Supabase 不可用")

        return SUPABASE_AVAILABLE
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        return False

def main():
    """主诊断函数"""
    print("🔍 开始诊断数据库保存问题...")
    print("=" * 60)

    # 检查配置
    url, key = check_supabase_config()

    # 检查连接
    manager = check_supabase_connection()

    # 测试保存功能
    if manager:
        step_success = test_step_save(manager)
        screenshot_success = test_screenshot_save(manager)
    else:
        step_success = False
        screenshot_success = False

    # 检查 Web 应用逻辑
    web_available = check_web_app_logic()

    # 总结
    print("\n" + "=" * 60)
    print("📊 诊断结果总结:")
    print(f"   配置检查: {'✅' if url and key else '❌'}")
    print(f"   数据库连接: {'✅' if manager else '❌'}")
    print(f"   步骤保存: {'✅' if step_success else '❌'}")
    print(f"   截图保存: {'✅' if screenshot_success else '❌'}")
    print(f"   Web应用检测: {'✅' if web_available else '❌'}")

    # 问题分析
    print("\n🔧 可能的问题:")
    if not key or 'service' not in key.lower():
        print("   - SUPABASE_SECRET_KEY 可能使用了错误的密钥类型")
    if not manager:
        print("   - Supabase 连接失败，检查 URL 和密钥")
    if not step_success:
        print("   - task_steps 表可能不存在或权限不足")
    if not screenshot_success:
        print("   - step_screenshots 表可能不存在或权限不足")
    if not web_available:
        print("   - Web 应用初始化时 Supabase 不可用")

    # 解决建议
    print("\n💡 解决建议:")
    print("   1. 确认使用了正确的 service_role 密钥")
    print("   2. 运行数据库迁移脚本创建必要的表")
    print("   3. 检查 Supabase 项目权限设置")
    print("   4. 重启 Web 应用确保配置生效")

if __name__ == "__main__":
    main()