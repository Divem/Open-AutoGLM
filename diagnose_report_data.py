#!/usr/bin/env python3
"""
诊断报告数据为 0 的问题
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

def check_database_connection():
    """检查数据库连接和数据"""
    print("\n1. 检查数据库连接和数据...")
    try:
        from supabase import create_client

        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SECRET_KEY')

        if not url or not key:
            print("   ❌ 缺少数据库配置")
            return False, None

        client = create_client(url, key)

        # 检查 tasks 表
        print("   检查 tasks 表...")
        result = client.table('tasks').select('count', count='exact').execute()
        if result.count is not None:
            print(f"   ✅ tasks 表连接成功，总数: {result.count}")
        else:
            print("   ❌ tasks 表查询失败")
            return False, None

        # 检查 task_steps 表
        print("   检查 task_steps 表...")
        try:
            result = client.table('task_steps').select('count', count='exact').execute()
            if result.count is not None:
                print(f"   ✅ task_steps 表连接成功，总数: {result.count}")
            else:
                print("   ❌ task_steps 表查询失败")
        except Exception as e:
            print(f"   ❌ task_steps 表不存在或访问失败: {e}")

        # 检查 step_screenshots 表
        print("   检查 step_screenshots 表...")
        try:
            result = client.table('step_screenshots').select('count', count='exact').execute()
            if result.count is not None:
                print(f"   ✅ step_screenshots 表连接成功，总数: {result.count}")
            else:
                print("   ❌ step_screenshots 表查询失败")
        except Exception as e:
            print(f"   ❌ step_screenshots 表不存在或访问失败: {e}")

        return True, client

    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        return False, None

def check_web_app_report_logic():
    """检查 Web 应用的报告逻辑"""
    print("\n2. 检查 Web 应用报告逻辑...")

    try:
        # 检查报告相关的路由
        from web.app import PhoneAgentWeb
        import inspect

        # 查找报告相关的方法
        app = PhoneAgentWeb()

        # 检查是否有报告路由
        if hasattr(app, 'app'):
            routes = []
            for rule in app.app.url_map.iter_rules():
                if 'report' in str(rule.rule):
                    routes.append(str(rule))
            if routes:
                print(f"   ✅ 找到报告路由: {routes}")
            else:
                print("   ⚠️ 未找到报告路由")

        # 检查数据库管理器
        try:
            from web.supabase_manager import SupabaseTaskManager
            manager = SupabaseTaskManager()
            print("   ✅ SupabaseTaskManager 初始化成功")

            # 测试获取统计数据
            stats = manager.get_statistics()
            if stats:
                print(f"   📊 统计数据: {stats}")
            else:
                print("   ⚠️ 获取统计数据失败或返回空")

        except Exception as e:
            print(f"   ❌ SupabaseTaskManager 初始化失败: {e}")

    except Exception as e:
        print(f"   ❌ 检查报告逻辑失败: {e}")

def test_direct_data_queries():
    """直接测试数据查询"""
    print("\n3. 直接测试数据查询...")

    try:
        from supabase import create_client
        from datetime import datetime, timedelta

        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SECRET_KEY')
        client = create_client(url, key)

        # 查询最近 7 天的任务
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()

        print(f"   查询 {seven_days_ago} 之后的数据...")

        # 查询任务
        tasks = client.table('tasks')\
            .select('task_id, status, created_at')\
            .gte('created_at', seven_days_ago)\
            .execute()

        if tasks.data:
            print(f"   ✅ 找到 {len(tasks.data)} 个任务")
            for status in ['completed', 'failed', 'running']:
                count = sum(1 for t in tasks.data if t.get('status') == status)
                if count > 0:
                    print(f"      - {status}: {count}")
        else:
            print("   ⚠️ 最近 7 天没有任务数据")

        # 查询步骤
        try:
            steps = client.table('task_steps')\
                .select('*')\
                .gte('created_at', seven_days_ago)\
                .limit(10)\
                .execute()

            if steps.data:
                print(f"   ✅ 找到 {len(steps.data)} 个步骤（最近10个）")
            else:
                print("   ⚠️ 没有步骤数据")
        except Exception as e:
            print(f"   ⚠️ 步骤查询失败: {e}")

        # 查询截图
        try:
            screenshots = client.table('step_screenshots')\
                .select('*')\
                .gte('created_at', seven_days_ago)\
                .limit(10)\
                .execute()

            if screenshots.data:
                print(f"   ✅ 找到 {len(screenshots.data)} 个截图（最近10个）")
            else:
                print("   ⚠️ 没有截图数据")
        except Exception as e:
            print(f"   ⚠️ 截图查询失败: {e}")

    except Exception as e:
        print(f"   ❌ 直接查询失败: {e}")

def check_api_endpoints():
    """检查 API 端点"""
    print("\n4. 检查 API 端点...")

    try:
        import requests

        # 检查统计 API
        response = requests.get('http://localhost:8080/api/statistics', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ /api/statistics 响应成功: {stats}")
        else:
            print(f"   ❌ /api/statistics 响应失败: {response.status_code}")

        # 检查任务报告 API
        response = requests.get('http://localhost:8080/api/tasks/summary', timeout=5)
        if response.status_code == 200:
            summary = response.json()
            print(f"   ✅ /api/tasks/summary 响应成功: {summary}")
        else:
            print(f"   ❌ /api/tasks/summary 响应失败: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("   ❌ Web 服务未运行（连接拒绝）")
    except Exception as e:
        print(f"   ❌ API 检查失败: {e}")

def main():
    """主诊断函数"""
    print("🔍 诊断报告数据为 0 的问题...")
    print("=" * 60)

    # 检查数据库
    db_ok, client = check_database_connection()

    # 检查 Web 应用逻辑
    check_web_app_report_logic()

    # 直接测试数据查询
    test_direct_data_queries()

    # 检查 API 端点
    check_api_endpoints()

    print("\n" + "=" * 60)
    print("📊 诊断总结:")

    if not db_ok:
        print("❌ 数据库连接问题 - 这很可能是报告数据为 0 的原因")
    else:
        print("✅ 数据库连接正常")

    print("\n💡 可能的解决方案:")
    print("1. 如果数据库连接失败：")
    print("   - 检查 SUPABASE_URL 和 SUPABASE_SECRET_KEY 配置")
    print("   - 确认使用了 service_role key")
    print("   - 检查 Supabase 项目状态")

    print("\n2. 如果数据库连接正常但数据为空：")
    print("   - 确认任务执行时步骤保存功能正常工作")
    print("   - 检查任务执行是否触发了数据库保存")
    print("   - 查看任务执行日志是否有错误")

    print("\n3. 如果数据存在但报告显示为 0：")
    print("   - 检查报告 API 是否正确查询数据库")
    print("   - 确认统计计算逻辑是否正确")
    print("   - 检查前端是否正确显示数据")

if __name__ == "__main__":
    main()