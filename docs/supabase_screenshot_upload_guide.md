# Supabase 截图上传指南

本指南介绍如何将截图文件上传到 Supabase Storage，实现集中存储和远程访问。

## 功能特性

### 1. 双重存储策略
- **本地存储**: 保存到 `web/static/screenshots` 目录
- **云端存储**: 同时上传到 Supabase Storage
- **智能回退**: 优先使用云端 URL，本地路径作为备份

### 2. 自动化上传
- 任务执行时自动触发截图上传
- 异步批量处理，不影响任务性能
- 失败重试机制确保上传成功

### 3. 压缩优化
- 自动压缩大图片减少存储空间
- 支持格式转换（PNG → JPEG）
- 保持合理的图片质量

## 配置步骤

### 1. 运行数据库迁移

在 Supabase Dashboard 的 SQL Editor 中执行：

```sql
-- 添加 screenshot_url 字段到 task_steps 表
ALTER TABLE task_steps ADD COLUMN IF NOT EXISTS screenshot_url TEXT;

-- 添加 remote_url 字段到 step_screenshots 表
ALTER TABLE step_screenshots ADD COLUMN IF NOT EXISTS remote_url TEXT;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_task_steps_screenshot_url
    ON task_steps(screenshot_url)
    WHERE screenshot_url IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_step_screenshots_remote_url
    ON step_screenshots(remote_url)
    WHERE remote_url IS NOT NULL;
```

### 2. 配置 Supabase Storage

1. 访问 [Supabase Dashboard](https://app.supabase.com)
2. 选择项目：`obkstdzogheljzmxtfvh`
3. 进入 Storage 部分
4. 确认 `AutoGLMStorage` bucket 已存在
5. 配置访问策略：
   - **公开读取**：允许任何人查看截图
   - **认证上传**：只有应用可以上传文件

### 3. 设置环境变量

在 `.env` 文件中添加：

```bash
SUPABASE_URL=your-supabase-url
SUPABASE_SECRET_KEY=your-supabase-service-role-key
```

## 使用方法

### 1. 自动上传（推荐）

任务执行时，截图会自动上传：

```python
# 在 PhoneAgent 中使用
screenshot = get_screenshot(device_id="your_device_id", save_to_web_dir=True)

# 截图会自动保存到本地并触发上传
# 上传状态可在日志中查看
```

### 2. 批量上传现有截图

使用批量上传工具：

```bash
# 上传默认目录下的所有截图
python tools/bulk_upload_screenshots.py

# 指定目录和任务前缀
python tools/bulk_upload_screenshots.py \
  --screenshots-dir web/static/screenshots \
  --task-prefix migration_202412

# 预览模式（不实际上传）
python tools/bulk_upload_screenshots.py --dry-run
```

### 3. 查看上传状态

检查日志输出：
```
Screenshot uploaded successfully: screenshots/task_123/20241214_214567_a1b2c3d4.png -> https://example.com/screenshot.png
```

## Web 界面集成

### 1. 任务报告页面

- 在任务报告中，截图优先显示云端 URL
- 本地截图显示"来自云端"标识
- 支持图片预览和下载

### 2. 截图回放

在任务执行时间线中：
- 自动加载云端截图
- 本地文件作为回退
- 快速响应和流畅体验

## API 接口

### 获取任务截图

```bash
GET /api/tasks/{task_id}/screenshots
```

响应示例：
```json
{
  "data": {
    "screenshots": [
      {
        "id": "uuid",
        "task_id": "task_123",
        "screenshot_path": "web/static/screenshots/screenshot.png",
        "remote_url": "https://storage.googleapis.com/...",
        "file_size": 1024000,
        "created_at": "2024-12-14T21:45:00Z"
      }
    ],
    "total_count": 1
  }
}
```

### 更新截图 URL

```python
# 在代码中更新
global_task_manager.update_step_screenshot_url(
    step_id="step_uuid",
    local_path="web/static/screenshots/screenshot.png",
    remote_url="https://storage.url/screenshot.png"
)
```

## 故障排除

### 1. 上传失败

**问题**: 截图上传失败

**解决方案**:
- 检查 SUPABASE_URL 和 SUPABASE_SECRET_KEY 环境变量
- 确认 Supabase Storage bucket 存在
- 检查网络连接

```bash
# 测试连接
curl -H "Authorization: Bearer $SUPABASE_KEY" \
     "$SUPABASE_URL/storage/v1/bucket"

# 查看日志
grep "Screenshot" logs/application.log
```

### 2. 数据库字段缺失

**问题**: `screenshot_url` 字段不存在

**解决方案**:
```sql
-- 检查字段是否存在
SELECT column_name FROM information_schema.columns
WHERE table_name = 'task_steps' AND column_name = 'screenshot_url';

-- 如果不存在，执行迁移
ALTER TABLE task_steps ADD COLUMN screenshot_url TEXT;
```

### 3. 权限错误

**问题**: Storage 访问权限错误

**解决方案**:
1. 在 Supabase Dashboard 中配置 Storage RLS 策略
2. 允许公开读取：
   ```sql
   CREATE POLICY "Public Access" ON storage.objects
   FOR SELECT USING (true);
   ```

### 4. 性能问题

**问题**: 上传速度慢

**优化建议**:
- 增加上传并发数
- 启用图片压缩
- 使用 CDN 加速访问

```python
# 在 screenshot_manager.py 中调整
self.upload_executor = ThreadPoolExecutor(max_workers=4)  # 增加并发
self.compression_quality = 75  # 降低质量以减小文件大小
```

## 监控和维护

### 1. 上传统计

查看上传统计：

```python
from web.screenshot_manager import get_screenshot_manager

manager = get_screenshot_manager()
stats = manager.get_upload_statistics()
print(f"已上传: {stats['total_uploaded']}, 失败: {stats['total_failed']}")
```

### 2. 清理策略

自动清理规则：
- 保留最近 30 天的截图
- 定期删除孤立文件
- 压缩历史数据

### 3. 存储优化

- 监控存储使用量
- 设置存储限制告警
- 定期分析存储趋势

## 最佳实践

1. **文件命名**
   - 使用时间戳生成唯一文件名
   - 包含任务 ID 便于管理
   - 避免特殊字符

2. **错误处理**
   - 本地备份防止数据丢失
   - 重试机制处理临时错误
   - 详细日志便于调试

3. **性能优化**
   - 异步上传不阻塞主流程
   - 批量处理提高效率
   - 压缩减少存储成本

4. **安全考虑**
   - 访问控制防止未授权访问
   - 敏感内容不截图
   - 定期清理过期数据

## 更新日志

### v1.0.0 (2024-12-14)
- 初始版本发布
- 基本上传功能
- 双重存储策略
- Web 界面集成