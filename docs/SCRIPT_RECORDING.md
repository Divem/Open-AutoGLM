# Phone Agent 脚本记录功能

Phone Agent 现在支持脚本记录功能，可以在执行任务时自动记录所有操作并生成可重放的自动化脚本。

## 功能特性

### 📹 脚本记录
- **自动记录**: 在执行任务时自动记录所有操作步骤
- **详细信息**: 捕获操作类型、坐标、文本输入、思考过程等
- **截图保存**: 可选保存每个步骤的截图（如果可用）
- **执行结果**: 记录每个操作的成功/失败状态和错误信息

### 📄 脚本格式
- **JSON格式**: 保存结构化的脚本数据，包含元数据和步骤
- **Python脚本**: 自动生成可重放的Python脚本
- **元数据**: 包含任务名称、设备信息、执行时间、成功率等

### 🔄 重放功能
- **完整重放**: 可以精确重现录制的操作序列
- **可配置延迟**: 支持在操作之间添加延迟
- **错误处理**: 自动处理失败的步骤和异常情况
- **交互式控制**: 支持中断和继续执行

## 使用方法

### 命令行使用

#### 基本用法
```bash
# 启用脚本记录执行任务
python main.py --record-script "打开微信查看未读消息"

# 自定义脚本输出目录
python main.py --record-script --script-output-dir my_scripts "检查天气应用"

# 静默模式录制
python main.py --record-script --quiet "发送测试邮件"
```

#### 高级用法
```bash
# 结合其他参数使用
python main.py --record-script --device-id emulator-5554 --max-steps 50 "设置闹钟"

# 指定语言和模型
python main.py --record-script --lang cn --model autoglm-phone "导航到公司"
```

### 编程接口使用

```python
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

# 创建配置
model_config = ModelConfig(
    base_url="https://open.bigmodel.cn/api/paas/v4",
    model_name="autoglm-phone"
)

# 启用脚本记录
agent_config = AgentConfig(
    max_steps=100,
    device_id=None,
    verbose=True,
    record_script=True,  # 启用脚本记录
    script_output_dir="scripts"  # 输出目录
)

# 创建代理
agent = PhoneAgent(
    model_config=model_config,
    agent_config=agent_config
)

# 执行任务（自动记录）
result = agent.run("打开设置检查电池")

# 获取录制摘要
summary = agent.get_script_summary()
print(summary)
```

## 生成的文件

### JSON脚本格式
```json
{
  "metadata": {
    "task_name": "打开微信查看未读消息",
    "description": "打开微信查看未读消息",
    "created_at": "2025-12-13T13:30:00.000000",
    "total_steps": 5,
    "device_id": "4ABVB25327007599",
    "model_name": "autoglm-phone",
    "success_rate": 100.0,
    "execution_time": 12.5
  },
  "steps": [
    {
      "step_number": 1,
      "action_type": "Launch",
      "action_data": {
        "_metadata": "do",
        "action": "Launch",
        "app": "WeChat"
      },
      "thinking": "启动微信应用",
      "screenshot_path": "screenshots/step_001.png",
      "timestamp": "2025-12-13T13:30:01.000000",
      "success": true,
      "error_message": null
    }
  ]
}
```

### Python重放脚本
生成的Python脚本包含完整的重放逻辑：

```python
#!/usr/bin/env python3
# Auto-generated replay script

class ReplayScript:
    def replay(self, device_id=None, delay=1.0):
        # 显示任务信息
        self.print_info()

        # 重放每个步骤
        for i, step in enumerate(self.steps, 1):
            # 执行操作
            if action_name == 'Launch':
                launch_app(app_name, device_id)
            elif action_name == 'Tap':
                tap(x, y, device_id)
            # ... 其他操作

            # 延迟
            if delay > 0:
                time.sleep(delay)
```

## 重放脚本使用

### 运行重放脚本
```bash
# 基本用法
python scripts/your_task_replay.py scripts/your_task.json

# 或者直接运行（如果脚本在同一目录）
python scripts/your_task_replay.py
```

### 重放过程
1. **显示信息**: 显示任务详情和统计数据
2. **用户输入**: 询问设备ID和操作延迟
3. **逐步执行**: 按顺序重放每个操作
4. **实时反馈**: 显示当前执行步骤和结果
5. **错误处理**: 处理失败的操作和异常情况
6. **中断支持**: 支持用户中断执行

## 支持的操作类型

| 操作类型 | 说明 | 支持重放 |
|---------|------|---------|
| Launch | 启动应用 | ✅ |
| Tap | 点击操作 | ✅ |
| Type | 文本输入 | ✅ |
| Swipe | 滑动操作 | ✅ |
| Back | 返回键 | ✅ |
| Home | 主屏幕键 | ✅ |
| Double Tap | 双击 | ✅ |
| Long Press | 长按 | ✅ |
| Wait | 等待/延迟 | ✅ |

## 配置选项

### AgentConfig 参数
```python
AgentConfig(
    record_script=True,              # 启用脚本记录
    script_output_dir="scripts",     # 脚本输出目录
    # ... 其他参数
)
```

### 命令行参数
- `--record-script`: 启用脚本记录
- `--script-output-dir DIR`: 指定脚本输出目录

## 最佳实践

### 1. 任务设计
- 使用清晰、具体的任务描述
- 避免过于复杂的任务，可以分解为多个步骤
- 确保任务的可重复性

### 2. 脚本管理
- 定期清理旧的脚本文件
- 使用有意义的命名规则
- 备份重要的脚本

### 3. 重放优化
- 根据需要调整操作延迟
- 在不同设备上测试脚本兼容性
- 处理可能的异常情况

### 4. 错误处理
- 检查脚本的成功率
- 分析失败步骤的原因
- 必要时重新录制任务

## 故障排除

### 常见问题

1. **脚本生成失败**
   - 检查输出目录权限
   - 确保磁盘空间充足
   - 查看错误日志

2. **重放脚本执行失败**
   - 检查设备连接状态
   - 确认ADB键盘已安装
   - 验证坐标转换正确性

3. **操作不精确**
   - 调整操作延迟时间
   - 检查屏幕分辨率变化
   - 重新录制任务

### 调试技巧

```python
# 查看录制摘要
summary = agent.get_script_summary()
print(summary)

# 检查步骤详情
for step in agent.recorder.steps:
    print(f"步骤 {step.step_number}: {step.action_type}")
    print(f"思考: {step.thinking}")
    print(f"成功: {step.success}")
```

## 示例

完整的使用示例请参考：
- `examples/script_recording_demo.py` - 功能演示
- `test_script_recording.py` - 测试用例
- 生成的示例脚本文件在 `test_scripts/` 目录中

## 贡献

欢迎提交问题报告和功能建议！如果您想为脚本记录功能贡献代码：

1. Fork 项目仓库
2. 创建功能分支
3. 提交您的更改
4. 创建 Pull Request

## 许可证

本功能遵循项目的原有许可证。