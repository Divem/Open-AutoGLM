## ADDED Requirements
### Requirement: Task History Data Consistency
任务历史数据的格式 **SHALL** 在前后端之间保持完全一致，确保数据能正确解析和显示。

#### Scenario: Unified task identifier format
- **WHEN** 前端处理任务数据
- **THEN** 所有任务必须使用统一的task_id字段进行标识
- **AND** 不得混用global_task_id等其他标识符

#### Scenario: Consistent time field mapping
- **WHEN** 显示任务时间信息
- **THEN** 前端必须正确映射后端的时间字段（created_at → start_time）
- **AND** 时间格式必须统一为ISO 8601标准格式

#### Scenario: API response structure validation
- **WHEN** 前端接收任务历史API响应
- **THEN** 响应结构必须符合{data: {tasks: [...]}}格式
- **AND** 每个任务对象必须包含所有必需的字段

### Requirement: Task History UI Enhancement
任务历史界面 **SHALL** 提供清晰的视觉反馈和交互体验。

#### Scenario: Loading state indication
- **WHEN** 任务历史正在加载
- **THEN** 界面必须显示加载指示器
- **AND** 在加载完成前隐藏任务列表

#### Scenario: Empty state handling
- **WHEN** 没有任务历史记录
- **THEN** 界面必须显示友好的空状态提示
- **AND** 提供开始执行新任务的引导