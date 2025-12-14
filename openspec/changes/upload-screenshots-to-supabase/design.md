# Design: Screenshot Upload to Supabase

## Context
当前系统截图存储在本地文件系统（web/static/screenshots），无法远程访问和持久保存。任务执行报告需要能够回放和回顾截图，以增强用户体验和调试能力。

## Goals / Non-Goals
- Goals:
  - 实现截图上传到 Supabase Storage
  - 保持本地存储作为备份
  - 在任务步骤中关联截图 URL
  - 支持批量上传和清理
- Non-Goals:
  - 不修改现有的截图捕获逻辑
  - 不改变截图的命名规则
  - 不实现实时视频流

## Decisions
- Decision: 使用已有的 Supabase Storage bucket "AutoGLMStorage"
  - Bucket 已存在，无需创建
  - 位置: https://supabase.com/dashboard/project/obkstdzogheljzmxtfvh/storage/files/buckets/AutoGLMStorage
  - 配置适当的访问策略（公开读取，受限上传）
- Decision: 双重存储策略（本地 + Supabase）
  - 本地存储作为快速访问备份
  - Supabase 提供远程访问和持久化
  - 确保数据安全性和可用性
- Decision: 异步上传
  - 不阻塞任务执行流程
  - 使用后台队列处理上传
  - 失败重试机制

## Risks / Trade-offs
- [网络延迟] → 异步上传 + 本地备份
- [存储成本] → 实施定期清理策略
- [上传失败] → 重试机制 + 错误日志
- [性能影响] → 批量上传 + 压缩优化

## Database Integration

### Schema Design
基于现有的 `add-task-step-persistence` 变更，截图将集成到以下表结构：

1. **task_steps 表扩展**
   - 添加 `screenshot_url` 字段存储 Supabase URL
   - 保留现有的 `screenshot_path` 字段作为本地路径

2. **step_screenshots 表**
   - 详细管理截图元数据
   - 关联任务ID和步骤ID
   - 存储文件信息和URL

3. **关联关系**
   - 每个任务可以有多个步骤
   - 每个步骤可以有多个截图
   - 支持一对多的任务-截图关联

## Migration Plan
1. 配置已有的 AutoGLMStorage bucket 访问策略
2. 扩展 task_steps 表添加 screenshot_url 字段
3. 创建 step_screenshots 表（基于 add-task-step-persistence 设计）
4. 部署新的截图管理器
5. 逐步迁移现有截图（可选）
6. 启用新的上传逻辑

## Open Questions
- 是否需要对截图进行压缩以节省存储空间？
- 截图保留策略（保留多长时间）？
- 是否需要实现图片访问权限控制？