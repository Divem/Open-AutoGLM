#!/usr/bin/env python3
"""测试Supabase数据库连接"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'web'))

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SECRET_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("=" * 60)
print("Supabase 连接测试")
print("=" * 60)

print(f"\n📍 Supabase URL: {SUPABASE_URL}")
print(f"🔑 Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "❌ 未找到密钥")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ 缺少Supabase配置，请检查.env文件")
    sys.exit(1)

# 测试基本导入
try:
    from supabase import create_client, Client
    print("\n✅ supabase库已安装")
except ImportError as e:
    print(f"\n❌ 导入失败: {e}")
    sys.exit(1)

# 测试连接
try:
    print("\n🔌 正在连接Supabase...")
    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ 客户端创建成功")
except Exception as e:
    print(f"❌ 客户端创建失败: {e}")
    sys.exit(1)

# 测试查询tasks表
try:
    print("\n📊 正在查询tasks表...")
    result = client.table('tasks').select('*').limit(5).execute()
    print(f"✅ 查询成功，找到 {len(result.data)} 条任务")

    if result.data:
        print("\n任务列表:")
        for task in result.data[:3]:
            task_id = task.get('task_id', 'N/A')
            status = task.get('status', 'N/A')
            description = task.get('task_description', 'N/A')[:50]
            print(f"  - {task_id}: {status} - {description}")
    else:
        print("  (空表)")

except Exception as e:
    print(f"❌ 查询tasks表失败: {e}")
    print("\n可能的原因:")
    print("  1. tasks表不存在")
    print("  2. SSL/TLS连接问题")
    print("  3. 权限不足")
    print("  4. 网络连接问题")

# 测试查询task_steps表
try:
    print("\n📊 正在查询task_steps表...")
    result = client.table('task_steps').select('*').limit(5).execute()
    print(f"✅ 查询成功，找到 {len(result.data)} 条步骤")
except Exception as e:
    print(f"⚠️  查询task_steps表失败: {e}")

# 测试查询screenshots表
try:
    print("\n📊 正在查询screenshots表...")
    result = client.table('screenshots').select('*').limit(5).execute()
    print(f"✅ 查询成功，找到 {len(result.data)} 条截图")
except Exception as e:
    print(f"⚠️  查询screenshots表失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
