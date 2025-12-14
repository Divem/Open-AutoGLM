# Change: Add Script Persistence to Database

## Why
为了增强Open-AutoGLM的脚本功能，需要将执行过程中生成的脚本保存到数据库中，实现持久化存储。当前脚本记录功能仅保存到本地文件，无法在Web界面中方便地查看和管理历史脚本。通过添加脚本持久化功能，用户可以在任务历史中查看和重放执行脚本，提升系统的可用性和脚本管理能力。

## What Changes
- 在Supabase数据库中创建scripts表，存储脚本元数据和内容
- 修改GlobalTask类，添加script_id字段关联脚本数据
- 扩展任务执行流程，在任务完成时自动保存脚本到数据库
- 在Web界面任务历史中添加"查看脚本"按钮
- 实现脚本查看页面，显示脚本详细信息和操作步骤
- 提供脚本重放和导出功能

## Impact
- Affected specs: task-management, script-recording, web-interface
- Affected code: web/app.py, phone_agent/recorder.py, web/static/js/app.js, web/templates/
- Database: 新增scripts表，修改现有tasks表添加script_id字段
- **NON-BREAKING**: 新增功能，不影响现有任务执行流程