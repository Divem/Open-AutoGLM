# Change: Fix Task Report Internal Server Error

## Why
用户在点击任务执行报告时遇到 500 内部服务器错误，导致无法查看任务执行详情。该错误影响了用户对任务执行状态的追踪和分析，降低了系统的可用性。

## What Changes
- 修复任务报告页面访问时的数据库字段错误
- 增强错误处理机制，确保即使部分数据不可用也能正常显示报告
- 验证并确保必要的数据库迁移已正确执行
- 改进前端错误处理和用户反馈
- 添加字段存在性检查，防止因缺少字段导致的错误

## Impact
- Affected specs: web-interface
- Affected code: web/app.py, web/supabase_manager.py, web/templates/task_report.html
- Critical fix for user-facing functionality