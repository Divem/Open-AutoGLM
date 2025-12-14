# 修复数据库持久化问题

## Why
执行任务后，截图和步骤都没有保存到数据库中。通过诊断发现以下问题：

1. **错误的 Supabase 密钥类型**：使用了 publishable key 而不是 service_role key，导致权限不足
2. **数据库表结构不完整**：task_steps 表缺少 step_id 列
3. **外键约束错误**：step_screenshots 表引用了不存在的 task_id
4. **SUPABASE_AVAILABLE 检测失败**：Web 应用无法正确检测 Supabase 可用性

诊断错误信息：
- `PGRST204: Could not find the 'step_id' column of 'task_steps' in the schema cache`
- `23503: insert or update on table "step_screenshots" violates foreign key constraint`
- 使用了 publishable key 而非 service_role key

## What Changes
修复数据库持久化问题，确保步骤和截图正确保存。

**主要修改**：
1. 修正 Supabase 配置，使用正确的 service_role key
2. 运行数据库迁移，确保表结构完整
3. 修复 Web 应用中的 Supabase 检测逻辑
4. 添加数据库连接和保存的错误处理

## Impact
- **Affected code**:
  - `.env` - Supabase 密钥配置
  - `database/migrations/` - 数据库迁移脚本
  - `web/supabase_manager.py` - Supabase 连接和错误处理
  - `web/app.py` - Supabase 可用性检测
- **User Experience**: 修复后所有任务步骤和截图将正确保存到数据库
- **Breaking Changes**: 否，仅修复配置和数据库结构
- **Dependencies**: 需要运行数据库迁移脚本

## Technical Considerations
- **密钥安全**: service_role key 具有完整权限，必须妥善保管
- **数据库迁移**: 需要按正确顺序执行迁移脚本
- **错误处理**: 增强错误日志，便于问题诊断
- **向后兼容**: 确保现有数据不受影响