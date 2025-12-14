# Change: Upload Screenshots to Supabase

## Why
目前截图文件仅存储在本地文件系统中，无法在任务执行报告中进行远程回放和回顾。将截图上传到 Supabase 可以实现集中存储、跨设备访问和持久化保存，提升任务执行的可追溯性和用户体验。

## What Changes
- 使用已有的 Supabase Storage bucket: AutoGLMStorage
  - 位置: https://supabase.com/dashboard/project/obkstdzogheljzmxtfvh/storage/files/buckets/AutoGLMStorage
- 修改截图保存逻辑，同时保存到本地和 Supabase Storage
- 扩展 task_steps 表添加 screenshot_url 字段
- 利用 step_screenshots 表管理截图元数据
- 更新 Web 界面以从 Supabase 加载截图
- 添加截图清理和管理功能

## Dependencies
**PREREQUISITE**: `add-task-step-persistence` change must be implemented first
- 依赖 task_steps 表结构
- 依赖 step_screenshots 表结构
- 将扩展现有的数据库表而非创建新表

## Impact
- Affected specs: task-management
- Affected code:
  - web/supabase_manager.py (新增截图管理功能)
  - phone_agent/adb/screenshot.py (修改截图保存逻辑)
  - web/app.py (更新截图加载逻辑)
  - web/static/js/app.js (更新前端截图显示)
  - database/migrations/ (新增数据库迁移脚本)