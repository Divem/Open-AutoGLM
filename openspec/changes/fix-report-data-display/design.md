# 报告数据为0问题修复设计

## 问题诊断结果

通过运行诊断脚本，我们发现了以下具体问题：

### 1. 数据层面
- ✅ **数据库连接正常**：Supabase连接成功
- ✅ **tasks表有数据**：39条任务记录（14个完成，21个运行中）
- ❌ **task_steps表为空**：0条记录
- ❌ **step_screenshots表为空**：0条记录

### 2. API层面
- ❌ **统计API缺失**：/api/statistics返回404
- ❌ **摘要API缺失**：/api/tasks/summary返回404

### 3. 根本原因
任务执行时，步骤和截图数据没有成功保存到数据库，导致：
1. 报告查询task_steps表时返回空数据
2. 所有基于步骤的统计显示为0
3. 截图相关统计无法显示

## 解决方案设计

### 1. 修复步骤保存逻辑

**问题分析**：
- `SUPABASE_AVAILABLE`检测可能有问题
- `global_task_manager`可能没有`save_step`方法
- 错误被静默忽略，没有日志输出

**解决方案**：
```python
# 在web/app.py中添加详细日志
if SUPABASE_AVAILABLE and hasattr(global_task_manager, 'save_step'):
    try:
        # 保存步骤
        step_id = global_task_manager.save_step(step_record)
        if step_id:
            logger.info(f"Step saved successfully: {step_id}")
        else:
            logger.error(f"Failed to save step: {step_record.get('task_id')}")
    except Exception as e:
        logger.error(f"Error saving step: {e}")
else:
    logger.warning("Step saving not available")
```

### 2. 添加统计API端点

**实现/api/statistics端点**：
```python
@app.route('/api/statistics')
def get_statistics():
    """获取任务统计信息"""
    try:
        manager = SupabaseTaskManager()
        stats = manager.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**实现/api/tasks/summary端点**：
```python
@app.route('/api/tasks/summary')
def get_task_summary():
    """获取任务摘要信息"""
    try:
        manager = SupabaseTaskManager()
        summary = manager.get_task_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### 3. 扩展SupabaseTaskManager

**添加get_statistics方法**：
```python
def get_statistics(self):
    """获取任务统计信息"""
    try:
        # 任务统计
        total_tasks = self.get_total_task_count()
        completed_tasks = self.get_completed_task_count()
        failed_tasks = self.get_failed_task_count()

        # 步骤统计
        total_steps = self.get_total_step_count()
        successful_steps = self.get_successful_step_count()

        # 截图统计
        total_screenshots = self.get_total_screenshot_count()

        return {
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "running": total_tasks - completed_tasks - failed_tasks
            },
            "steps": {
                "total": total_steps,
                "successful": successful_steps
            },
            "screenshots": {
                "total": total_screenshots
            }
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {}
```

## 实施步骤

### Phase 1: 诊断和日志
1. 在步骤保存代码周围添加详细日志
2. 运行一个测试任务，观察日志输出
3. 确定保存失败的具体原因

### Phase 2: 修复保存逻辑
1. 修复SUPABASE_AVAILABLE检测
2. 确保global_task_manager正确初始化
3. 添加错误处理和验证

### Phase 3: 实现API端点
1. 添加统计方法到SupabaseTaskManager
2. 实现/api/statistics端点
3. 实现/api/tasks/summary端点

### Phase 4: 测试验证
1. 执行测试任务
2. 验证步骤保存
3. 检查报告数据
4. 测试API端点

## 验证标准

修复成功后的预期结果：
1. ✅ 任务执行时步骤保存到task_steps表
2. ✅ 截图信息保存到step_screenshots表
3. ✅ /api/statistics返回正确的统计数据
4. ✅ 报告页面显示真实数据（不为0）
5. ✅ 日志显示步骤保存成功

## 风险评估

**低风险**：
- 主要是修复现有功能，不改变核心逻辑
- 添加的API端点是只读的
- 错误处理确保不影响现有功能

**缓解措施**：
- 在修复前运行完整测试
- 保留原始代码备份
- 分阶段实施，每步验证