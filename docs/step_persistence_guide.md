# 任务步骤持久化系统指南

## 概述

任务步骤持久化系统为 Open-AutoGLM 提供了详细的任务执行跟踪和记录功能。该系统能够捕获每个执行步骤的详细信息，包括 AI 思考过程、执行动作、截图等，为用户提供完整的任务执行可观测性。

## 功能特性

### 1. 步骤数据收集
- **自动收集**：在任务执行过程中自动收集每个步骤
- **详细信息**：记录步骤类型、数据、思考过程、执行结果
- **截图关联**：自动关联步骤与截图文件
- **性能指标**：记录步骤执行时间

### 2. 数据持久化
- **实时存储**：步骤数据实时写入 Supabase 数据库
- **批量优化**：使用批量写入提高性能
- **异步处理**：不阻塞任务执行流程
- **降级策略**：数据库不可用时保存到本地文件

### 3. 查询和分析
- **步骤查询**：按任务查询所有执行步骤
- **执行报告**：生成详细的任务执行报告
- **统计分析**：提供成功率、耗时等统计信息
- **截图管理**：组织和管理任务相关截图

## 数据结构

### task_steps 表

存储每个执行步骤的详细信息：

```sql
CREATE TABLE task_steps (
    id UUID PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    step_type TEXT NOT NULL,
    step_data JSONB NOT NULL,
    thinking TEXT,
    action_result JSONB,
    screenshot_path TEXT,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### step_screenshots 表

管理步骤相关的截图信息：

```sql
CREATE TABLE step_screenshots (
    id UUID PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_id UUID NOT NULL,
    screenshot_path TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,
    compressed BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 使用指南

### 1. 启用步骤跟踪

在 PhoneAgent 中启用步骤跟踪：

```python
from phone_agent.step_tracker import StepTracker

# 创建步骤跟踪器
tracker = StepTracker(task_id="your_task_id")

# 可选：添加回调函数
def on_step(step):
    print(f"Step {step.step_number}: {step.step_type}")

tracker.add_step_callback(on_step)
```

### 2. 记录步骤

```python
# 记录思考步骤
tracker.record_step(
    step_type=StepType.THINKING,
    step_data={"analysis": "需要点击按钮"},
    thinking="分析当前界面，找到目标按钮"
)

# 记录动作步骤
tracker.record_step(
    step_type=StepType.ACTION,
    step_data={"action": "click", "element": "button"},
    success=True
)

# 记录带截图的步骤
tracker.record_step(
    step_type=StepType.SCREENSHOT,
    step_data={"action": "capture_screen"},
    screenshot_path="/path/to/screenshot.png",
    success=True
)
```

### 3. 查询步骤数据

通过 Web API 查询：

```bash
# 获取任务的所有步骤
GET /api/tasks/{task_id}/steps

# 获取任务执行报告
GET /api/tasks/{task_id}/report

# 获取任务截图
GET /api/tasks/{task_id}/screenshots
```

### 4. 查看执行报告

1. 在 Web 界面的任务历史中
2. 点击已完成任务的"报告"按钮
3. 查看详细的执行时间线和截图

## API 接口

### 获取任务步骤

```
GET /api/tasks/{task_id}/steps
```

参数：
- `limit` (可选): 限制返回的步骤数量
- `page` (可选): 页码（默认 1）
- `per_page` (可选): 每页步骤数（默认 20，最大 100）

响应：
```json
{
  "data": {
    "steps": [...],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

### 获取任务报告

```
GET /api/tasks/{task_id}/report
```

响应：
```json
{
  "data": {
    "task": {...},
    "steps": [...],
    "screenshots": [...],
    "statistics": {
      "total_steps": 100,
      "successful_steps": 95,
      "failed_steps": 5,
      "success_rate": 0.95,
      "total_duration_ms": 60000,
      "average_step_duration_ms": 600,
      "screenshots_count": 50
    }
  }
}
```

## 配置选项

### StepTracker 配置

```python
tracker = StepTracker(
    task_id="task_id",
    buffer_size=50,        # 缓冲区大小
    flush_interval=5.0     # 刷新间隔（秒）
)
```

### 环境变量

- `SUPABASE_URL`: Supabase 项目 URL
- `SUPABASE_SECRET_KEY`: Supabase 服务角色密钥

## 性能优化

### 1. 批量写入
- 使用 50 个步骤的缓冲区
- 5 秒定时刷新机制
- 缓冲区满时立即刷新

### 2. 异步处理
- 步骤写入不阻塞任务执行
- 使用线程池处理异步操作
- 错误重试机制

### 3. 数据压缩
- 截图文件压缩存储
- 旧数据定期清理
- 分层存储策略

## 故障处理

### 1. 数据库连接失败
- 自动降级到本地文件存储
- 连接恢复后同步数据
- 详细的错误日志记录

### 2. 内存使用优化
- LRU 缓冲区淘汰机制
- 定期垃圾回收
- 内存使用监控

### 3. 数据一致性
- 事务处理确保原子性
- 数据完整性检查
- 自动修复机制

## 最佳实践

### 1. 合理使用步骤类型
- `THINKING`: AI 思考过程
- `ACTION`: 具体操作执行
- `SCREENSHOT`: 截图采集
- `ERROR`: 错误和异常
- `VALIDATION`: 结果验证

### 2. 优化截图使用
- 只在关键步骤保存截图
- 使用压缩减少存储空间
- 定期清理旧截图

### 3. 监控和维护
- 监控步骤记录成功率
- 定期清理历史数据
- 分析性能瓶颈

## 故障排除

### 常见问题

1. **步骤未被记录**
   - 检查步骤跟踪是否启用
   - 验证数据库连接
   - 查看错误日志

2. **性能影响**
   - 调整缓冲区大小
   - 增加刷新间隔
   - 检查批量写入效率

3. **截图缺失**
   - 验证截图文件路径
   - 检查文件权限
   - 确认截图生成流程

### 日志位置

- 应用日志：控制台输出
- 错误日志：详细异常信息
- 备份文件：`backup/steps/` 目录

## 更新日志

### v1.0.0 (2024-12-14)
- 初始版本发布
- 基本步骤跟踪功能
- Web 界面集成
- Supabase 存储