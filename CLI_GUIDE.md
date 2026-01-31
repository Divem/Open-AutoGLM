# Open-AutoGLM 命令行使用指南

本文档详细说明如何通过命令行使用 Open-AutoGLM。

## 📋 目录

- [快速开始](#快速开始)
- [基础命令](#基础命令)
- [完整参数列表](#完整参数列表)
- [使用场景](#使用场景)
- [环境变量配置](#环境变量配置)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 最简单的用法（交互模式）

```bash
python3 main.py
```

这将进入交互模式，你可以逐个输入任务。

### 2. 单次任务执行

```bash
# 使用本地模型
python3 main.py --base-url http://localhost:8000/v1 "打开微信查看未读消息"

# 使用智谱 BigModel
python3 main.py --base-url https://open.bigmodel.cn/api/paas/v4 \
  --model autoglm-phone \
  --apikey "your-api-key" \
  "打开抖音搜索美食攻略"
```

---

## 📚 基础命令

### 查看帮助

```bash
python3 main.py --help
```

### 列出支持的应用

```bash
python3 main.py --list-apps
```

输出示例：
```
支持的应用列表：
社交通讯: 微信, QQ, 微博, 钉钉
电商购物: 淘宝, 京东, 拼多多, 唯品会
美食外卖: 美团, 饿了么, 大众点评
...
```

### 查看已连接的设备

```bash
python3 main.py --list-devices
```

输出示例：
```
Connected devices:
------------------------------------------------------------
  ✓ 4ABVB25327007599           [usb] (Mi 11)
  ✓ 192.168.1.100:5555         [wifi] (Pixel 5)
```

---

## 🔧 完整参数列表

### 模型配置参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--base-url` | - | 模型 API 地址 | `http://localhost:8000/v1` |
| `--model` | - | 模型名称 | `autoglm-phone-9b` |
| `--apikey` | - | API 认证密钥 | `EMPTY` |
| `--max-steps` | - | 每个任务最大步数 | `100` |

**示例**：
```bash
# 使用本地模型
python3 main.py --base-url http://localhost:8000/v1 --model autoglm-phone-9b "打开设置"

# 使用智谱 BigModel
python3 main.py \
  --base-url https://open.bigmodel.cn/api/paas/v4 \
  --model autoglm-phone \
  --apikey "your-api-key" \
  "打开淘宝"
```

### 设备管理参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--device-id` | `-d` | 指定 ADB 设备 ID | `--device-id emulator-5554` |
| `--connect` | `-c` | 连接远程设备 | `--connect 192.168.1.100:5555` |
| `--disconnect` | - | 断开远程设备 | `--disconnect all` |
| `--list-devices` | - | 列出已连接设备 | `--list-devices` |
| `--enable-tcpip` | - | 在 USB 设备上启用 TCP/IP | `--enable-tcpip 5555` |

**示例**：
```bash
# 列出所有设备
python3 main.py --list-devices

# 连接远程设备
python3 main.py --connect 192.168.1.100:5555

# 在指定设备上执行任务
python3 main.py --device-id emulator-5554 "打开微信"

# 启用 TCP/IP 调试（通过 USB）
python3 main.py --enable-tcpip

# 断开所有远程连接
python3 main.py --disconnect all
```

### 其他配置参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--lang` | - | 系统提示语言 (cn/en) | `cn` |
| `--quiet` | `-q` | 静默模式，不输出详细信息 | `False` |
| `--record-script` | - | 启用脚本记录功能 | `False` |
| `--script-output-dir` | - | 脚本输出目录 | `scripts` |

**示例**：
```bash
# 使用英文界面
python3 main.py --lang en "Open Chrome browser"

# 静默模式
python3 main.py --quiet "打开设置"

# 启用脚本记录
python3 main.py --record-script "打开微信查看未读消息"

# 自定义脚本输出目录
python3 main.py --record-script --script-output-dir my_scripts "检查天气"
```

---

## 💡 使用场景

### 场景 1: 使用本地部署的模型

```bash
# 1. 启动本地模型服务（假设已在 8000 端口）
# 2. 运行任务
python3 main.py --base-url http://localhost:8000/v1 "打开微信发消息"
```

### 场景 2: 使用智谱 BigModel（推荐）

```bash
# 配置环境变量（或使用 .env 文件）
export PHONE_AGENT_API_KEY="your-bigmodel-api-key"

# 执行任务
python3 main.py \
  --base-url https://open.bigmodel.cn/api/paas/v4 \
  --model autoglm-phone \
  "打开美团搜索附近的火锅店"
```

### 场景 3: 远程设备控制

```bash
# 1. 启用设备的 TCP/IP 调试
python3 main.py --enable-tcpip

# 2. 连接到设备（手机和电脑在同一 WiFi）
python3 main.py --connect 192.168.1.100:5555

# 3. 在远程设备上执行任务
python3 main.py --device-id 192.168.1.100:5555 "打开抖音"
```

### 场景 4: 脚本记录与重放

```bash
# 记录任务执行过程
python3 main.py --record-script "打开设置调整音量到最大"

# 查看生成的脚本
ls scripts/
# 输出: 20251213_133613_打开设置调整音量到最大.json
#       20251213_133613_打开设置调整音量到最大_replay.py

# 重放脚本
python3 scripts/20251213_133613_打开设置调整音量到最大_replay.py
```

### 场景 5: 多设备管理

```bash
# 查看所有连接的设备
python3 main.py --list-devices

# 在设备 1 上执行任务
python3 main.py --device-id 4ABVB25327007599 "打开微信"

# 在设备 2 上执行任务
python3 main.py --device-id 192.168.1.100:5555 "打开淘宝"
```

### 场景 6: 交互模式

```bash
# 进入交互模式
python3 main.py

# 然后逐个输入任务：
# > 打开微信
# > 查看未读消息
# > 返回
# > 打开抖音
# > 搜索美食攻略
# > exit
```

---

## ⚙️ 环境变量配置

你可以通过环境变量或 `.env` 文件配置默认值，避免每次都输入参数。

### 方法 1: 使用 .env 文件（推荐）

在项目根目录创建 `.env` 文件：

```bash
# 模型配置
PHONE_AGENT_BASE_URL=https://open.bigmodel.cn/api/paas/v4
PHONE_AGENT_MODEL=autoglm-phone
PHONE_AGENT_API_KEY=your-api-key-here
PHONE_AGENT_MAX_STEPS=100

# 设备配置
PHONE_AGENT_DEVICE_ID=4ABVB25327007599

# 语言配置
PHONE_AGENT_LANG=cn

# 脚本记录
PHONE_AGENT_RECORD_SCRIPT=false
PHONE_AGENT_SCRIPT_OUTPUT_DIR=scripts
```

然后直接运行：
```bash
python3 main.py "打开微信"
```

### 方法 2: 命令行导出环境变量

```bash
export PHONE_AGENT_BASE_URL=https://open.bigmodel.cn/api/paas/v4
export PHONE_AGENT_MODEL=autoglm-phone
export PHONE_AGENT_API_KEY=your-api-key

python3 main.py "打开淘宝"
```

### 环境变量优先级

命令行参数 > 环境变量 > 默认值

示例：
```bash
# .env 中设置了 BASE_URL=http://localhost:8000/v1
# 但命令行指定了不同的 URL
python3 main.py --base-url https://open.bigmodel.cn/api/paas/v4 "打开微信"
# 实际使用: https://open.bigmodel.cn/api/paas/v4
```

---

## 🎯 实战示例

### 电商比价

```bash
# 在京东搜索商品
python3 main.py "打开京东搜索 iPhone 15"

# 在淘宝搜索同一商品
python3 main.py "打开淘宝搜索 iPhone 15"
```

### 日常任务

```bash
# 发送微信消息
python3 main.py "打开微信给张三发送消息：今晚一起吃饭"

# 查看天气
python3 main.py "打开天气应用查看北京今天的天气"

# 设置闹钟
python3 main.py "打开时钟应用设置明天早上7点的闹钟"
```

### 自动化测试

```bash
# 测试应用功能
python3 main.py --record-script --script-output-dir test_scripts \
  "测试微信的发送消息功能"

# 批量测试多个任务
for task in "打开微信" "打开淘宝" "打开抖音"; do
  echo "执行任务: $task"
  python3 main.py --quiet "$task"
done
```

---

## ❓ 常见问题

### Q1: 命令行模式和 Web 界面哪个更好？

**A**: 各有优势：
- **命令行模式**: 适合自动化脚本、批量任务、远程 SSH 操作
- **Web 界面**: 适合日常使用、实时监控、查看执行报告

### Q2: 如何查看详细的执行过程？

**A**: 去掉 `--quiet` 参数（默认就是详细模式）：
```bash
python3 main.py "打开微信"
```

### Q3: 任务执行失败怎么办？

**A**: 检查以下几点：
1. 设备是否正确连接: `python3 main.py --list-devices`
2. ADB Keyboard 是否已安装
3. 模型服务是否正常
4. 网络连接是否正常

### Q4: 可以在脚本中使用吗？

**A**: 可以！示例：
```bash
#!/bin/bash
# auto_task.sh

python3 main.py --quiet "打开微信查看未读消息"
python3 main.py --quiet "打开邮件应用检查新邮件"
python3 main.py --quiet "打开日历查看今天的日程"
```

### Q5: 如何同时控制多个设备？

**A**:
```bash
# 在不同终端中运行
# 终端 1:
python3 main.py --device-id device1 "打开微信"

# 终端 2:
python3 main.py --device-id device2 "打开淘宝"
```

### Q6: 支持后台运行吗？

**A**: 支持，使用 nohup：
```bash
nohup python3 main.py "长时间任务" > task.log 2>&1 &
```

---

## 📖 更多资源

- [项目主 README](../README.md)
- [Web 界面使用指南](../README.md#-web-界面使用指南推荐方式)
- [脚本记录功能](../README.md#-脚本记录与重放)
- [远程调试配置](../README.md#远程调试)

---

## 💻 命令速查表

```bash
# 基础用法
python3 main.py "任务描述"

# 查看帮助
python3 main.py --help

# 列出设备
python3 main.py --list-devices

# 列出应用
python3 main.py --list-apps

# 连接远程设备
python3 main.py --connect 192.168.1.100:5555

# 指定设备执行
python3 main.py --device-id xxx "打开微信"

# 使用特定模型
python3 main.py --base-url URL --model NAME "打开微信"

# 启用脚本记录
python3 main.py --record-script "任务描述"

# 静默模式
python3 main.py --quiet "任务描述"

# 英文界面
python3 main.py --lang en "Open Chrome"
```

---

*最后更新: 2025-01-31*
