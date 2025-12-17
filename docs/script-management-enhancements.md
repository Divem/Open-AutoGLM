# 脚本管理和配置功能增强文档

## 概述

本文档记录了对 Open-AutoGLM 项目中脚本管理和本地截图回退功能的完善和增强，重点包括性能优化、配置管理、错误处理和监控功能。

## 增强功能

### 1. 本地文件扫描器优化

#### 1.1 LRU缓存和性能监控
- **智能缓存系统**: 实现了带线程安全的缓存机制，避免重复扫描
- **性能统计**: 详细记录扫描次数、缓存命中率、平均扫描时间等指标
- **性能警告**: 当扫描时间超过阈值时自动发出警告

```python
# 性能统计示例
{
    'scans_count': 10,
    'cache_hits': 8,
    'total_scan_time': 1.23,
    'avg_scan_time': 0.123,
    'cache_hit_rate': 80.0
}
```

#### 1.2 文件扫描优化
- **使用 os.scandir**: 替代 glob 以提高大目录扫描性能
- **批量处理**: 支持批量扫描和分页处理大量文件
- **错误隔离**: 单个文件解析错误不影响整体扫描

#### 1.3 配置参数系统
支持通过环境变量动态配置：

```bash
# 基础配置
SCREENSHOT_FALLBACK_ENABLED=true
SCREENSHOT_DIR=static/screenshots
SCREENSHOT_CACHE_TIMEOUT=300

# 性能配置
SCREENSHOT_MAX_FILES=50
SCREENSHOT_TIME_WINDOW=10
SCREENSHOT_SCAN_BATCH_SIZE=100

# 功能开关
SCREENSHOT_ENABLE_LRU_CACHE=true
SCREENSHOT_ENABLE_PERF_MONITOR=true
SCREENSHOT_ENABLE_ASYNC=false

# 调试配置
SCREENSHOT_DEBUG=false
SCREENSHOT_LOG_LEVEL=INFO
```

### 2. 增强的错误处理

#### 2.1 分层错误处理
- **扫描错误**: 文件系统访问和文件解析错误
- **匹配错误**: 时间窗口匹配和关联错误
- **路径错误**: 文件路径转换和验证错误
- **验证错误**: 文件格式和完整性验证错误

#### 2.2 文件验证
- **格式验证**: 检查PNG文件头
- **大小验证**: 过滤空文件和异常文件
- **存在性验证**: 确保文件真实存在且可访问

#### 2.3 详细统计和日志
- **错误分类统计**: 按错误类型分类统计
- **性能指标**: 执行时间、文件数量、成功率
- **调试信息**: 可配置的详细调试日志

### 3. 配置管理API

#### 3.1 配置查询
```http
GET /api/config/screenshot-fallback
```

返回配置和性能统计信息：
```json
{
  "data": {
    "config": { /* 配置参数 */ },
    "performance_stats": { /* 性能统计 */ },
    "is_enabled": true
  }
}
```

#### 3.2 配置更新
```http
POST /api/config/screenshot-fallback
Content-Type: application/json

{
  "config": {
    "enabled": true,
    "max_files": 100,
    "cache_timeout": 600
  }
}
```

#### 3.3 缓存管理
```http
POST /api/config/screenshot-fallback/clear-cache
```

#### 3.4 功能测试
```http
POST /api/config/screenshot-fallback/test
```

返回测试结果，包括文件扫描时间、缓存状态等。

### 4. 脚本管理增强

#### 4.1 完整的脚本生命周期管理
- **保存**: 支持任务脚本的自动保存和手动保存
- **检索**: 按任务ID、关键词、设备等多维度搜索
- **导出**: 支持JSON和Python重播脚本格式
- **删除**: 支持软删除和硬删除

#### 4.2 脚本元数据管理
```python
@dataclass
class ScriptRecord:
    id: Optional[str] = None
    task_id: str = ""
    task_name: str = ""
    description: str = ""
    total_steps: int = 0
    success_rate: float = 0.0
    execution_time: float = 0.0
    device_id: Optional[str] = None
    model_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    script_data: Dict = None
    script_metadata: Dict = None
    script_version: str = "1.0"
    checksum: Optional[str] = None
    is_active: bool = True
```

#### 4.3 脚本API端点
- `GET /api/scripts` - 获取脚本列表（支持搜索和过滤）
- `GET /api/scripts/<id>` - 获取特定脚本详情
- `POST /api/scripts/<id>/export` - 导出脚本（JSON/Python格式）
- `POST /api/scripts/<id>/replay` - 启动脚本重播
- `DELETE /api/scripts/<id>` - 删除脚本
- `GET /api/scripts/summary` - 获取脚本摘要统计

