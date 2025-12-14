# 数据库迁移指南

## 概述

本目录包含 Open-AutoGLM 的数据库迁移脚本，用于创建和更新数据库表结构。

## 迁移文件

### 001_create_task_steps.sql
创建 `task_steps` 表，用于存储任务执行的详细步骤信息。

**表结构：**
- `id`: 主键（UUID）
- `task_id`: 关联的任务ID
- `step_number`: 步骤编号
- `step_type`: 步骤类型（thinking, action, screenshot 等）
- `step_data`: 步骤详细数据（JSON）
- `thinking`: AI思考过程
- `action_result`: 动作执行结果（JSON）
- `screenshot_path`: 截图文件路径
- `duration_ms`: 执行时长（毫秒）
- `success`: 执行成功状态
- `error_message`: 错误信息
- `created_at`: 创建时间

### 002_create_step_screenshots.sql
创建 `step_screenshots` 表，用于管理步骤相关的截图信息。

**表结构：**
- `id`: 主键（UUID）
- `task_id`: 关联的任务ID
- `step_id`: 关联的步骤ID
- `screenshot_path`: 截图文件路径
- `file_size`: 文件大小（字节）
- `file_hash`: 文件哈希值（SHA256）
- `compressed`: 是否压缩
- `metadata`: 截图元数据（JSON）
- `created_at`: 创建时间

### 003_extend_tasks_table.sql
扩展现有的 `tasks` 表，添加步骤统计字段。

**新增字段：**
- `total_steps`: 总步骤数
- `successful_steps`: 成功步骤数
- `failed_steps`: 失败步骤数
- `total_duration_ms`: 总执行时长（毫秒）
- `last_step_at`: 最后步骤时间
- `has_detailed_steps`: 是否有详细步骤数据

## 运行迁移

### 使用迁移运行器

```bash
# 运行所有迁移
python database/migrations/migration_runner.py

# 或使用 Python 模块方式
python -m database.migrations.migration_runner
```

### 手动执行

1. 登录 Supabase Dashboard
2. 打开 SQL 编辑器
3. 依次执行迁移文件中的 SQL 语句

### 环境变量

运行迁移前需要设置以下环境变量：

```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SECRET_KEY="your-supabase-service-role-key"
```

## 迁移依赖关系

迁移文件按数字顺序执行：

1. `001_create_task_steps.sql` - 必须首先执行
2. `002_create_step_screenshots.sql` - 依赖 task_steps 表
3. `003_extend_tasks_table.sql` - 可以独立执行

## 回滚策略

如果需要回滚迁移：

```sql
-- 删除扩展字段（003）
ALTER TABLE tasks DROP COLUMN IF EXISTS total_steps;
ALTER TABLE tasks DROP COLUMN IF EXISTS successful_steps;
ALTER TABLE tasks DROP COLUMN IF EXISTS failed_steps;
ALTER TABLE tasks DROP COLUMN IF EXISTS total_duration_ms;
ALTER TABLE tasks DROP COLUMN IF EXISTS last_step_at;
ALTER TABLE tasks DROP COLUMN IF EXISTS has_detailed_steps;

-- 删除表（002 和 001）
DROP TABLE IF EXISTS step_screenshots;
DROP TABLE IF EXISTS task_steps;
```

## 注意事项

1. **备份数据**：运行迁移前请备份重要数据
2. **测试环境**：先在测试环境中验证迁移
3. **停机时间**：某些迁移可能需要短暂停机
4. **权限要求**：需要足够的数据库权限执行 DDL 语句

## 故障排除

### 迁移失败

1. 检查 SQL 语法是否正确
2. 验证表名和字段名
3. 确认外键约束的引用完整性
4. 查看详细的错误日志

### 性能问题

1. 大表添加字段可能较慢
2. 考虑在低峰期执行迁移
3. 监控数据库性能指标

### 数据一致性问题

1. 运行迁移后验证数据完整性
2. 检查外键关系是否正确
3. 验证索引是否创建成功

## 联系支持

如果遇到迁移问题，请：

1. 查看错误日志
2. 检查数据库状态
3. 联系开发团队获取支持