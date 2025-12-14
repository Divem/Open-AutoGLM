# Design: Web界面实时截图传输机制

## 架构概述

```
┌──────────────────────────────────────────────────────────┐
│                    Phone Agent Backend                    │
│                                                            │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │             │   │              │   │              │  │
│  │    ADB      │──▶│  Screenshot  │──▶│   Save to    │  │
│  │  Screencap  │   │  Processing  │   │     File     │  │
│  │             │   │              │   │              │  │
│  └─────────────┘   └──────────────┘   └───────┬──────┘  │
│                                                │          │
│                                                │          │
│                                                ▼          │
│                                        ┌──────────────┐  │
│                                        │   Filename   │  │
│                                        │    Only      │  │
│                                        └───────┬──────┘  │
└────────────────────────────────────────────────┼─────────┘
                                                 │
                            Socket.IO            │ (~50 bytes)
                         step_update event       │
                                                 │
                                                 ▼
┌────────────────────────────────────────────────┼─────────┐
│                                                │          │
│                    Web Frontend                │          │
│                                                │          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────▼──────┐  │
│  │              │   │              │   │             │  │
│  │  Receive     │◀──│  HTTP GET    │◀──│  Construct  │  │
│  │  Image       │   │  Request     │   │  Image URL  │  │
│  │              │   │              │   │             │  │
│  └──────┬───────┘   └──────────────┘   └─────────────┘  │
│         │                                                 │
│         ▼                                                 │
│  ┌──────────────┐                                        │
│  │   Display    │                                        │
│  │  Screenshot  │                                        │
│  │              │                                        │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ HTTP GET /screenshots/<filename>
                         │ (~500KB-2MB)
                         │
┌────────────────────────┼─────────────────────────────────┐
│                        │                                  │
│              Flask Static File Server                     │
│                        │                                  │
│              web/static/screenshots/                      │
│                                                            │
│  screenshot_20251213_221530_abc123.png                    │
│  screenshot_20251213_221532_def456.png                    │
│  screenshot_20251213_221535_ghi789.png                    │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

## 核心设计决策

### 1. 文件存储而非内存传输

**决策**: 将截图保存为文件,通过HTTP GET请求获取,而不是通过Socket.IO传输完整数据。

**理由**:
- Socket.IO消息体积从~500KB-2MB降至~50字节
- 不阻塞实时通信通道
- HTTP GET有完善的缓存和压缩支持
- 支持浏览器原生图片优化

**权衡**:
- ✅ 性能: 大幅降低Socket.IO负载
- ✅ 可扩展性: 支持CDN和反向代理
- ❌ 磁盘I/O: 增加文件读写操作(但影响极小)
- ❌ 存储: 需要管理临时文件

### 2. 文件命名策略

**格式**: `screenshot_{timestamp}_{uuid}.png`

**示例**: `screenshot_20251213_221530_a1b2c3d4.png`

**组成部分**:
- `timestamp`: YYYYMMDD_HHMMSS格式,便于排序和清理
- `uuid`: 短UUID(8字符),确保并发安全
- 扩展名: 固定为`.png`(暂不支持其他格式)

**优点**:
- 时间戳支持自然排序
- UUID防止并发冲突
- 文件名包含足够上下文信息
- 易于实现基于时间的清理策略

### 3. 文件生命周期管理

```
创建 → 使用 → 清理
 │      │      │
 │      │      └─ 自动: 1小时后删除
 │      │      └─ 手动: session结束时删除(可选)
 │      │
 │      └─ 通过HTTP GET访问
 │      └─ 可被多个客户端访问(共享链接)
 │
 └─ 每个step生成一个文件
 └─ 保存在web/static/screenshots/
```

**清理策略**:
- **默认策略**: 1小时后自动删除
- **会话策略**: session结束时立即删除(可选,暂不实现)
- **存储限制**: 超过磁盘限制时删除最旧的文件(可选,未来)

**实现**:
```python
# 后台定时任务(每10分钟运行)
def cleanup_old_screenshots():
    cutoff_time = datetime.now() - timedelta(hours=1)
    screenshots_dir = Path('web/static/screenshots')

    for file in screenshots_dir.glob('screenshot_*.png'):
        # 从文件名解析时间戳
        try:
            timestamp_str = file.stem.split('_')[1] + file.stem.split('_')[2]
            file_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')

            if file_time < cutoff_time:
                file.unlink()
                logger.debug(f"Deleted old screenshot: {file.name}")
        except Exception as e:
            logger.warning(f"Failed to parse or delete {file.name}: {e}")
```

## 数据流详解

### 步骤1: 截图捕获 (PhoneAgent)

```python
# phone_agent/agent.py:_step()

