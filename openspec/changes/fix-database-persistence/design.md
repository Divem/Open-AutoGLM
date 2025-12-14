# 数据库持久化问题修复设计

## 问题诊断结果

通过运行诊断脚本，我们发现了以下具体问题：

### 1. 配置问题
- **密钥类型错误**：使用了 publishable key 而非 service_role key
- publishable key 只有读取权限，无法执行写入操作

### 2. 数据库结构问题
- **task_steps 表缺少 step_id 列**：`PGRST204` 错误
- **外键约束错误**：step_screenshots 引用不存在的 task_id：`23503` 错误

### 3. 代码问题
- **SUPABASE_AVAILABLE 检测失败**：导入路径问题

## 解决方案设计

### 1. Supabase 配置修复

**问题**：使用 publishable key 导致权限不足

**解决方案**：
1. 获取正确的 service_role key
2. 更新 .env 文件配置
3. 验证密钥权限

**实施步骤**：
```bash
# 1. 登录 Supabase Dashboard
# 2. 进入 Project Settings > API
# 3. 复制 service_role (secret) key
# 4. 更新 .env 文件
SUPABASE_SECRET_KEY=your_service_role_key_here
```

### 2. 数据库迁移

**问题**：表结构不完整，缺少必要的列

**解决方案**：运行数据库迁移脚本

**关键迁移**：
1. `001_create_task_steps.sql` - 创建 task_steps 表
2. `002_create_step_screenshots.sql` - 创建 step_screenshots 表
3. `003_extend_tasks_table.sql` - 扩展 tasks 表
4. `004_add_screenshot_urls.sql` - 添加截图URL字段

**执行顺序**：
```bash
cd database/migrations
python3 migration_runner.py
```

### 3. 代码修复

**问题1**：SUPABASE_AVAILABLE 导入失败

**原因**：`app.py` 中的导入路径不正确

**解决方案**：
```python
# 修改前
from app import SUPABASE_AVAILABLE  # ❌

# 修改后
from supabase_manager import SUPABASE_AVAILABLE  # ✅
```

**问题2**：缺少错误处理

**解决方案**：在数据库保存时添加详细错误日志
```python
try:
    result = global_task_manager.save_step(step_record)
    if not result:
        logger.error(f"Failed to save step {step_record['step_id']}")
except Exception as e:
    logger.error(f"Error saving step: {e}")
    # 不中断任务执行
```

## 实施计划

### Phase 1: 配置修复
1. 获取 service_role key
2. 更新 .env 文件
3. 验证连接

### Phase 2: 数据库迁移
1. 备份当前数据库（如果需要）
2. 运行迁移脚本
3. 验证表结构

### Phase 3: 代码修复
1. 修复导入问题
2. 添加错误处理
3. 测试连接

### Phase 4: 验证测试
1. 执行完整任务
2. 检查数据库数据
3. 验证所有功能

## 风险评估

**高风险**：
- service_role key 泄露风险
- 数据库迁移可能影响现有数据

**缓解措施**：
- 妥善保管 service_role key
- 在执行迁移前备份数据
- 先在测试环境验证

## 验证标准

修复成功后的预期结果：
1. ✅ 任务执行后步骤数据出现在 task_steps 表
2. ✅ 截图信息出现在 step_screenshots 表
3. ✅ Web 应用显示 Supabase 可用
4. ✅ 无数据库相关错误日志

## 回滚计划

如果修复失败：
1. 恢复原来的 .env 配置
2. 保留数据库备份
3. 修改代码为不依赖数据库保存的模式