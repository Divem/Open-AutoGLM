-- 脚本持久化功能数据库迁移
-- 创建scripts表并修改tasks表添加script_id字段

-- 1. 创建scripts表
CREATE TABLE IF NOT EXISTS scripts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id TEXT NOT NULL,
    task_name TEXT NOT NULL,
    description TEXT NOT NULL,
    total_steps INTEGER NOT NULL DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.00,
    execution_time DECIMAL(10,2) DEFAULT 0.00,
    device_id TEXT,
    model_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    script_data JSONB NOT NULL,
    script_metadata JSONB NOT NULL,
    script_version TEXT DEFAULT '1.0',
    checksum TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 2. 在tasks表中添加script_id字段
-- 注意：需要先检查是否存在，如果存在则删除并重建
DO $$
BEGIN
    -- 检查是否存在外键约束并删除
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'tasks_script_id_fkey'
        AND table_name = 'tasks'
    ) THEN
        ALTER TABLE tasks DROP CONSTRAINT tasks_script_id_fkey;
    END IF;

    -- 检查是否存在script_id列并删除
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'script_id'
    ) THEN
        ALTER TABLE tasks DROP COLUMN script_id;
    END IF;

    -- 添加UUID类型的script_id字段
    ALTER TABLE tasks ADD COLUMN script_id UUID;

    -- 添加外键约束
    ALTER TABLE tasks ADD CONSTRAINT tasks_script_id_fkey
        FOREIGN KEY (script_id) REFERENCES scripts(id);

END $$;

-- 3. 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_scripts_task_id ON scripts(task_id);
CREATE INDEX IF NOT EXISTS idx_scripts_created_at ON scripts(created_at);
CREATE INDEX IF NOT EXISTS idx_scripts_task_name ON scripts(task_name);
CREATE INDEX IF NOT EXISTS idx_scripts_device_id ON scripts(device_id);
CREATE INDEX IF NOT EXISTS idx_scripts_model_name ON scripts(model_name);
CREATE INDEX IF NOT EXISTS idx_scripts_is_active ON scripts(is_active);

-- 4. 为tasks表的script_id创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_script_id ON tasks(script_id);

-- 5. 创建更新时间戳的触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_scripts_updated_at
    BEFORE UPDATE ON scripts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 6. 添加约束确保脚本的完整性
ALTER TABLE scripts
ADD CONSTRAINT check_total_steps_non_negative
CHECK (total_steps >= 0);

ALTER TABLE scripts
ADD CONSTRAINT check_success_rate_range
CHECK (success_rate >= 0 AND success_rate <= 100);

ALTER TABLE scripts
ADD CONSTRAINT check_execution_time_non_negative
CHECK (execution_time >= 0);

-- 7. 为脚本数据创建部分索引以提高性能
CREATE INDEX IF NOT EXISTS idx_scripts_data_gin
ON scripts USING GIN (script_data);

CREATE INDEX IF NOT EXISTS idx_scripts_metadata_gin
ON scripts USING GIN (script_metadata);

-- 8. 创建视图以简化常用查询
CREATE OR REPLACE VIEW script_summary AS
SELECT
    s.id,
    s.task_id,
    s.task_name,
    s.total_steps,
    s.success_rate,
    s.execution_time,
    s.device_id,
    s.model_name,
    s.created_at,
    s.is_active,
    t.status as task_status,
    t.user_id,
    t.session_id
FROM scripts s
LEFT JOIN tasks t ON s.task_id = t.task_id
WHERE s.is_active = TRUE;

-- 9. 添加注释说明
COMMENT ON TABLE scripts IS '存储自动化脚本的详细信息，包括元数据和操作步骤';
COMMENT ON COLUMN scripts.script_data IS 'JSON格式的完整脚本数据，包含所有操作步骤';
COMMENT ON COLUMN scripts.script_metadata IS 'JSON格式的脚本元数据';
COMMENT ON COLUMN scripts.checksum IS '脚本数据的校验和，用于验证数据完整性';
COMMENT ON COLUMN scripts.script_version IS '脚本格式版本，用于兼容性管理';
COMMENT ON COLUMN scripts.is_active IS '标记脚本是否有效，软删除用';
COMMENT ON VIEW script_summary IS '脚本摘要视图，用于常用的脚本查询';