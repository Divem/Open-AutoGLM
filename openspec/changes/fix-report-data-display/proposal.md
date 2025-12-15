# 修复报告数据显示为0的问题

## Why
诊断结果显示报告页面所有数据显示为0，通过深入调查发现：

1. **数据库连接正常**：Supabase连接成功，tasks表有39条记录
2. **步骤数据缺失**：task_steps表为空（0条记录）
3. **截图数据缺失**：step_screenshots表为空（0条记录）
4. **API端点缺失**：/api/statistics和/api/tasks/summary返回404

核心问题：任务执行时步骤和截图数据没有成功保存到数据库，导致报告统计数据全部显示为0。

## What Changes
修复任务执行过程中的步骤保存逻辑，确保所有数据正确持久化。

**主要修复**：
1. 修复SUPABASE_AVAILABLE检测逻辑
2. 确保步骤保存功能正常触发
3. 添加缺失的报告API端点
4. 增强错误处理和日志记录

## Impact
- **Affected code**:
  - `web/app.py` - 修复SUPABASE_AVAILABLE检测和步骤保存逻辑
  - `web/supabase_manager.py` - 添加统计API方法
- **User Experience**: 修复报告数据显示问题，展示真实的任务统计信息
- **Breaking Changes**: 否，仅修复功能问题
- **Dependencies**: 无新增依赖

## Technical Considerations
- **SUPABASE_AVAILABLE检测**：需要确保正确检测Supabase可用性
- **步骤保存触发**：确认任务执行时步骤保存逻辑被正确调用
- **错误处理**：增强错误日志，便于问题诊断
- **API端点**：添加必要的统计和数据查询端点