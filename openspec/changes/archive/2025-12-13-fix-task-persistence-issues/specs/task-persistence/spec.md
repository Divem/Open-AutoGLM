# Spec: Task Persistence

## ADDED Requirements

### Requirement: Resilient Task Loading
任务加载 **SHALL** 具备弹性,单个任务损坏不影响系统启动。

#### Scenario: Application starts with partial task loading failure
- **WHEN** 数据库中有100个任务,其中5个数据损坏
- **THEN** 成功加载95个有效任务
- **AND** 跳过5个损坏任务
- **AND** `load_tasks()`返回True
- **AND** 控制台输出警告信息,列出跳过的任务ID和原因
- **AND** 应用正常启动

#### Scenario: Application starts with all tasks corrupted
- **WHEN** 数据库中所有任务数据都损坏(极端情况)
- **THEN** 不抛出异常
- **AND** `load_tasks()`返回True
- **AND** 任务列表为空
- **AND** 控制台输出错误统计
- **AND** 应用以干净状态启动

### Requirement: Database Connection Fault Tolerance
系统 **SHALL** 处理数据库不可用的情况,提供graceful degradation。

#### Scenario: Application starts when Supabase is unavailable
- **WHEN** Supabase服务不可用或配置错误
- **THEN** 不抛出未捕获异常导致应用崩溃
- **AND** 记录连接错误到日志
- **AND** 控制台显示清晰的错误和解决建议
- **AND** 管理器以"离线模式"初始化
- **AND** `load_tasks()`返回False
- **AND** 新任务暂存在内存

### Requirement: Detailed Error Logging
错误日志 **SHALL** 包含足够的诊断信息,帮助快速定位问题。

#### Scenario: Log complete diagnostic info on task loading failure
- **WHEN** 任务加载失败
- **THEN** 日志必须包含:时间戳,错误类型,错误消息,任务ID,数据快照,堆栈跟踪,修复建议
- **AND** 使用正确的日志级别(ERROR用于致命错误,WARNING用于可恢复问题)

### Requirement: Performance Monitoring
系统 **SHALL** 监控并记录任务加载性能指标。

#### Scenario: Record task loading metrics
- **WHEN** 加载大量任务(>1000个)
- **THEN** 记录:总加载时间,每个任务平均处理时间,成功/失败/跳过数量,数据库查询vs处理时间
- **AND** 如果加载时间>3秒,输出性能警告
- **AND** 记录状态统计

## MODIFIED Requirements

### Requirement: Atomic Task Status Updates
任务状态更新 **SHALL** 是原子性的,自动维护时间戳。

#### Scenario: Auto-update timestamps on status change
- **WHEN** 更新任务状态为'completed'
- **THEN** `last_activity`自动更新为当前时间
- **AND** 如果状态是终态,自动设置`end_time`
- **AND** 数据库和内存同步更新

### Requirement: Transactional Task Creation
任务创建 **SHALL** 保证内存和数据库的一致性。

#### Scenario: Rollback memory state on database insert failure
- **WHEN** 创建新任务但数据库写入失败
- **THEN** `add_task()`返回False
- **AND** 任务不添加到内存字典
- **AND** 记录明确的错误
- **AND** 不留下不一致状态
