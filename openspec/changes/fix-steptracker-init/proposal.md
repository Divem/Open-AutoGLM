# 修复 StepTracker 初始化错误

## Why
在执行任务时出现错误："StepTracker.init() missing 1 required positional argument: 'task_id'"。这是因为：

1. **初始化问题**：在 PhoneAgent 的 `__init__` 方法中，调用 `StepTracker()` 时没有传递必需的 `task_id` 参数
2. **方法调用错误**：在 PhoneAgent 的 `run` 方法中调用了不存在的 `start_task()` 方法
3. **生命周期管理不当**：StepTracker 的初始化时机与 task_id 生成时机不匹配

这导致任务执行失败，阻止了步骤追踪功能的正常工作，也影响了新实现的步骤数据库保存功能。

## What Changes
修复 StepTracker 的初始化和使用方式，确保步骤追踪功能正常工作。

**主要修改**：
- 修改 PhoneAgent 中 StepTracker 的初始化时机
- 移除不存在的 `start_task()` 方法调用
- 确保在有了 task_id 后再初始化 StepTracker

## Impact
- **Affected code**:
  - `phone_agent/agent.py` - 修改 StepTracker 初始化逻辑
- **User Experience**: 修复任务执行错误，恢复步骤追踪功能
- **Breaking Changes**: 否，仅修复错误
- **Dependencies**: 无新增依赖

## Technical Considerations
- **初始化时机**：需要在 task_id 生成后才能初始化 StepTracker
- **错误处理**：确保即使 StepTracker 初始化失败也不影响任务执行
- **向后兼容**：保持与现有代码的兼容性