# 1. 获取截图对象
screenshot = self.adb.get_screenshot(self.agent_config.device_id)
# screenshot.base64_data: str (完整base64字符串, ~500KB-2MB)
# screenshot.width: int
# screenshot.height: int
```

### 步骤2: 文件保存 (新增逻辑)

```python
# phone_agent/agent.py:_step()

import base64
from pathlib import Path
from datetime import datetime
import uuid

def save_screenshot_to_file(screenshot: Screenshot, save_dir: Path) -> Optional[str]:
    """
    Save screenshot to file and return filename.

    Returns:
        filename (e.g. 'screenshot_20251213_221530_a1b2c3d4.png') or None if failed
    """
    if not screenshot or not screenshot.base64_data:
        return None

    try:
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        short_uuid = uuid.uuid4().hex[:8]
        filename = f"screenshot_{timestamp}_{short_uuid}.png"

        # Decode base64 and save
        filepath = save_dir / filename
        image_data = base64.b64decode(screenshot.base64_data)
        filepath.write_bytes(image_data)

        return filename
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return None

# 使用
save_dir = Path(__file__).parent.parent / 'web' / 'static' / 'screenshots'
filename = save_screenshot_to_file(screenshot, save_dir)
```

### 步骤3: Socket.IO传输

```python
# phone_agent/agent.py:_step()

if step_callback:
    step_data = {
        'step_number': self._step_count,
        'thinking': response.thinking,
        'action': action,
        'result': result,
        'screenshot': filename,  # 只传文件名!
        'success': result.success,
        'finished': finished
    }
    step_callback(step_data)
```

**Socket.IO消息示例**:
```json
{
  "event": "step_update",
  "data": {
    "session_id": "abc-123",
    "step": {
      "step_number": 3,
      "thinking": "需要点击设置图标",
      "action": {"action_type": "tap", "coordinate": [100, 200]},
      "result": {"success": true, "message": "已点击"},
      "screenshot": "screenshot_20251213_221530_a1b2c3d4.png",
      "success": true,
      "finished": false
    },
    "task_id": "task-456",
    "timestamp": "2025-12-13T22:15:30.123Z"
  }
}
```

**消息体积**: ~500字节 (vs 原方案的500KB+)

### 步骤4: 前端接收和显示

```javascript
// web/static/js/app.js

onStepUpdate(data) {
    const step = data.step;

    // Update screenshot
    if (step.screenshot) {
        this.updateScreenshot(step.screenshot);
    }
}

updateScreenshot(screenshotData) {
    const container = document.getElementById('screenshot-container');

    let imageSrc;

    // 检测数据格式
    if (screenshotData.startsWith('data:image/')) {
        // Base64 data URL (向后兼容)
        imageSrc = screenshotData;
    } else {
        // 文件名 (新格式)
        imageSrc = `/screenshots/${screenshotData}`;
    }

    // 更新DOM
    container.innerHTML = `
        <div class="screenshot-preview">
            <img src="${imageSrc}"
                 alt="操作截图"
                 class="img-fluid"
                 onerror="this.style.display='none';">
        </div>
    `;
}
```

**HTTP GET请求**:
```
GET /screenshots/screenshot_20251213_221530_a1b2c3d4.png HTTP/1.1
Host: localhost:5001
Accept: image/png,image/*,*/*;q=0.8
```

### 步骤5: Flask静态文件服务

```python
# web/app.py

@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    """Serve screenshot files"""
    # 已有实现,无需修改
    return send_from_directory(app.config['SCREENSHOTS_FOLDER'], filename)
```

## 错误处理策略

### 场景1: 截图捕获失败

```python
# phone_agent/adb/screenshot.py 已处理

# 返回黑屏fallback
return Screenshot(
    base64_data=black_image_base64,
    width=1080,
    height=2400,
    is_sensitive=True
)
```

**策略**: 保存fallback截图,前端正常显示黑屏(用户可识别)

### 场景2: 文件保存失败

**原因**:
- 磁盘空间不足
- 权限问题
- I/O错误

**处理**:
```python
def save_screenshot_to_file(...) -> Optional[str]:
    try:
        # ...保存逻辑
        return filename
    except OSError as e:
        if e.errno == errno.ENOSPC:
            logger.error("Disk full, cannot save screenshot")
        elif e.errno == errno.EACCES:
            logger.error("Permission denied, cannot save screenshot")
        else:
            logger.error(f"Failed to save screenshot: {e}")
        return None
```

**降级策略**:
- `screenshot`字段设为None
- 前端显示"截图不可用"消息
- 任务继续执行(不影响核心功能)

### 场景3: 前端加载失败

**触发条件**:
- 文件被提前删除
- 网络错误
- 权限问题

**处理**:
```javascript
<img src="/screenshots/xxx.png"
     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
<div style="display:none;" class="error-message">
    截图加载失败
