#!/usr/bin/env python3
"""
创建脚本持久化所需的数据库表
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# 加载环境变量
load_dotenv()

def create_scripts_tables():
    """创建脚本相关的数据库表"""

    # 获取Supabase配置
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SECRET_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ 缺少Supabase配置，请检查.env文件")
        return False

    print(f"✅ 连接到Supabase: {supabase_url}")

    # 创建客户端
    supabase = create_client(supabase_url, supabase_key)

    # 创建scripts表的SQL
    create_scripts_sql = """
    CREATE TABLE IF NOT EXISTS scripts (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        task_id TEXT NOT NULL,
        task_name TEXT NOT NULL,
        description TEXT,
        device_id TEXT,
        model_name TEXT,
        total_steps INTEGER DEFAULT 0,
        success_steps INTEGER DEFAULT 0,
        failed_steps INTEGER DEFAULT 0,
        execution_time INTEGER,
        script_data JSONB NOT NULL,
        metadata JSONB,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """

    # 创建script_summary表的SQL
    create_summary_sql = """
    CREATE TABLE IF NOT EXISTS script_summary (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
        execution_count INTEGER DEFAULT 1,
        last_executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        average_execution_time INTEGER,
        success_rate DECIMAL(5,2) DEFAULT 0.0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """

    # 创建索引
    create_indexes_sql = """
    -- scripts表索引
    CREATE INDEX IF NOT EXISTS idx_scripts_task_id ON scripts(task_id);
    CREATE INDEX IF NOT EXISTS idx_scripts_device_id ON scripts(device_id);
    CREATE INDEX IF NOT EXISTS idx_scripts_created_at ON scripts(created_at);
    CREATE INDEX IF NOT EXISTS idx_scripts_is_active ON scripts(is_active);

    -- script_summary表索引
    CREATE INDEX IF NOT EXISTS idx_script_summary_script_id ON script_summary(script_id);
    CREATE INDEX IF NOT EXISTS idx_script_summary_last_executed ON script_summary(last_executed_at);
    """

    print("\n=== 请在 Supabase Dashboard 的 SQL 编辑器中执行以下 SQL ===\n")
    print("1. 创建scripts表:")
    print(create_scripts_sql)
    print("\n2. 创建script_summary表:")
    print(create_summary_sql)
    print("\n3. 创建索引:")
    print(create_indexes_sql)

    # 测试表是否创建成功
    try:
        print("\n=== 测试表访问 ===")
        result = supabase.table('scripts').select('id').limit(1).execute()
        if result.data is not None:
            print("✅ scripts表创建成功，可以正常访问")
        else:
            print("❌ scripts表创建失败或无法访问")
            return False

        result = supabase.table('script_summary').select('id').limit(1).execute()
        if result.data is not None:
            print("✅ script_summary表创建成功，可以正常访问")
        else:
            print("❌ script_summary表创建失败或无法访问")
            return False

        print("\n✅ 所有表创建成功！")
        return True

    except Exception as e:
        print(f"❌ 表访问测试失败: {e}")
        print("\n请确保在Supabase Dashboard中执行了上述SQL语句")
        return False

if __name__ == "__main__":
    print("=== Open-AutoGLM 脚本持久化表创建工具 ===")
    success = create_scripts_tables()

    if success:
        print("\n🎉 脚本持久化数据库表创建完成！")
        print("\n接下来您需要:")
        print("1. 在Web界面配置中启用脚本记录功能")
        print("2. 重新运行任务以生成脚本记录")
    else:
        print("\n⚠️ 请按照上述说明手动创建数据库表")