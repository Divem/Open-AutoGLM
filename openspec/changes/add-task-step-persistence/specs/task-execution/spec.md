# Spec: 任务执行步骤跟踪

## ADDED Requirements

### Requirement: Task Step Data Collection
PhoneAgent **SHALL** 在任务执行过程中自动收集详细的步骤数据。

#### Scenario: Automatic step data collection during task execution
- **WHEN** PhoneAgent执行每个步骤时
- **THEN** 系统 **MUST** 自动收集以下步骤信息：
  - 步骤编号和执行时间
  - AI模型的思考过程（thinking）
  - 执行的动作详情（action）
  - 动作执行结果（action_result）
  - 相关截图文件路径
  - 步骤执行时长
  - 执行成功/失败状态
- **AND** 系统 **SHOULD** 以非阻塞方式收集数据
- **AND** 数据收集 **MUST** 不影响任务执行性能超过10%

#### Scenario: Step data structure validation
- **WHEN** 收集步骤数据时
- **THEN** 系统 **MUST** 验证数据结构的完整性
- **AND** **SHOULD** 检查必需字段的存在性
- **AND** **MUST** 验证数据类型的正确性
- **AND** 缺失数据 **SHOULD** 有合理的默认值或标记

#### Scenario: Step type classification and tracking
- **WHEN** 分类执行步骤时
- **THEN** 系统 **SHOULD** 支持以下步骤类型：
  - "thinking" - AI思考过程
  - "action" - 具体操作执行
  - "screenshot" - 截图采集
  - "error" - 错误和异常
  - "validation" - 结果验证
- **AND** 每种类型 **MUST** 有对应的数据字段结构
- **AND** 系统 **SHOULD** 支持自定义步骤类型扩展

### Requirement: Real-time Step Persistence
任务执行系统 **SHALL** 支持步骤数据的实时持久化存储。

#### Scenario: Asynchronous batch writing for performance
- **WHEN** 收集到步骤数据时
- **THEN** 系统 **MUST** 使用异步批量写入机制
- **AND** **SHOULD** 缓冲至少10个步骤或等待5秒后批量写入
- **AND** 批量写入 **MUST** 使用数据库事务确保一致性
- **AND** 任务完成时 **MUST** 强制刷新所有缓存数据

#### Scenario: Memory management and buffering
- **WHEN** 管理步骤数据缓冲区时
- **THEN** 系统 **MUST** 设置合理的内存缓冲区大小
- **AND** **SHOULD** 实现LRU淘汰机制防止内存溢出
- **AND** 缓冲区满时 **MUST** 自动触发数据写入
- **AND** 系统 **SHOULD** 监控内存使用情况

#### Scenario: Graceful degradation on database failures
- **WHEN** 数据库连接失败时
- **THEN** 系统 **SHOULD** 继续执行任务不中断
- **AND** **MUST** 将步骤数据暂存到本地文件系统
- **AND** 数据库恢复后 **SHOULD** 自动同步缓存数据
- **AND** 最终同步失败 **MUST** 记录详细错误日志

## MODIFIED Requirements

### Requirement: PhoneAgent Step Execution Flow
PhoneAgent的步骤执行流程 **SHALL** 集成步骤跟踪功能。

#### Scenario: Step tracking integration in execution flow
- **WHEN** 执行每个Agent步骤时
- **THEN** PhoneAgent **MUST** 集成StepTracker实例
- **AND** **SHOULD** 在步骤开始前记录步骤开始信息
- **AND** **MUST** 在步骤执行完成后记录完整结果
- **AND** 步骤跟踪 **SHOULD** 是可配置的开关功能

#### Scenario: Screenshot capture and metadata linking
- **WHEN** 执行截图相关操作时
- **THEN** 系统 **MUST** 自动关联截图文件与执行步骤
- **AND** **SHOULD** 记录截图文件路径、大小、创建时间
- **AND** **MUST** 支持截图文件的压缩和优化
- **AND** 截图数据 **SHOULD** 包含设备屏幕信息

#### Scenario: Step timing and performance metrics
- **WHEN** 执行步骤时
- **THEN** 系统 **MUST** 精确测量每个步骤的执行时间
- **AND** **SHOULD** 记录CPU和内存使用情况
- **AND** **MUST** 计算步骤间的间隔时间
- **AND** 性能数据 **SHOULD** 用于后续分析和优化

### Requirement: Task Completion and Data Finalization
任务完成时 **SHALL** 确保所有步骤数据完整持久化。

#### Scenario: Final data flush on task completion
- **WHEN** 任务执行完成（成功、失败或停止）时
- **THEN** 系统 **MUST** 强制刷新所有未写入的步骤数据
- **AND** **SHOULD** 验证所有步骤数据的完整性
- **AND** **MUST** 更新任务的步骤统计信息
- **AND** **SHOULD** 生成执行摘要报告

#### Scenario: Step data consistency validation
- **WHEN** 验证步骤数据一致性时
- **THEN** 系统 **MUST** 检查步骤编号的连续性
- **AND** **SHOULD** 验证时间戳的逻辑顺序
- **AND** **MUST** 确保引用的截图文件存在
- **AND** 数据不一致 **SHOULD** 触发修复或告警机制