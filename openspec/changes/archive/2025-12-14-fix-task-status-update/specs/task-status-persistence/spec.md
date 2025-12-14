# Spec: Task Status Persistence

## ADDED Requirements

### Requirement: Database Task Status Updates Must Persist
任务状态更新 **SHALL** 正确持久化到Supabase数据库。

#### Scenario: Update task status to completed
- **WHEN** 任务执行完成,调用`update_task_status(task_id, 'completed')`
- **THEN** 数据库中的`tasks.status`字段**SHALL**更新为'completed'
- **AND** `tasks.end_time`字段**SHALL**设置为当前时间
- **AND** `tasks.last_activity`字段**SHALL**更新为当前时间
- **AND** 内存中的GlobalTask对象**SHALL**同步更新

#### Scenario: Update task status to error
- **WHEN** 任务执行失败,调用`update_task_status(task_id, 'error', error_message)`
- **THEN** 数据库中的`tasks.status`字段**SHALL**更新为'error'
- **AND** `tasks.error_message`字段**SHALL**包含错误信息
- **AND** `tasks.end_time`字段**SHALL**设置为当前时间
- **AND** 更新失败时**SHALL**返回False并记录日志

#### Scenario: Update task status to stopped
- **WHEN** 用户主动停止任务,调用`update_task_status(task_id, 'stopped')`
- **THEN** 数据库中的`tasks.status`字段**SHALL**更新为'stopped'
- **AND** `tasks.end_time`字段**SHALL**设置为当前时间

### Requirement: Database Query Field Names Must Match Schema
数据库查询 **SHALL** 使用实际存在的表字段名,而非对象属性别名。

#### Scenario: Use correct primary key field in WHERE clause
- **WHEN** 更新tasks表的记录
- **THEN** WHERE条件**SHALL**使用`eq('task_id', ...)`而非`eq('global_task_id', ...)`
- **AND** `task_id`**SHALL**是tasks表的实际主键字段名
- **AND** `global_task_id`**SHALL NOT**作为数据库字段名使用(它只是Python对象的property)

#### Scenario: Database update returns affected rows
- **WHEN** 执行`supabase.table('tasks').update(...).eq('task_id', task_id).execute()`
- **THEN** 匹配到记录时`result.data`**SHALL**不为空列表
- **AND** `len(result.data)`**SHALL**等于1(单条更新)
- **AND** 匹配不到记录时`result.data`**SHALL**为空列表

#### Scenario: Update failure is detected and logged
- **WHEN** 数据库更新的`result.data`为空
- **THEN** `update_task()`方法**SHALL**返回False
- **AND** **SHALL**记录WARNING级别日志:"Task update returned no data for task_id: {task_id}"
- **AND** 调用方**SHALL**能感知更新失败

### Requirement: Task Status Consistency After Page Refresh
任务状态 **SHALL** 在页面刷新后保持一致。

#### Scenario: Refresh page shows persisted status
- **WHEN** 用户完成任务后刷新Web页面
- **THEN** 任务列表**SHALL**显示正确的status(completed/error/stopped)
- **AND** 不应该恢复到'running'状态
- **AND** end_time**SHALL**显示任务结束时间

#### Scenario: Application restart preserves task status
- **WHEN** Web服务重启后加载任务
- **THEN** 从数据库加载的任务**SHALL**保持实际状态
- **AND** 不应该所有任务都显示'running'

### Requirement: Update Logging and Debugging
数据库更新操作 **SHALL** 记录详细日志便于调试。

#### Scenario: Log successful database updates
- **WHEN** 数据库更新成功(`result.data`不为空)
- **THEN** **SHALL**记录DEBUG级别日志
- **AND** 日志**SHALL**包含task_id
- **AND** 日志**SHALL**包含受影响的行数
- **AND** 日志格式: "Task updated successfully: {task_id}, affected rows: {count}"

#### Scenario: Log failed database updates
- **WHEN** 数据库更新失败(`result.data`为空)
- **THEN** **SHALL**记录WARNING级别日志
- **AND** 日志**SHALL**包含task_id和尝试更新的字段
- **AND** 日志格式: "Task update returned no data for task_id: {task_id}"
- **AND** **SHOULD**包含update_data内容便于调试

