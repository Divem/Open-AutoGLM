# Spec: Realtime Screenshot Delivery

## ADDED Requirements

### Requirement: File-Based Screenshot Transmission
实时截图传输 **SHALL** 使用文件存储和HTTP GET方式,而非通过Socket.IO传输完整数据。

#### Scenario: Save screenshot to file during task execution
- **WHEN** PhoneAgent执行任务步骤并捕获截图
- **THEN** 截图**SHALL**保存为PNG文件到`web/static/screenshots/`目录
- **AND** 文件名**SHALL**使用格式`screenshot_{timestamp}_{uuid}.png`
- **AND** `step_callback`的`screenshot`字段**SHALL**包含文件名(不是完整路径或base64数据)
- **AND** 文件保存失败时**SHALL**返回None,不中断任务执行

#### Scenario: Frontend loads screenshot via HTTP GET
- **WHEN** 前端收到`step_update`事件且`screenshot`字段为文件名
- **THEN** 前端**SHALL**构造URL `/screenshots/{filename}`
- **AND** 通过HTTP GET请求加载图片
- **AND** 显示在"实时截图"区域
- **AND** 图片加载失败时**SHALL**显示友好的错误提示

#### Scenario: Socket.IO message size is minimized
- **WHEN** 发送`step_update`事件
- **THEN** `screenshot`字段大小**SHALL**<100字节(仅文件名)
- **AND** 完整Socket.IO消息大小**SHALL**<5KB
- **AND** 不包含base64图片数据

### Requirement: Backwards Compatibility
系统 **SHALL** 同时支持文件名和base64两种截图格式。

#### Scenario: Frontend detects screenshot data format
- **WHEN** 前端收到`screenshot`字段
- **THEN** 如果以`data:image/`开头,**SHALL**作为base64 data URL处理
- **AND** 如果长度>1000且包含base64特征,**SHALL**添加data URL前缀
- **AND** 否则**SHALL**作为文件名处理,构造`/screenshots/{filename}` URL

#### Scenario: Legacy base64 screenshots still work
- **WHEN** 后端发送base64格式的截图数据(向后兼容)
- **THEN** 前端**SHALL**正确识别并显示
- **AND** 不抛出JavaScript错误

### Requirement: Screenshot File Lifecycle Management
截图文件 **SHALL** 自动管理生命周期,防止磁盘空间耗尽。

#### Scenario: Automatically cleanup old screenshots
- **WHEN** 截图文件创建超过1小时
- **THEN** 后台定时任务**SHALL**自动删除该文件
- **AND** 清理过程**SHALL**不影响应用性能
- **AND** 活动session的截图**SHOULD**被保留(可选优化)

#### Scenario: Handle disk space exhaustion gracefully
- **WHEN** 磁盘空间不足无法保存截图
- **THEN** **SHALL**捕获`OSError`异常
- **AND** 记录ERROR级别日志
- **AND** 返回None给`step_callback`
- **AND** 任务继续执行,不崩溃

#### Scenario: Screenshots directory is automatically created
- **WHEN** 应用启动
- **THEN** **SHALL**检查`web/static/screenshots/`目录是否存在
- **AND** 如果不存在**SHALL**自动创建
- **AND** 启动日志**SHALL**显示目录状态

### Requirement: Filename Uniqueness and Security
截图文件名 **SHALL** 确保唯一性和安全性。

#### Scenario: Generate unique screenshot filename
- **WHEN** 保存新截图
- **THEN** 文件名**SHALL**包含时间戳(格式`YYYYMMDD_HHMMSS`)
- **AND** **SHALL**包含8字符的随机UUID
- **AND** 完整格式**SHALL**为`screenshot_{timestamp}_{uuid}.png`
- **AND** 并发保存时**SHALL**不产生文件名冲突

#### Scenario: Prevent path traversal attacks
- **WHEN** HTTP请求访问`/screenshots/<filename>`
- **THEN** Flask的`send_from_directory`**SHALL**自动拒绝包含`..`的路径
- **AND** 只允许访问`web/static/screenshots/`目录下的文件
- **AND** 路径遍历尝试**SHALL**返回404或403错误

#### Scenario: Validate screenshot filename format
- **WHEN** 接收到截图文件名
- **THEN** **SHOULD**验证格式匹配正则`^screenshot_\d{8}_\d{6}_[a-f0-9]{8}\.png$`
- **AND** 非法格式**SHOULD**被拒绝或记录警告

### Requirement: Error Handling and Resilience
截图功能 **SHALL** 具备完善的错误处理,不影响核心任务执行。

#### Scenario: Handle screenshot capture failure
- **WHEN** ADB截图捕获失败(例如敏感屏幕)
- **THEN** PhoneAgent**SHALL**返回黑屏fallback Screenshot对象
- **AND** `is_sensitive`标志**SHALL**设置为True
- **AND** 黑屏截图**SHALL**正常保存和显示

#### Scenario: Handle file write permission errors
- **WHEN** 截图目录没有写权限
- **THEN** **SHALL**捕获`PermissionError`
- **AND** 记录ERROR级别日志
- **AND** 返回None,任务继续执行

#### Scenario: Frontend handles missing screenshot gracefully
- **WHEN** 前端尝试加载截图但文件已被删除
- **THEN** `<img>`标签的`onerror`事件**SHALL**触发
- **AND** **SHALL**隐藏图片元素
- **AND** **SHALL**显示"截图不可用"或"截图加载失败"消息
- **AND** 不抛出JavaScript错误

### Requirement: Performance Monitoring
系统 **SHALL** 监控截图功能的性能指标。

#### Scenario: Monitor screenshot save performance
- **WHEN** 保存截图文件
- **THEN** 文件I/O操作**SHALL**在50ms内完成(SSD环境)
- **AND** 超过阈值时**SHOULD**记录WARNING日志

#### Scenario: Monitor screenshot update latency
- **WHEN** 从截图捕获到前端显示
- **THEN** 端到端延迟**SHALL**<2秒(正常网络环境)
- **AND** **SHOULD**在日志中记录各阶段耗时(捕获/保存/传输/加载)

#### Scenario: Socket.IO message size is tracked
- **WHEN** 发送`step_update`事件
- **THEN** 消息大小**SHOULD**被记录到DEBUG日志
- **AND** 超过5KB时**SHOULD**记录WARNING

### Requirement: Static File Serving
Flask静态文件服务 **SHALL** 正确配置以支持截图访问。

#### Scenario: Serve screenshot files via HTTP GET
- **WHEN** 客户端请求`GET /screenshots/{filename}`
- **THEN** Flask**SHALL**返回对应的PNG文件
- **AND** `Content-Type`**SHALL**为`image/png`
- **AND** 文件不存在时**SHALL**返回404
- **AND** 响应**SHOULD**包含适当的Cache-Control头(可选)

#### Scenario: Screenshots directory is configured correctly
- **WHEN** Flask应用初始化
- **THEN** `app.config['SCREENSHOTS_FOLDER']`**SHALL**指向`web/static/screenshots/`
- **AND** 路由`/screenshots/<path:filename>`**SHALL**正确注册

## MODIFIED Requirements

无(这是新增功能,不修改现有需求)

## REMOVED Requirements

无
