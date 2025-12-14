# Spec: Data Mapping

## ADDED Requirements

### Requirement: Database Field Filtering
GlobalTask数据映射 **SHALL** 正确过滤数据库内部字段,防止初始化失败。

#### Scenario: Filter extra database fields when loading tasks
- **WHEN** 从Supabase数据库加载任务记录
- **THEN** `GlobalTask.from_dict()`必须过滤掉数据库内部字段(`id`, `updated_at`)
- **AND** 只保留dataclass定义的业务字段
- **AND** 不抛出"unexpected keyword argument"异常
- **AND** 记录被过滤字段的debug日志

#### Scenario: Handle missing optional fields gracefully
- **WHEN** 任务数据中可选字段缺失或为NULL
- **THEN** 可选字段必须设置为None
- **AND** 不抛出KeyError异常
- **AND** 必需字段缺失时抛出明确的ValidationError

### Requirement: Type-Safe Field Conversion
数据类型转换 **SHALL** 安全可靠,特别是datetime和JSON字段。

#### Scenario: Convert ISO datetime strings to Python datetime objects
- **WHEN** 数据库返回ISO 8601格式的时间字符串
- **THEN** 必须成功解析为datetime对象
- **AND** 支持timezone-aware和timezone-naive格式
- **AND** 解析失败时抛出清晰的错误信息

#### Scenario: Validate and convert config JSON field
- **WHEN** config字段为JSON字符串而非字典
- **THEN** 必须尝试解析为字典
- **AND** 解析失败时记录错误并使用空字典

### Requirement: Data Integrity Validation
任务数据 **SHALL** 通过完整性验证才能被加载。

#### Scenario: Validate required fields presence
- **WHEN** 验证任务数据
- **THEN** 所有必需字段(task_id, session_id, user_id, task_description, status, created_at, last_activity, config)必须存在
- **AND** 缺失时抛出ValidationError,明确指出缺失字段

#### Scenario: Validate status enum values
- **WHEN** 检查status字段值
- **THEN** 值必须是['running', 'completed', 'error', 'stopped']之一
- **AND** 非法值抛出ValidationError,列出所有有效值

### Requirement: Error Recovery
数据映射错误 **SHALL** 被优雅处理,不影响其他任务加载。

#### Scenario: Skip corrupted task and continue loading
- **WHEN** 加载任务列表时遇到一个数据损坏的任务
- **THEN** 记录该任务的错误信息
- **AND** 跳过该任务
- **AND** 继续加载其他有效任务
- **AND** 最终返回成功状态

#### Scenario: Auto-fix recoverable data issues
- **WHEN** 任务的last_activity字段缺失但created_at存在
- **THEN** 自动设置`last_activity = created_at`
- **AND** 记录修复操作到日志
- **AND** 成功创建任务对象

## MODIFIED Requirements

### Requirement: Legacy Field Name Compatibility
GlobalTask属性访问 **SHALL** 保持向后兼容性。

#### Scenario: Support legacy property names
- **WHEN** 代码使用legacy属性名(global_task_id, task, error, start_time)
- **THEN** 必须正确返回对应的新字段值
- **AND** 不触发弃用警告
- **AND** 文档注明推荐使用新字段名