### 5. Web界面集成

#### 5.1 配置页面增强
- 模型配置：支持多种预设配置（本地模型、智谱BigModel、ModelScope）
- 执行配置：最大步数、设备ID、详细输出等
- 脚本记录：自动记录和脚本输出目录配置

#### 5.2 脚本管理界面
- 脚本列表展示
- 脚本详情查看（包括步骤、成功率、执行时间等）
- 脚本导出功能
- 脚本重播功能
- 脚本删除功能

#### 5.3 设备状态监控
- 实时设备连接状态检查
- 设备信息展示（型号、连接类型等）
- 设备选择和管理

## 环境变量配置

### 截图回退配置
```bash
# 启用/禁用本地截图回退
export SCREENSHOT_FALLBACK_ENABLED=true

# 截图目录路径
export SCREENSHOT_DIR=web/static/screenshots

# 缓存超时时间（秒）
export SCREENSHOT_CACHE_TIMEOUT=300

# 最大返回截图数量
export SCREENSHOT_MAX_FILES=50

# 时间窗口（分钟）
export SCREENSHOT_TIME_WINDOW=10

# 扫描批次大小
export SCREENSHOT_SCAN_BATCH_SIZE=100

# 启用LRU缓存
export SCREENSHOT_ENABLE_LRU_CACHE=true

# 启用性能监控
export SCREENSHOT_ENABLE_PERF_MONITOR=true

# 启用异步扫描
export SCREENSHOT_ENABLE_ASYNC=false

# 调试模式
export SCREENSHOT_DEBUG=false

# 日志级别
export SCREENSHOT_LOG_LEVEL=INFO
```

### 脚本管理配置
```bash
# 启用脚本记录
export RECORD_SCRIPT=true

# 脚本输出目录
export SCRIPT_OUTPUT_DIR=web_scripts

# 脚本清理天数
export SCRIPT_CLEANUP_DAYS=90
```

## 性能优化效果

### 扫描性能
- **缓存命中率**: 通常可达到80%以上
- **扫描时间**: 大幅减少重复扫描，平均扫描时间 < 500ms
- **内存使用**: 优化内存使用，支持大量文件（>1000个）

### 错误处理
- **错误隔离**: 单个文件错误不影响整体功能
- **详细统计**: 提供详细的错误分类和性能统计
- **优雅降级**: 在各种异常情况下都能优雅降级

## 使用示例

### 配置本地截图回退
```python
# 通过环境变量配置
os.environ['SCREENSHOT_FALLBACK_ENABLED'] = 'true'
os.environ['SCREENSHOT_MAX_FILES'] = '100'

# 运行时动态配置
scanner = LocalFileScanner()
scanner.update_config({
    'enabled': True,
    'max_files': 100,
    'time_window_minutes': 15
})
```

### 测试功能
```bash
# 测试截图回退功能
curl -X POST http://localhost:5000/api/config/screenshot-fallback/test

# 获取配置状态
curl http://localhost:5000/api/config/screenshot-fallback

# 清除缓存
curl -X POST http://localhost:5000/api/config/screenshot-fallback/clear-cache
```

### 管理脚本
```bash
# 获取脚本列表
curl http://localhost:5000/api/scripts

# 导出脚本
curl http://localhost:5000/api/scripts/{id}/export?format=python

# 删除脚本
curl -X DELETE http://localhost:5000/api/scripts/{id}
```

## 监控和调试

### 性能监控
- 定期检查缓存命中率
- 监控平均扫描时间
- 跟踪错误率和分类

### 调试技巧
- 启用调试模式获取详细日志
- 使用性能监控API检查系统状态
- 检查环境变量配置是否正确

### 故障排除
1. **截图不显示**: 检查 `SCREENSHOT_FALLBACK_ENABLED` 和目录路径
2. **性能问题**: 检查缓存设置和文件数量
3. **配置不生效**: 验证环境变量格式和值

## 未来改进方向

1. **异步处理**: 实现完全异步的文件扫描和处理
2. **分布式缓存**: 支持Redis等外部缓存系统
3. **机器学习匹配**: 使用ML算法提高文件匹配准确性
4. **实时监控**: 集成Prometheus/Grafana进行实时监控
5. **批量操作**: 支持批量脚本管理和操作

---

**文档版本**: 1.0
**更新日期**: 2025-12-17
**维护者**: Open-AutoGLM 开发团队