</div>
```

## 性能优化

### 1. 文件I/O优化

**问题**: 每个步骤都要写文件,是否会影响性能?

**分析**:
- 文件大小: 100KB-500KB (PNG格式)
- 写入时间: <50ms (SSD), <100ms (HDD)
- 频率: 每步骤一次,通常每5-10秒

**结论**: 影响可忽略,远低于网络传输和ADB通信开销

**优化**:
- 使用缓冲I/O (Python默认)
- 异步写入 (可选,未来)

### 2. Socket.IO性能

**优化前** (完整base64):
- 消息体积: 500KB-2MB
- 编码/解码开销: 高
- 网络传输: 慢(特别是移动网络)

**优化后** (文件名):
- 消息体积: ~50字节
- 编码/解码开销: 极低
- 网络传输: 快

**提升**: ~10,000倍体积减少

### 3. HTTP缓存

**Cache-Control**: 前端可以缓存截图(可选)

```python
@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    response = send_from_directory(app.config['SCREENSHOTS_FOLDER'], filename)
    # 短期缓存(5分钟)
    response.headers['Cache-Control'] = 'public, max-age=300'
    return response
```

## 安全考虑

### 1. 路径遍历防护

**威胁**: 恶意客户端请求 `/screenshots/../../../etc/passwd`

**防护**:
```python
from werkzeug.security import safe_join

@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    # Flask的send_from_directory已内置safe_join
    # 会自动拒绝包含'..'的路径
    return send_from_directory(app.config['SCREENSHOTS_FOLDER'], filename)
```

### 2. 文件名验证

```python
import re

def validate_screenshot_filename(filename: str) -> bool:
    """验证文件名格式"""
    pattern = r'^screenshot_\d{8}_\d{6}_[a-f0-9]{8}\.png$'
    return bool(re.match(pattern, filename))
```

### 3. 磁盘配额

**问题**: 恶意用户大量创建任务,填满磁盘

**缓解**:
- 实现自动清理(1小时)
- 监控磁盘使用率
- 限制并发任务数量
- 设置最大文件数量限制

## 向后兼容性

**目标**: 支持base64和文件名两种格式

**前端检测逻辑**:
```javascript
function getImageSrc(screenshotData) {
    if (!screenshotData) return null;

    // Base64 data URL
    if (screenshotData.startsWith('data:image/')) {
        return screenshotData;
    }

    // Base64 string without prefix
    if (screenshotData.length > 1000) {
        return `data:image/png;base64,${screenshotData}`;
    }

    // Filename (new format)
    return `/screenshots/${screenshotData}`;
}
```

**后端兼容**:
- 继续支持base64格式的历史数据
- 新数据统一使用文件名格式

## 测试策略

### 单元测试

```python
def test_save_screenshot_to_file():
    # 创建测试截图
    test_screenshot = Screenshot(
        base64_data=base64.b64encode(b"fake_png_data").decode(),
        width=1080,
        height=2400
    )

    # 保存
    filename = save_screenshot_to_file(test_screenshot, tmp_dir)

    # 验证
    assert filename is not None
    assert re.match(r'screenshot_\d{8}_\d{6}_[a-f0-9]{8}\.png', filename)
    assert (tmp_dir / filename).exists()
```

### 集成测试

```python
def test_realtime_screenshot_display(web_client, adb_device):
    # 1. 启动任务
    response = web_client.emit('start_task', {
        'session_id': 'test-session',
        'task': '打开设置'
    })

    # 2. 等待step_update事件
    events = web_client.get_received('step_update')
    assert len(events) > 0

    # 3. 验证截图字段
    step = events[0]['step']
    assert step['screenshot'] is not None
    assert step['screenshot'].startswith('screenshot_')

    # 4. 验证文件存在
    filepath = Path('web/static/screenshots') / step['screenshot']
    assert filepath.exists()

    # 5. 验证HTTP访问
    response = web_client.get(f"/screenshots/{step['screenshot']}")
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'image/png'
```

### 性能测试

```python
def test_screenshot_performance():
    # 测试100次截图保存
    times = []
    for _ in range(100):
        start = time.time()
        filename = save_screenshot_to_file(screenshot, save_dir)
        elapsed = time.time() - start
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    assert avg_time < 0.05, f"Average save time {avg_time}s exceeds 50ms"
```

## 未来优化方向

1. **WebSocket Binary Frames**: 直接传输二进制数据,跳过base64编码
2. **WebP格式**: 更高压缩率,减小文件体积30-50%
3. **懒加载**: 只在用户滚动到可视区域时加载截图
4. **缩略图**: 实时传输小缩略图,点击加载完整图片
5. **CDN集成**: 对于公开demo,使用CDN加速
6. **视频流**: 长时间任务考虑使用视频流代替静态截图
