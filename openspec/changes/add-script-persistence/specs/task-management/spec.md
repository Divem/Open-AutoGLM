## MODIFIED Requirements
### Requirement: Task Script Persistence
任务执行系统 **SHALL** 在任务完成时自动将记录的脚本保存到数据库中，并提供脚本查看和管理功能。

#### Scenario: Script Database Storage
- **WHEN** 任务执行完成并且启用了脚本记录功能
- **THEN** 系统 **MUST** 将生成的脚本数据保存到Supabase数据库的scripts表中
- **AND** 脚本数据 **MUST** 包含完整的元数据（任务名称、描述、执行时间等）和操作步骤
- **AND** tasks表 **MUST** 通过script_id字段关联对应的脚本记录

#### Scenario: Task-Script Association
- **WHEN** 查询任务历史时
- **THEN** 系统 **SHOULD** 返回任务关联的script_id（如果存在）
- **AND** 如果任务有脚本，界面 **MUST** 显示"查看脚本"按钮或链接
- **AND** script_id **SHOULD** 在GlobalTask数据类中可用

#### Scenario: Script Generation on Task Completion
- **WHEN** 任务执行成功或失败完成时
- **THEN** 如果启用了脚本记录，ScriptRecorder **MUST** 生成完整的脚本数据
- **AND** 脚本数据 **MUST** 包含所有成功和失败的操作步骤
- **AND** 脚本 **SHOULD** 自动保存到数据库，无需用户手动操作

### Requirement: Script Data Model
数据库脚本存储 **SHALL** 支持完整的脚本元数据和操作步骤信息。

#### Scenario: Script Database Schema
- **WHEN** 创建或更新脚本数据库记录时
- **THEN** scripts表 **MUST** 包含以下字段：
  - id: 主键，UUID格式
  - task_id: 关联的任务ID
  - task_name: 任务名称
  - description: 任务详细描述
  - total_steps: 总操作步骤数
  - success_rate: 成功率百分比
  - execution_time: 执行时间（秒）
  - device_id: 设备ID
  - model_name: 使用的模型名称
  - created_at: 创建时间戳
  - script_data: JSON格式的完整脚本数据
  - script_metadata: JSON格式的脚本元数据
- **AND** script_data **MUST** 包含所有操作步骤的详细信息

### Requirement: Script Metadata Storage
脚本元数据 **SHALL** 单独存储以支持快速查询和显示。

#### Scenario: Metadata Extraction
- **WHEN** 保存脚本到数据库时
- **THEN** 系统 **MUST** 从ScriptRecorder中提取metadata字段
- **AND** 将metadata **SHOULD** 存储为独立的JSON字段以便查询
- **AND** 常用元数据字段（task_name, total_steps, success_rate）**SHOULD** 作为独立列以支持索引