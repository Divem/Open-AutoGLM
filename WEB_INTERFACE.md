# Phone Agent Web Interface

Phone Agent Web Interface 提供了一个现代化的 Web 界面，支持通过多轮对话进行手机自动化任务的下发和监控。

## 功能特性

### 🌐 Web 界面
- **现代化设计**: 基于 Bootstrap 5 的响应式界面
- **多轮对话**: 支持连续的对话交互
- **实时更新**: WebSocket 实时推送任务执行状态
- **截图显示**: 实时显示操作过程中的手机截图

### 🔧 配置管理
- **模型配置**: 支持本地和云端模型服务
- **设备管理**: 自动检测和管理 ADB 设备
- **预设配置**: 内置常用服务配置（本地模型、智谱BigModel、ModelScope）
- **参数调整**: 灵活的执行参数配置

### 📊 状态监控
- **执行状态**: 实时显示任务执行状态和进度
- **步骤跟踪**: 详细展示每个执行步骤的思考和动作
- **性能统计**: 显示执行步数、耗时等信息
- **错误处理**: 完善的错误提示和处理机制

## 快速开始

### 1. 安装依赖

```bash
# 安装 Web 界面依赖
pip install -r requirements-web.txt

# 或者直接安装核心依赖
pip install flask flask-socketio python-socketio eventlet requests
```

### 2. 启动 Web 服务

#### 使用启动脚本（推荐）

```bash
# 默认启动（端口 5000）
python web_start.py

# 指定端口
python web_start.py --port 8080

# 启用调试模式
python web_start.py --debug

# 跳过依赖检查
python web_start.py --skip-checks
```

#### 直接启动

```bash
cd web
python app.py --host 0.0.0.0 --port 5000
```

### 3. 访问 Web 界面

打开浏览器访问：http://localhost:5000

## 使用指南

### 主界面

主界面分为两个主要区域：

#### 左侧：对话区域
- **任务输入**: 在底部输入框中描述要执行的任务
- **对话历史**: 显示用户和助手的完整对话记录
- **实时更新**: 任务执行过程中的步骤和结果会实时显示

#### 右侧：状态面板
- **执行状态**: 显示当前任务状态、执行步数、耗时等
- **设备信息**: 显示连接的设备列表
- **实时截图**: 显示执行过程中的手机截图
- **支持的应用**: 列出支持的应用

### 配置界面

点击顶部的"配置"按钮进入配置界面：

#### 模型配置
- **服务地址**: 模型服务的 URL
- **模型名称**: 要使用的模型名称
- **API Key**: 认证密钥（如果需要）
- **语言设置**: 选择界面语言

#### 执行配置
- **最大步数**: 单个任务的最大执行步数
- **设备ID**: 指定使用的设备（留空自动检测）
- **详细输出**: 是否显示详细的执行过程

#### 脚本记录
- **启用记录**: 自动记录操作并生成脚本
- **输出目录**: 脚本保存的目录

### 预设配置

Web 界面提供了三个预设配置：

1. **本地模型**
   - 地址: `http://localhost:8000/v1`
   - 模型: `autoglm-phone-9b`
   - 无需 API Key

2. **智谱BigModel**
   - 地址: `https://open.bigmodel.cn/api/paas/v4`
   - 模型: `autoglm-phone`
   - 需要 API Key

3. **ModelScope**
   - 地址: `https://api-inference.modelscope.cn/v1`
   - 模型: `ZhipuAI/AutoGLM-Phone-9B`
   - 需要 API Key

## API 接口

Web 界面提供以下 REST API 接口：

### 会话管理
```http
POST /api/sessions
Content-Type: application/json

{
  "user_id": "web_user_123"
}
```

响应：
```json
{
  "session_id": "uuid-string",
  "created_at": "2024-01-01T12:00:00"
}
```

### 获取会话信息
```http
GET /api/sessions/{session_id}
```

### 配置管理
```http
GET /api/config
POST /api/config
Content-Type: application/json

{
  "name": "default",
  "base_url": "http://localhost:8000/v1",
  "model_name": "autoglm-phone-9b",
  "api_key": "EMPTY"
}
```

### 设备管理
```http
GET /api/devices
```

响应：
```json
[
  {
    "device_id": "emulator-5554",
    "connection_type": "usb",
    "model": "Android SDK built for x86"
  }
]
```

### 应用列表
```http
GET /api/apps
```

## WebSocket 事件

Web 界面使用 WebSocket 进行实时通信：

### 客户端事件
- `join_session`: 加入会话房间
- `send_task`: 发送任务执行请求
- `stop_task`: 停止当前任务

### 服务端事件
- `task_started`: 任务开始执行
- `step_update`: 步骤执行更新
- `task_completed`: 任务执行完成
- `task_error`: 任务执行错误
- `task_stopped`: 任务被停止

## 文件结构

```
web/
├── app.py                    # Flask 应用主文件
├── static/                   # 静态资源
│   ├── css/
│   │   └── style.css        # 界面样式
│   └── js/
│       ├── app.js           # 主界面 JavaScript
│       └── config.js        # 配置页面 JavaScript
└── templates/               # HTML 模板
    ├── index.html           # 主界面
    └── config.html          # 配置界面

web_start.py                 # 启动脚本
requirements-web.txt         # Web 依赖
```

## 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   # 升级 pip
   pip install --upgrade pip

   # 清理缓存重装
   pip cache purge
   pip install -r requirements-web.txt
   ```

2. **端口被占用**
   ```bash
   # 使用不同端口启动
   python web_start.py --port 8080
   ```

3. **ADB 设备未找到**
   - 确保 USB 调试已开启
   - 检查设备连接状态
   - 重新授权设备

4. **模型服务连接失败**
   - 检查模型服务是否正在运行
   - 验证服务地址和端口
   - 检查网络连接

5. **WebSocket 连接失败**
   - 检查防火墙设置
   - 确认端口没有被阻止
   - 刷新浏览器页面

### 调试模式

启用调试模式可以查看详细的日志信息：

```bash
python web_start.py --debug
```

调试模式下：
- 详细的错误堆栈信息
- 自动重载功能
- Flask 调试工具栏

### 日志查看

Web 界面的日志会输出到控制台，包括：
- 用户连接和断开
- 任务执行状态
- 错误信息
- 性能统计

## 高级配置

### 自定义主机和端口

```bash
python web/app.py --host 192.168.1.100 --port 8080
```

### 环境变量配置

可以通过环境变量配置默认参数：

```bash
export PHONE_AGENT_WEB_HOST=0.0.0.0
export PHONE_AGENT_WEB_PORT=5000
export PHONE_AGENT_WEB_DEBUG=false
```

### 反向代理配置

如果需要使用 Nginx 等反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 性能优化

### 生产环境部署

1. **使用 Gunicorn**：
   ```bash
   pip install gunicorn eventlet
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
   ```

2. **启用 HTTPS**：
   配置 SSL 证书和安全设置

3. **负载均衡**：
   使用多个 Worker 进程处理并发请求

### 资源优化

- 启用 gzip 压缩
- 设置静态文件缓存
- 优化图片和资源大小
- 使用 CDN 加速静态资源

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 Web 界面：

- 功能建议和需求
- Bug 报告和修复
- 界面优化和改进
- 性能优化建议

## 许可证

Web 界面遵循项目的原许可证。