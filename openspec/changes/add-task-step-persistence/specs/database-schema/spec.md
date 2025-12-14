# Spec: 数据库表结构扩展

## ADDED Requirements

### Requirement: Task Steps Table
数据库 **SHALL** 包含task_steps表来存储任务执行的详细步骤信息。

#### Scenario: Creating task_steps table structure
- **WHEN** 创建task_steps表时
- **THEN** 表结构 **MUST** 包含以下字段：
  - id (UUID, PRIMARY KEY) - 主键
  - task_id (TEXT, NOT NULL) - 关联的任务ID
  - step_number (INTEGER, NOT NULL) - 步骤编号
  - step_type (TEXT, NOT NULL) - 步骤类型
  - step_data (JSONB, NOT NULL) - 步骤详细数据
  - thinking (TEXT) - AI思考过程
  - action_result (JSONB) - 动作执行结果
  - screenshot_path (TEXT) - 截图文件路径
  - duration_ms (INTEGER) - 执行时长（毫秒）
  - success (BOOLEAN, DEFAULT true) - 执行成功状态
  - error_message (TEXT) - 错误信息
  - created_at (TIMESTAMPTZ, NOT NULL, DEFAULT NOW()) - 创建时间
- **AND** 表 **MUST** 有外键约束到tasks表的task_id字段
- **AND** **SHOULD** 设置合适的索引以提高查询性能

#### Scenario: Task steps indexing for performance
- **WHEN** 为task_steps表创建索引时
- **THEN** 系统 **MUST** 创建以下索引：
  - idx_task_steps_task_id_step_number (task_id, step_number) - 复合索引用于步骤查询
  - idx_task_steps_created_at (created_at) - 时间索引用于时间范围查询
  - idx_task_steps_step_type (step_type) - 类型索引用于类型过滤
- **AND** **SHOULD** 考虑添加部分索引以优化特定查询模式
- **AND** 索引 **MUST** 支持大数据量下的高效查询

### Requirement: Step Screenshots Table
数据库 **SHALL** 包含step_screenshots表来管理步骤相关的截图信息。

#### Scenario: Creating step_screenshots table structure
- **WHEN** 创建step_screenshots表时
- **THEN** 表结构 **MUST** 包含以下字段：
  - id (UUID, PRIMARY KEY) - 主键
  - task_id (TEXT, NOT NULL) - 关联的任务ID
  - step_id (UUID, NOT NULL) - 关联的步骤ID
  - screenshot_path (TEXT, NOT NULL) - 截图文件路径
  - file_size (INTEGER) - 文件大小
  - file_hash (TEXT) - 文件哈希值
  - compressed (BOOLEAN, DEFAULT false) - 是否压缩
  - metadata (JSONB) - 截图元数据
  - created_at (TIMESTAMPTZ, NOT NULL, DEFAULT NOW()) - 创建时间
- **AND** 表 **MUST** 有外键约束到task_steps表的id字段
- **AND** **SHOULD** 有唯一约束防止重复截图

#### Scenario: Screenshot file management and optimization
- **WHEN** 管理截图文件时
- **THEN** 系统 **SHOULD** 自动压缩截图文件以节省存储空间
- **AND** **MUST** 计算并存储文件哈希值用于完整性验证
- **AND** **SHOULD** 支持多种图片格式（PNG、WebP等）
- **AND** **MUST** 定期清理孤立的截图文件

### Requirement: Tasks Table Extension
现有的tasks表 **SHALL** 扩展以支持步骤统计信息。

#### Scenario: Adding step statistics fields to tasks table
- **WHEN** 扩展tasks表时
- **THEN** 表结构 **MUST** 添加以下字段：
  - total_steps (INTEGER) - 总步骤数
  - successful_steps (INTEGER) - 成功步骤数
  - failed_steps (INTEGER) - 失败步骤数
  - total_duration_ms (INTEGER) - 总执行时长
  - last_step_at (TIMESTAMPTZ) - 最后步骤时间
  - has_detailed_steps (BOOLEAN, DEFAULT false) - 是否有详细步骤数据
- **AND** 这些字段 **SHOULD** 在步骤数据更新时自动计算和更新
- **AND** **MUST** 提供向后兼容性

#### Scenario: Step statistics calculation and update
- **WHEN** 步骤数据发生变化时
- **THEN** 系统 **MUST** 自动更新tasks表中的统计字段
- **AND** **SHOULD** 使用数据库触发器或应用层逻辑实现
- **AND** 统计计算 **MUST** 保证数据一致性
- **AND** 批量更新 **SHOULD** 优化性能

## MODIFIED Requirements

### Requirement: Database Migration and Versioning
数据库模式 **SHALL** 支持安全的迁移和版本管理。

#### Scenario: Incremental database schema migration
- **WHEN** 更新数据库结构时
- **THEN** 系统 **MUST** 支持增量迁移脚本
- **AND** **SHOULD** 提供回滚机制
- **AND** **MUST** 在迁移前备份数据
- **AND** 迁移过程 **SHOULD** 不影响现有功能

#### Scenario: Schema validation and consistency checks
- **WHEN** 验证数据库结构时
- **THEN** 系统 **MUST** 检查表结构的完整性
- **AND** **SHOULD** 验证索引和约束的正确性
- **AND** **MUST** 检查数据类型的一致性
- **AND** 结构问题 **SHOULD** 自动修复或报告

### Requirement: Data Retention and Cleanup
数据库 **SHALL** 实现合理的数据保留和清理策略。

#### Scenario: Automatic data cleanup based on retention policy
- **WHEN** 实施数据保留策略时
- **THEN** 系统 **SHOULD** 支持基于时间的自动清理
- **AND** **MUST** 保留重要任务数据的最小期限
- **AND** **SHOULD** 提供配置选项调整保留策略
- **AND** 清理操作 **MUST** 记录详细的日志

#### Scenario: Data archiving for long-term storage
- **WHEN** 存档历史数据时
- **THEN** 系统 **SHOULD** 支持将旧数据移动到归档存储
- **AND** **MUST** 保持归档数据的可访问性
- **AND** **SHOULD** 压缩归档数据以节省空间
- **AND** 归档过程 **MUST** 不影响在线查询性能