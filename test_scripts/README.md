# 测试脚本归档

本文件夹包含项目中使用的各种测试脚本。

## 📋 测试脚本列表

### 🔌 数据库连接测试

#### `test_supabase_connection.py`
**用途**: 测试 Supabase 数据库连接状态

**运行方式**:
```bash
python3 test_supabase_connection.py
```

**测试内容**:
- Supabase 客户端连接
- tasks 表查询
- task_steps 表查询
- screenshots 表查询

---

### ⏱️ 时间格式测试

#### `test_time_formatting.py` / `test_time_formatting.html`
**用途**: 测试时间格式化和显示功能

#### `test_time_parsing.html`
**用途**: 测试时间解析功能

#### `test_time_simple.html`
**用途**: 简单时间格式测试

---

### 📊 数据持久化测试

#### `test_database_persistence.py`
**用途**: 测试数据库持久化功能

#### `test_script_persistence.py`
**用途**: 测试脚本持久化功能

#### `test_record_step_fix.py`
**用途**: 测试步骤记录修复

#### `test_step_tracking.py`
**用途**: 测试步骤跟踪功能

#### `test_steptracker_fix.py`
**用途**: 测试步骤跟踪器修复

---

### 📱 设备适配测试

#### `test_mac_adaptation.html`
**用途**: macOS 系统适配测试

#### `test_screenshot_data.py`
**用途**: 测试截图数据处理

---

### 🎨 UI 渲染测试

#### `test_markdown_rendering.html`
**用途**: Markdown 渲染测试

#### `test_nav.html`
**用途**: 导航栏测试

#### `test-task-history.html`
**用途**: 任务历史显示测试

---

## 🚀 快速运行

### 运行所有 Python 测试
```bash
cd test_scripts
for file in test_*.py; do
    echo "运行 $file..."
    python3 "$file"
done
```

### 运行特定测试
```bash
# 数据库连接测试
python3 test_supabase_connection.py

# 时间格式测试
python3 test_time_formatting.py
```

### 在浏览器中打开 HTML 测试
```bash
# macOS
open test_*.html

# Linux
xdg-open test_*.html

# Windows
start test_*.html
```

---

## 📝 注意事项

1. **环境要求**: 这些测试脚本需要在项目根目录下运行，以确保能正确导入依赖模块
2. **配置要求**: 某些测试需要配置 `.env` 文件（特别是数据库相关测试）
3. **清理**: HTML 测试文件可以安全删除，它们主要用于开发调试

---

## 🔧 维护建议

- 定期清理过时的测试脚本
- 为新功能添加相应的测试脚本
- 保持测试脚本的文档更新

---

*最后更新: 2025-01-31*
