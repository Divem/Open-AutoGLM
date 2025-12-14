# Change: 修复任务持久化中的数据映射问题

## Why
当前系统在从Supabase数据库加载任务历史时存在严重的数据映射问题,导致应用启动失败。具体问题包括:

1. **数据库字段映射错误**: Supabase返回的数据包含数据库内部字段(如`id`),但`GlobalTask.from_dict()`方法没有处理这些额外字段,导致初始化失败并报错: `GlobalTask.__init__() got an unexpected keyword argument 'id'`

2. **数据一致性问题**: 数据库schema与Python数据类的字段定义不一致,数据库使用`script_id TEXT`但没有正确关联到scripts表

3. **错误处理不足**: 加载任务失败时只打印错误但不影响应用启动,导致任务历史功能完全失效

4. **缺少降级策略**: 当Supabase不可用时,没有本地存储的fallback机制

这些问题严重影响了系统的稳定性和用户体验,导致Web界面启动时无法加载任务历史,所有历史任务数据无法访问。

## What Changes

### 核心修复
1. **优化GlobalTask数据映射**
   - 修改`GlobalTask.from_dict()`方法,过滤掉数据库内部字段
   - 添加字段白名单机制,只接受dataclass定义的字段
   - 添加字段类型验证和转换

2. **修复数据库Schema一致性**
   - 更新tasks表的script_id字段定义
   - 添加外键约束确保数据完整性
   - 提供数据库迁移脚本

3. **增强错误处理**
   - 添加详细的错误日志
   - 任务加载失败时返回空列表而不是失败
   - 添加数据验证和修复机制

4. **实现降级策略**
   - 添加本地pickle文件作为fallback
   - Supabase不可用时自动切换到本地存储
   - 定期同步本地和云端数据

### 代码改进
- 添加数据验证层
- 改进异常处理和日志记录
- 添加单元测试验证数据映射逻辑

## Impact
- **Affected specs**: task-persistence, data-mapping
- **Affected code**:
  - `web/supabase_manager.py` - 核心修复
  - `database/create_supabase_tables.py` - Schema更新
  - `web/app.py` - 错误处理改进
- **Database changes**:
  - 修改tasks表schema(添加约束)
  - 需要数据迁移脚本
- **Breaking changes**: 无,向后兼容
- **Risk level**: 低 - 仅修复现有bug,不改变业务逻辑

## Success Criteria
1. 应用启动时能正确加载所有历史任务,无报错
2. 新创建的任务能正确保存到数据库并在重启后加载
3. Supabase不可用时应用仍能正常启动和运行
4. 所有现有任务数据保持完整,无数据丢失
5. 通过自动化测试验证数据映射的正确性

## Out of Scope
- 任务数据的高级查询和过滤功能
- 任务历史的分页和搜索功能
- 多租户数据隔离
- 实时任务同步功能

## Dependencies
- 无新增外部依赖
- 依赖现有的Supabase Python SDK
- 需要数据库管理员权限执行Schema更新

## Timeline Estimate
- 设计和规格: 1小时
- 实现核心修复: 2-3小时
- 测试和验证: 1-2小时
- 文档更新: 0.5小时
- **总计**: 4.5-6.5小时