#### Scenario: Log includes context for troubleshooting
- **WHEN** 记录数据库操作日志
- **THEN** 日志**SHOULD**包含足够上下文信息
- **AND** **SHOULD**包含操作类型(update_status, update_result等)
- **AND** **SHOULD**包含时间戳
- **AND** **SHOULD**便于使用grep/日志工具筛选

### Requirement: Backwards Compatibility with GlobalTask API
代码修复 **SHALL** 保持GlobalTask对象的向后兼容性。

#### Scenario: GlobalTask.global_task_id property still works
- **WHEN** 代码访问`task.global_task_id`属性
- **THEN** **SHALL**返回`task.task_id`的值
- **AND** 不抛出AttributeError异常
- **AND** 旧代码无需修改

#### Scenario: Database operations use actual field names
- **WHEN** 执行数据库CRUD操作
- **THEN** **SHALL**使用`task_id`作为字段名
- **AND** **SHALL NOT**使用`global_task_id`作为数据库字段名
- **AND** Python对象属性和数据库字段名解耦

### Requirement: Historical Data Integrity
历史任务数据 **SHALL** 能够被修复到正确状态。

#### Scenario: Identify stale running tasks
- **WHEN** 任务的status='running'且last_activity超过1小时
- **THEN** 该任务**SHOULD**被识别为可能的stale任务
- **AND** **SHOULD**通过error_message和result字段判断实际状态

#### Scenario: Provide data migration script
- **WHEN** 需要修复历史数据
- **THEN** **SHALL**提供Python脚本`scripts/fix_historical_task_status.py`
- **AND** 脚本**SHALL**支持--dry-run模式预览修复
- **AND** 脚本**SHALL**生成详细的修复日志
- **AND** 脚本**SHALL**安全地批量更新数据库

#### Scenario: Determine correct status for stale tasks
- **WHEN** 分析stale任务的实际状态
- **THEN** 如果有`error_message`,**SHALL**判定为'error'
- **AND** 如果有`result`但无错误,**SHALL**判定为'completed'
- **AND** 其他情况**SHALL**判定为'stopped'
- **AND** 判定逻辑**SHOULD**可配置或手动审核

## MODIFIED Requirements

### Requirement: SupabaseTaskManager.update_task() Method Signature
`update_task()`方法签名 **SHALL** 使用`task_id`作为第一个参数名。

#### Scenario: Accept task_id parameter
- **WHEN** 调用`update_task(task_id, **kwargs)`
- **THEN** 第一个参数**SHALL**命名为`task_id`(而非`global_task_id`)
- **AND** 为保持兼容性,**MAY**同时接受`global_task_id`作为别名参数
- **AND** 函数内部**SHALL**统一使用`task_id`

**修改前签名**:
```python
def update_task(self, global_task_id: str, **kwargs) -> bool:
```

**修改后签名(选项1 - 推荐)**:
```python
def update_task(self, task_id: str, **kwargs) -> bool:
```

**修改后签名(选项2 - 保持兼容)**:
```python
def update_task(self, task_id: str = None, global_task_id: str = None, **kwargs) -> bool:
    # 内部处理别名
    if task_id is None and global_task_id is not None:
        task_id = global_task_id
```

## REMOVED Requirements

无

## Acceptance Criteria

### 核心功能验收

1. ✅ **数据库更新成功**:
   - 执行任务并完成后,数据库tasks.status字段为'completed'
   - 执行任务遇到错误后,数据库tasks.status字段为'error'
   - 用户停止任务后,数据库tasks.status字段为'stopped'

2. ✅ **页面刷新后状态保持**:
   - 完成任务,刷新页面,任务状态仍为'completed'
   - 不会恢复到'running'状态

3. ✅ **应用重启后状态保持**:
   - 重启Web服务后,任务状态从数据库正确加载

4. ✅ **日志记录完整**:
   - 成功更新时有DEBUG日志
   - 失败更新时有WARNING日志
   - 日志包含task_id和受影响行数

### 数据一致性验收

5. ✅ **内存和数据库同步**:
   - 更新后,内存中的GlobalTask对象状态与数据库一致
   - 不存在"内存已更新但数据库未更新"的情况

