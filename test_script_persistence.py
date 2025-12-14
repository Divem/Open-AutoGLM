#!/usr/bin/env python3
"""
测试脚本持久化功能
"""
import sys
import os
sys.path.append('web')

try:
    from supabase import create_client
    from supabase_manager import SUPABASE_URL, SUPABASE_KEY
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()

    print("=== 测试Supabase连接 ===")
    print(f"URL: {SUPABASE_URL}")
    print(f"Key: {'已设置' if SUPABASE_KEY else '未设置'}")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("\n=== 测试tasks表 ===")
    try:
        result = supabase.table('tasks').select('id', 'task_id', 'script_id').limit(1).execute()
        print(f"✅ tasks表正常，数据: {result.data}")
    except Exception as e:
        print(f"❌ tasks表错误: {e}")

    print("\n=== 测试scripts表 ===")
    try:
        result = supabase.table('scripts').select('id', 'task_name').limit(1).execute()
        print(f"✅ scripts表正常，数据: {result.data}")
    except Exception as e:
        print(f"❌ scripts表错误: {e}")
        if "Does not exist" in str(e) or "does not exist" in str(e):
            print("⚠️  scripts表不存在，需要创建")

    print("\n=== 测试script_summary表 ===")
    try:
        result = supabase.table('script_summary').select('id').limit(1).execute()
        print(f"✅ script_summary表正常，数据: {result.data}")
    except Exception as e:
        print(f"❌ script_summary表错误: {e}")

except Exception as e:
    print(f"连接错误: {e}")
    sys.exit(1)