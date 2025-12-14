# Change: Fix Task History Display Issues

## Why
任务历史记录功能无法正常显示，用户无法查看之前的执行记录，影响用户体验和任务管理的连续性。

## What Changes
- 修复前后端数据格式不匹配问题（task_id vs global_task_id）
- 统一API响应格式（确保前端能正确解析任务数据）
- 修复时间属性映射不一致问题（start_time vs created_at）
- 改进错误处理和用户反馈机制
- 确保Supabase数据持久化正常工作

## Impact
- Affected specs: task-management, task-history
- Affected code: web/app.py, web/static/js/app.js, web/supabase_manager.py
- **BREAKING**: 修改API响应格式，需要前端适配