6. ✅ **历史数据修复**:
   - 所有原本status='running'的已完成任务都已修复
   - 修复后的状态反映任务的实际结果

### 性能和监控验收

7. ✅ **更新性能**:
   - 单次status更新延迟<50ms
   - 不影响任务执行性能

8. ✅ **监控和告警**:
   - 能通过日志查询更新成功率
   - 更新失败时能快速定位问题

### 兼容性验收

9. ✅ **API向后兼容**:
   - 现有调用`update_task_status()`的代码无需修改
   - GlobalTask.global_task_id属性仍可访问

10. ✅ **无回归问题**:
    - 修复后不引入新的bug
    - 所有现有功能正常工作

## Non-Functional Requirements

### 性能要求
- 数据库更新操作延迟<50ms (p99)
- 批量更新历史数据时,单条更新<100ms

### 可靠性要求
- 数据库更新成功率>99.9%
- 更新失败时必须有日志记录

### 可维护性要求
- 代码修改点集中,易于review
- 日志信息充足,便于故障排查
- 提供数据修复工具

### 安全性要求
- 数据修复脚本使用事务,防止部分失败
- 提供dry-run模式,避免误操作

## Testing Strategy

### 单元测试
```python
# tests/test_task_persistence.py

def test_update_task_with_correct_field_name():
    """测试使用正确的字段名更新任务"""
    manager = SupabaseTaskManager()
    task = manager.create_task(task_description="测试", device_id="test")

    # 更新状态
    success = manager.update_task_status(task.task_id, 'completed')
    assert success == True

    # 验证数据库
    result = manager.supabase.table('tasks')\
        .select('status')\
        .eq('task_id', task.task_id)\
        .execute()
    assert len(result.data) == 1
    assert result.data[0]['status'] == 'completed'
```

### 集成测试
```python
def test_task_status_after_execution():
    """测试任务执行完成后状态正确持久化"""
    # 1. 启动任务
    task_id = start_task("打开设置")

    # 2. 等待任务完成
    wait_for_task_completion(task_id)

    # 3. 验证数据库状态
    task = get_task_from_database(task_id)
    assert task.status == 'completed'
    assert task.end_time is not None
```

### 端到端测试
```python
def test_status_persistence_across_restart():
    """测试应用重启后状态保持"""
    # 1. 创建并完成任务
    task_id = execute_task_to_completion("测试任务")

    # 2. 重启应用
    restart_web_service()

    # 3. 验证任务状态
    response = requests.get(f'/api/tasks/{task_id}')
    assert response.json()['status'] == 'completed'
```

### 数据修复测试
```python
def test_historical_data_migration():
    """测试历史数据修复脚本"""
    # 1. 创建stale任务
    create_stale_running_task()

    # 2. 运行修复脚本
    result = run_migration_script(dry_run=True)
    assert result.tasks_to_fix > 0

    # 3. 执行实际修复
    run_migration_script(dry_run=False)

    # 4. 验证修复结果
    tasks = get_all_running_tasks()
    assert len(tasks) == 0  # 应该没有stale的running任务了
```

## Migration Plan

### 阶段1: 代码修复 (即刻执行)
1. 修改`web/supabase_manager.py:297`的字段名
2. 增强日志记录
3. 部署到生产环境

### 阶段2: 数据修复 (代码部署后)
1. 运行分析脚本识别stale任务
2. Dry-run预览修复计划
3. 执行批量修复
4. 验证修复结果

### 阶段3: 监控部署 (持续)
1. 配置日志告警规则
2. 添加自动化测试到CI/CD
3. 定期检查数据一致性

## Rollback Plan

如果修复后出现问题:

1. **代码回滚**: 恢复到修改前的代码(但会恢复bug)
2. **数据回滚**: 如果历史数据修复错误,从备份恢复
3. **降级方案**: 临时使用内存状态,忽略数据库状态不一致

**预防措施**:
- 修复前备份tasks表
- 小批量测试数据修复脚本
- 在staging环境先验证

## Related Specifications

- Task State Machine Specification
- Supabase Schema Documentation
- GlobalTask Data Model Specification
