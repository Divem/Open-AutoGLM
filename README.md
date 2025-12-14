# Open-AutoGLM

[Readme in English](README_en.md)

<div align="center">
<img src=resources/logo.svg width="20%"/>
</div>
<p align="center">
    👋 加入我们的 <a href="resources/WECHAT.md" target="_blank">微信</a> 社区
</p>
<p align="center">
    🎤 进一步在我们的产品 <a href="https://autoglm.zhipuai.cn/autotyper/" target="_blank">智谱 AI 输入法</a> 体验“用嘴发指令”
</p>

## 懒人版快速安装

你可以使用Claude Code，配置 [GLM Coding Plan](https://bigmodel.cn/glm-coding) 后，输入以下提示词，快速部署本项目。

```
访问文档，为我安装 AutoGLM
https://raw.githubusercontent.com/zai-org/Open-AutoGLM/refs/heads/main/README.md
```

## 🌐 Web 界面使用指南（推荐方式）

Open-AutoGLM 提供了现代化的 Web 界面，让手机自动化变得像聊天一样简单。

### 快速启动

#### 1. 启动 Web 服务

```bash
# 使用启动脚本（推荐）
python web_start.py

# 指定端口启动
python web_start.py --port 8080
```

#### 2. 访问界面

打开浏览器访问：**http://localhost:5000**

### 主要功能

#### 🗣️ 对话式交互
- 在底部输入框描述任务，如："打开小红书搜索美食攻略"
- 支持多轮对话，可以连续提出多个任务
- 实时显示任务执行状态和结果

#### 📱 设备管理
- 自动检测已连接的 ADB 设备
- 实时显示设备连接状态
- 支持远程 WiFi 连接设备

#### 📸 实时监控
- **状态面板**: 显示当前任务状态、执行步数、耗时
- **截图预览**: 实时显示操作过程中的手机截图
- **执行历史**: 查看之前的任务记录和结果

#### ⚙️ 配置管理
- **模型配置**: 支持本地模型、智谱BigModel、ModelScope
- **设备设置**: 选择特定设备或自动检测
- **执行参数**: 调整最大步数、详细输出等

### 界面布局

```
┌─────────────────────────────────┬─────────────────────────────────┐
│                                 │                                 │
│         对话区域                 │         状态面板                 │
│   ┌─────────────────────────┐   │   ┌─────────────────────────┐   │
│   │     历史对话记录         │   │   │     执行状态             │   │
│   │                         │   │   │     设备信息             │   │
│   │                         │   │   │     实时截图             │   │
│   └─────────────────────────┘   │   └─────────────────────────┘   │
│                                 │                                 │
│   ┌─────────────────────────┐   │                                 │
│   │   任务输入框 [发送]     │   │                                 │
│   └─────────────────────────┘   │                                 │
│                                 │                                 │
└─────────────────────────────────┴─────────────────────────────────┘
```

### 预设配置

Web 界面内置了三个预设配置：

1. **本地模型**: `http://localhost:8000/v1` (需要本地部署)
2. **智谱BigModel**: 直接使用，需要 API Key
3. **ModelScope**: 直接使用，需要 API Key

### 高级功能

#### 📊 任务执行报告
- 点击已完成任务的"报告"按钮
- 查看详细的执行时间线
- 回放每个步骤的截图和思考过程

#### 🔄 实时状态推送
- WebSocket 实时连接
- 任务状态实时更新
- 步骤执行进度实时显示

#### 💾 数据持久化
- 任务数据自动保存到云端数据库
- 截图文件上传到云存储
- 支持历史数据查询和分析

### 故障排除

**启动失败**:
```bash
# 检查依赖
pip install -r requirements-web.txt

# 检查端口占用
python web_start.py --port 8080
```

**设备连接问题**:
- 确保 USB 调试已开启
- 检查设备是否已授权
- 尝试重新连接设备

**模型连接失败**:
- 验证模型服务地址
- 检查 API Key 是否正确
- 确认网络连接正常

详细使用说明请参考：[Web Interface 文档](docs/WEB_INTERFACE.md)

## 项目介绍

Open-AutoGLM 是一个企业级手机自动化智能平台，基于先进的 AutoGLM 视觉语言模型构建。它能够以多模态方式理解手机屏幕内容，并通过自动化操作帮助用户完成复杂任务。

### 🌟 核心特性

#### 🌐 现代化 Web 界面
- **直观操作**: 基于 Bootstrap 5 的响应式 Web 界面
- **实时监控**: WebSocket 实时推送任务执行状态和进度
- **多轮对话**: 支持连续的对话交互，像聊天一样使用
- **截图预览**: 实时显示操作过程中的手机截图

#### ☁️ 云原生架构
- **Supabase 集成**: 云数据库存储，支持多设备访问
- **双重存储**: 本地 + 云端截图存储，确保数据安全
- **实时同步**: 任务数据跨设备实时同步
- **可观测性**: 详细的步骤跟踪和执行报告

#### 🤖 智能自动化
- **视觉理解**: 先进的多模态模型理解屏幕内容
- **智能规划**: 自动分解任务并生成执行步骤
- **50+ 应用支持**: 微信、淘宝、抖音等主流应用全覆盖
- **学习能力**: 支持复杂的多步骤任务执行

#### 📊 执行监控
- **步骤跟踪**: 详细记录每个执行步骤的思考和动作
- **性能分析**: 任务执行时间和成功率统计
- **错误诊断**: 完善的错误提示和处理机制
- **历史记录**: 完整的任务执行历史回放

### 💡 使用场景

- **日常效率**: 自动发送消息、查看天气、设置闹钟
- **电商比价**: 在多个平台间比较价格并自动下单
- **内容创作**: 自动发布社交媒体内容
- **数据收集**: 自动抓取应用数据并整理
- **测试自动化**: 移动应用的功能测试和回归测试

### 🚀 快速体验

1. **Web 界面（推荐）**:
   ```bash
   python web_start.py
   # 访问 http://localhost:5000
   ```

2. **命令行方式**:
   ```bash
   python main.py --base-url https://open.bigmodel.cn/api/paas/v4 --model autoglm-phone "打开微信查看未读消息"
   ```

> ⚠️
> 本项目仅供研究和学习使用。严禁用于非法获取信息、干扰系统或任何违法活动。请仔细审阅 [使用条款](resources/privacy_policy.txt)。

## 模型下载地址

| Model                         | Download Links                                                                                                                                                         |
|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AutoGLM-Phone-9B              | [🤗 Hugging Face](https://huggingface.co/zai-org/AutoGLM-Phone-9B)<br>[🤖 ModelScope](https://modelscope.cn/models/ZhipuAI/AutoGLM-Phone-9B)                           |
| AutoGLM-Phone-9B-Multilingual | [🤗 Hugging Face](https://huggingface.co/zai-org/AutoGLM-Phone-9B-Multilingual)<br>[🤖 ModelScope](https://modelscope.cn/models/ZhipuAI/AutoGLM-Phone-9B-Multilingual) |

其中，`AutoGLM-Phone-9B` 是针对中文手机应用优化的模型，而 `AutoGLM-Phone-9B-Multilingual` 支持英语场景，适用于包含英文等其他语言内容的应用。

## 环境准备

### 1. Python 环境

建议使用 Python 3.10 及以上版本。

### 2. ADB (Android Debug Bridge)

1. 下载官方 ADB [安装包](https://developer.android.com/tools/releases/platform-tools?hl=zh-cn)，并解压到自定义路径
2. 配置环境变量

- MacOS 配置方法：在 `Terminal` 或者任何命令行工具里

  ```bash
  # 假设解压后的目录为 ~/Downlaods/platform-tools。如果不是请自行调整命令。
  export PATH=${PATH}:~/Downloads/platform-tools
  ```

- Windows 配置方法：可参考 [第三方教程](https://blog.csdn.net/x2584179909/article/details/108319973) 进行配置。

### 3. Android 7.0+ 的设备或模拟器，并启用 `开发者模式` 和 `USB 调试`

1. 开发者模式启用：通常启用方法是，找到 `设置-关于手机-版本号` 然后连续快速点击 10
   次左右，直到弹出弹窗显示“开发者模式已启用”。不同手机会有些许差别，如果找不到，可以上网搜索一下教程。
2. USB 调试启用：启用开发者模式之后，会出现 `设置-开发者选项-USB 调试`，勾选启用
3. 部分机型在设置开发者选项以后, 可能需要重启设备才能生效. 可以测试一下: 将手机用USB数据线连接到电脑后, `adb devices`
   查看是否有设备信息, 如果没有说明连接失败.

**请务必仔细检查相关权限**

![权限](resources/screenshot-20251209-181423.png)

### 4. 安装 ADB Keyboard(用于文本输入)

下载 [安装包](https://github.com/senzhk/ADBKeyBoard/blob/master/ADBKeyboard.apk) 并在对应的安卓设备中进行安装。
注意，安装完成后还需要到 `设置-输入法` 或者 `设置-键盘列表` 中启用 `ADB Keyboard` 才能生效(或使用命令`adb shell ime enable com.android.adbkeyboard/.AdbIME`[How-to-use](https://github.com/senzhk/ADBKeyBoard/blob/master/README.md#how-to-use))

### 5. 云服务准备（可选，推荐）

为了获得完整功能体验，建议准备 Supabase 云服务：

#### Supabase 账号
1. 访问 [Supabase 官网](https://supabase.com) 注册账号
2. 创建新项目（推荐选择离你最近的区域）
3. 获取项目的 URL 和 Service Role Key

#### 功能说明
- ✅ **数据持久化**: 任务记录、执行步骤自动保存
- ✅ **云端截图**: 截图文件自动上传到云存储
- ✅ **跨设备同步**: 数据在多个设备间实时同步
- ✅ **历史分析**: 长期使用数据分析和报告

> 💡 **注意**: 如果暂不配置云服务，系统会自动降级到本地存储模式，核心功能不受影响。

## 部署准备工作

### 1. 安装基础依赖

```bash
# 安装核心依赖
pip install -r requirements.txt
pip install -e .

# 安装 Web 界面依赖（推荐）
pip install -r requirements-web.txt
```

> 💡 **提示**: `requirements-web.txt` 包含 Flask、WebSocket 等Web界面必需的依赖包。

### 2. 快速启动（推荐）

#### Web 界面方式
```bash
# 一键启动 Web 界面
python web_start.py

# 访问 http://localhost:5000 开始使用
```

#### 命令行方式
```bash
# 使用第三方服务（需要 API Key）
python main.py --base-url https://open.bigmodel.cn/api/paas/v4 --model autoglm-phone --apikey "your-api-key" "打开微信查看未读消息"
```

### 3. 配置 ADB

确认 **USB数据线具有数据传输功能**, 而不是仅有充电功能

确保已安装 ADB 并使用 **USB数据线** 连接设备：

```bash
# 检查已连接的设备
adb devices

# 输出结果应显示你的设备，如：
# List of devices attached
# emulator-5554   device
```

### 4. 启动模型服务

你可以选择自行部署模型服务，或使用第三方模型服务商。

#### 选项 A: 使用第三方模型服务

如果你不想自行部署模型，可以使用以下已部署我们模型的第三方服务：

**1. 智谱 BigModel**

- 文档: https://docs.bigmodel.cn/cn/api/introduction
- `--base-url`: `https://open.bigmodel.cn/api/paas/v4`
- `--model`: `autoglm-phone`
- `--apikey`: 在智谱平台申请你的 API Key

**2. ModelScope(魔搭社区)**

- 文档: https://modelscope.cn/models/ZhipuAI/AutoGLM-Phone-9B
- `--base-url`: `https://api-inference.modelscope.cn/v1`
- `--model`: `ZhipuAI/AutoGLM-Phone-9B`
- `--apikey`: 在 ModelScope 平台申请你的 API Key

使用第三方服务的示例：

```bash
# 使用智谱 BigModel
python main.py --base-url https://open.bigmodel.cn/api/paas/v4 --model "autoglm-phone" --apikey "your-bigmodel-api-key" "打开美团搜索附近的火锅店"

# 使用 ModelScope
python main.py --base-url https://api-inference.modelscope.cn/v1 --model "ZhipuAI/AutoGLM-Phone-9B" --apikey "your-modelscope-api-key" "打开美团搜索附近的火锅店"
```

#### 选项 B: 自行部署模型

如果你希望在本地或自己的服务器上部署模型：

1. 按照 `requirements.txt` 中 `For Model Deployment` 章节自行安装推理引擎框架。

对于SGLang， 除了使用pip安装，你也可以使用官方docker:
>
> ```shell
> docker pull lmsysorg/sglang:v0.5.6.post1
> ```
>
> 进入容器，执行
>
> ```
> pip install nvidia-cudnn-cu12==9.16.0.29
> ```

对于 vLLM，除了使用pip 安装，你也可以使用官方docker:
>
> ```shell
> docker pull vllm/vllm-openai:v0.12.0
> ```
>
> 进入容器，执行
>
> ```
> pip install -U transformers --pre
> ```

**注意**: 上述步骤出现的关于 transformers 的依赖冲突可以忽略。

1. 在对应容器或者实体机中(非容器安装)下载模型，通过 SGlang / vLLM 启动，得到 OpenAI 格式服务。这里提供一个 vLLM部署方案，请严格遵循我们提供的启动参数:

- vLLM:

```shell
python3 -m vllm.entrypoints.openai.api_server \
 --served-model-name autoglm-phone-9b \
 --allowed-local-media-path /   \
 --mm-encoder-tp-mode data \
 --mm_processor_cache_type shm \
 --mm_processor_kwargs "{\"max_pixels\":5000000}" \
 --max-model-len 25480  \
 --chat-template-content-format string \
 --limit-mm-per-prompt "{\"image\":10}" \
 --model zai-org/AutoGLM-Phone-9B \
 --port 8000
```

- SGLang:

```shell
python3 -m sglang.launch_server --model-path  zai-org/AutoGLM-Phone-9B \
        --served-model-name autoglm-phone-9b  \
        --context-length 25480  \
        --mm-enable-dp-encoder   \
        --mm-process-config '{"image":{"max_pixels":5000000}}'  \
        --port 8000
```

- 该模型结构与 `GLM-4.1V-9B-Thinking` 相同, 关于模型部署的详细内容，你也以查看 [GLM-V](https://github.com/zai-org/GLM-V)
  获取模型部署和使用指南。

- 运行成功后，将可以通过 `http://localhost:8000/v1` 访问模型服务。 如果您在远程服务器部署模型, 使用该服务器的IP访问模型.

### 4. 检查模型部署

模型服务启动后，可以使用检查脚本验证部署是否成功：

```bash
python scripts/check_deployment_cn.py --base-url http://你的IP:你的端口/v1 --model 模型名称
```

脚本将发送测试请求并展示模型的推理结果，你可以根据输出判断模型部署是否正常工作。

基于给定的任务, 预期输出如下。**如果思维链长度很短, 或者出现了乱码, 很可能是模型部署失败**, 请仔细检查文档要求的配置和依赖。

```
<think>用户想要比较这个洗发水在京东和淘宝上的价格，然后选择最便宜的平台下单。当前在小红书app上，显示的是一个关于LUMMI MOOD洗发水的帖子。

我需要：
1. 先启动京东app，搜索这个洗发水
2. 查看京东的价格
3. 再启动淘宝app，搜索这个洗发水
4. 查看淘宝的价格
5. 比较价格后，选择最便宜的京东或淘宝下单

首先，我需要从当前的小红书界面退出，然后启动京东app。</think>
<answer>do(action="Launch", app="京东")
```

**参数说明：**
- `--base-url`: 模型服务地址(根据实际部署地址修改)
- `--model`: 模型名称
- `--messages-file`: 可选，指定自定义测试消息文件(默认使用 `scripts/sample_messages.json`)

## 使用 AutoGLM

### 🌐 Web 界面（推荐）

Web 界面提供了最直观的使用体验，支持实时监控和多轮对话：

```bash
# 启动 Web 界面
python web_start.py

# 浏览器访问 http://localhost:5000
```

**主要优势**:
- 🎯 **像聊天一样使用**: 自然语言对话交互
- 📱 **实时监控**: 查看执行状态和截图
- 📊 **任务报告**: 详细的执行步骤分析
- ⚙️ **可视化配置**: 图形化的参数设置
- 🔄 **历史记录**: 所有任务自动保存

### 💻 命令行（进阶用户）

对于自动化脚本和批量处理场景，可以使用命令行方式：

根据你部署的模型，设置 `--base-url` 和 `--model` 参数：

```bash
# 单次任务执行
python main.py --base-url http://localhost:8000/v1 --model "autoglm-phone-9b" "打开美团搜索附近的火锅店"

# 交互模式
python main.py --base-url http://localhost:8000/v1 --model "autoglm-phone-9b"

# 使用第三方服务（智谱BigModel）
python main.py --base-url https://open.bigmodel.cn/api/paas/v4 --model autoglm-phone --apikey "your-api-key" "打开微信查看未读消息"

# 使用英文界面
python main.py --lang en --base-url http://localhost:8000/v1 "Open Chrome browser"

# 列出支持的应用
python main.py --list-apps

# 脚本记录模式 - 自动记录操作并生成可重放脚本
python main.py --record-script "打开设置调整音量到最大"

# 自定义脚本输出目录
python main.py --record-script --script-output-dir my_scripts "检查天气应用"
```

### Python API

```python
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

# Configure model
model_config = ModelConfig(
    base_url="http://localhost:8000/v1",
    model_name="autoglm-phone-9b",
)

# 创建 Agent
agent = PhoneAgent(model_config=model_config)

# 执行任务
result = agent.run("打开淘宝搜索无线耳机")
print(result)

# 使用脚本记录功能
agent_config = AgentConfig(
    record_script=True,              # 启用脚本记录
    script_output_dir="scripts",     # 脚本输出目录
)

agent_with_recording = PhoneAgent(
    model_config=model_config,
    agent_config=agent_config
)

# 执行任务（自动记录）
result = agent_with_recording.run("打开设置检查电池")
print(result)

# 获取录制摘要
summary = agent_with_recording.get_script_summary()
print(summary)
```

## 📹 脚本记录与重放

Phone Agent 现在支持脚本记录功能，可以在执行任务时自动记录所有操作并生成可重放的自动化脚本。

### 功能特性

- **自动记录**: 在执行任务时自动记录所有操作步骤
- **详细信息**: 捕获操作类型、坐标、文本输入、思考过程等
- **截图保存**: 可选保存每个步骤的截图（如果可用）
- **执行结果**: 记录每个操作的成功/失败状态和错误信息
- **脚本格式**: 同时生成 JSON 格式（数据存储）和 Python 脚本（可重放）
- **完整重放**: 可以精确重现录制的操作序列

### 命令行使用

```bash
# 启用脚本记录执行任务
python main.py --record-script "打开微信查看未读消息"

# 自定义脚本输出目录
python main.py --record-script --script-output-dir my_scripts "检查天气应用"

# 静默模式录制
python main.py --record-script --quiet "发送测试邮件"

# 结合其他参数使用
python main.py --record-script --device-id emulator-5554 --max-steps 50 "设置闹钟"

# 指定语言和模型
python main.py --record-script --lang cn --model autoglm-phone "导航到公司"
```

### 生成的文件

执行脚本记录后，系统会生成两个文件：

1. **JSON 脚本文件**（如 `20251213_133613_打开设置调整音量到最大.json`）：
   - 包含完整的元数据（任务名称、设备信息、执行时间、成功率等）
   - 详细的步骤信息（操作类型、坐标、思考过程、截图路径等）

2. **Python 重放脚本**（如 `20251213_133613_打开设置调整音量到最大_replay.py`）：
   - 可直接运行的 Python 脚本
   - 支持设备配置和操作延迟设置
   - 包含错误处理和用户交互功能

### 使用生成的脚本

```bash
# 运行重放脚本
python scripts/20251213_133613_打开设置调整音量到最大_replay.py scripts/20251213_133613_打开设置调整音量到最大.json

# 或者直接运行（如果脚本在同一目录）
python scripts/your_task_replay.py
```

重放脚本执行时：
- 显示任务信息和统计数据
- 询问设备 ID 和操作延迟
- 按顺序重放每个操作
- 提供实时反馈和错误处理
- 支持用户中断执行

### 配置选项

#### AgentConfig 参数

```python
from phone_agent.agent import AgentConfig

config = AgentConfig(
    record_script=True,              # 启用脚本记录
    script_output_dir="scripts",     # 脚本输出目录
    # ... 其他参数
)
```

#### 命令行参数

- `--record-script`: 启用脚本记录
- `--script-output-dir DIR`: 指定脚本输出目录

### 支持的操作类型

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

### 实际示例

以下是一个完整的脚本记录示例：

```bash
# 执行任务并记录脚本
python main.py --record-script "打开设置调整音量到最大"

# 输出结果：
# ✅ 任务完成: 打开设置调整音量到最大
# 📊 执行统计: 4 步骤，成功率 100%，耗时 36.0s
# 📄 脚本已保存: scripts/20251213_133613_打开设置调整音量到最大.json
# 🐍 重放脚本: scripts/20251213_133613_打开设置调整音量到最大_replay.py
```

生成的 JSON 脚本包含：
```json
{
  "metadata": {
    "task_name": "打开设置调整音量到最大",
    "description": "打开设置调整音量到最大",
    "created_at": "2025-12-13T13:35:37.170487",
    "total_steps": 4,
    "device_id": null,
    "model_name": "autoglm-phone",
    "success_rate": 100.0,
    "execution_time": 36.0
  },
  "steps": [
    {
      "step_number": 1,
      "action_type": "Tap",
      "action_data": {
        "action": "Tap",
        "element": [619, 721]
      },
      "thinking": "用户要求打开设置并调整音量到最大...",
      "success": true
    }
    // ... 更多步骤
  ]
}
```

详细文档请参考：[SCRIPT_RECORDING.md](SCRIPT_RECORDING.md)

## ☁️ 云集成配置

Open-AutoGLM 支持 Supabase 云服务集成，提供数据持久化、云端存储和多设备同步功能。

### 快速配置

#### 1. 创建 Supabase 项目

1. 访问 [Supabase 官网](https://supabase.com) 并登录
2. 点击 "New Project" 创建新项目
3. 选择组织和数据库配置
4. 记录项目的 **URL** 和 **Service Role Key**

#### 2. 环境变量配置

在项目根目录创建 `.env` 文件：

```bash
# Supabase 配置
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SECRET_KEY=your-service-role-key
```

或者在启动时直接设置：

```bash
export SUPABASE_URL=https://your-project-id.supabase.co
export SUPABASE_SECRET_KEY=your-service-role-key
python web_start.py
```

#### 3. 数据库初始化

首次使用时，系统会自动创建必要的数据库表：

- `tasks` - 任务记录
- `task_steps` - 执行步骤详情
- `step_screenshots` - 截图文件信息

> 💡 **自动迁移**: 无需手动执行SQL，系统会自动处理数据库结构。

### 云服务功能

#### 🗄️ 数据持久化
- **任务记录**: 所有任务自动保存到云端数据库
- **执行步骤**: 详细的步骤跟踪数据持久化存储
- **配置信息**: 用户配置跨设备同步

#### 📸 云端截图存储
- **自动上传**: 截图时自动上传到 Supabase Storage
- **双重存储**: 本地 + 云端，确保数据安全
- **智能压缩**: 自动压缩大图片，节省存储空间
- **CDN加速**: 支持全球快速访问

#### 🔄 多设备同步
- **实时同步**: 任务数据在多个设备间实时同步
- **跨平台访问**: 通过Web界面在不同设备上访问历史数据
- **配置共享**: 模型配置和设备设置自动同步

#### 📊 数据分析
- **使用统计**: 任务执行次数、成功率等统计信息
- **性能分析**: 执行时间、步数等性能指标
- **趋势报告**: 长期使用趋势分析

### 配置验证

#### 检查连接状态
```bash
# Web 界面中会显示连接状态
# 绿色：已连接云服务
# 黄色：使用本地存储模式
# 红色：连接失败
```

#### 测试数据上传
```bash
# 执行一个简单任务测试
python main.py --base-url https://open.bigmodel.cn/api/paas/v4 --model autoglm-phone "打开设置"
```

检查云数据库中是否出现新的任务记录。

### 高级配置

#### 自定义存储桶
默认使用 `AutoGLMStorage` 存储桶，可以自定义：
```python
# 在 web/supabase_manager.py 中修改
STORAGE_BUCKET_NAME = "your-custom-bucket"
```

#### 数据保留策略
```python
# 设置数据保留天数
DATA_RETENTION_DAYS = 30

# 设置截图保留策略
SCREENSHOT_RETENTION_DAYS = 7
```

#### 批量上传历史截图
```bash
# 上传本地所有截图到云端
python tools/bulk_upload_screenshots.py

# 预览模式（不实际上传）
python tools/bulk_upload_screenshots.py --dry-run
```

### 故障排除

#### 连接失败
- 检查 Supabase URL 和 Key 是否正确
- 确认网络连接正常
- 验证 Supabase 项目状态

#### 上传失败
- 检查 Storage 权限设置
- 确认存储桶配额未超限
- 查看详细错误日志

#### 数据同步问题
- 检查设备时间同步
- 确认环境变量配置正确
- 重启服务重新连接

详细配置说明请参考：
- [步骤持久化指南](docs/step_persistence_guide.md)
- [截图上传指南](docs/supabase_screenshot_upload_guide.md)

## 🌐 Web 界面概述

Open-AutoGLM 的 Web 界面提供了现代化的用户体验，支持实时监控和多轮对话。

### 核心功能
- 🗣️ **对话式交互**: 像聊天一样使用自然语言描述任务
- 📱 **实时监控**: WebSocket 实时推送执行状态和截图
- 📊 **任务报告**: 详细的执行步骤分析和性能统计
- ⚙️ **可视化配置**: 图形化的模型和设备参数设置

快速启动请参考：[🌐 Web 界面使用指南](#-web-界面使用指南推荐方式)

详细使用说明请参考：[WEB_INTERFACE.md](WEB_INTERFACE.md)

## 📊 任务执行监控

Open-AutoGLM 提供了完整的任务执行可观测性系统，让您能够详细了解每个任务的执行过程。

### 步骤跟踪系统

#### 🔍 详细记录
- **AI 思考过程**: 记录每个决策点的分析过程
- **执行动作**: 详细记录点击、滑动、输入等操作
- **执行结果**: 记录每个操作的成功/失败状态
- **耗时统计**: 精确记录每个步骤的执行时间
- **截图关联**: 自动关联执行步骤与界面截图

#### 📈 性能分析
- **成功率统计**: 任务和步骤级别的成功率分析
- **执行时间分析**: 平均执行时间、性能瓶颈识别
- **错误模式识别**: 常见错误类型和频率统计
- **优化建议**: 基于历史数据的性能优化建议

### 任务执行报告

#### 📑 报告内容
- **执行时间线**: 按时间顺序展示所有执行步骤
- **截图回放**: 像翻书一样查看任务执行过程
- **思考链条**: 完整展示 AI 的决策过程
- **错误诊断**: 失败步骤的详细错误分析

#### 📊 统计数据
```
任务: 打开小红书搜索美食
总步骤: 12 步
成功步骤: 11 步
失败步骤: 1 步
成功率: 91.7%
总耗时: 45.2 秒
平均步骤耗时: 3.8 秒
```

### 查看方式

#### Web 界面（推荐）
1. 执行任务后，在对话历史中点击"报告"按钮
2. 查看详细的执行时间线和截图回放
3. 分析性能统计数据和优化建议

#### API 接口
```bash
# 获取任务步骤
GET /api/tasks/{task_id}/steps

# 获取任务报告
GET /api/tasks/{task_id}/report

# 获取任务截图
GET /api/tasks/{task_id}/screenshots
```

### 数据持久化

#### 💾 云端存储
- 所有步骤数据自动保存到 Supabase 数据库
- 支持历史数据查询和分析
- 跨设备同步访问历史记录

#### 📸 截图管理
- 截图自动上传到云端存储
- 支持批量上传和历史截图迁移
- 智能压缩节省存储空间

### 使用场景

#### 🧪 调试和优化
- 分析任务失败原因，优化操作流程
- 识别性能瓶颈，提升执行效率
- 对比不同任务策略的效果

#### 📋 自动化测试
- 记录测试执行过程，便于问题定位
- 生成测试报告，验证应用功能
- 监控测试覆盖率和质量指标

#### 📈 业务分析
- 统计常用功能和操作模式
- 分析用户行为和系统使用情况
- 生成业务洞察和改进建议

详细技术说明请参考：[步骤持久化指南](docs/step_persistence_guide.md)

## 远程调试

Phone Agent 支持通过 WiFi/网络进行远程 ADB 调试，无需 USB 连接即可控制设备。

### 配置远程调试

#### 在手机端开启无线调试

确保手机和电脑在同一个WiFi中，如图所示

![开启无线调试](resources/setting.png)

#### 在电脑端使用标准 ADB 命令

```bash

# 通过 WiFi 连接, 改成手机显示的 IP 地址和端口
adb connect 192.168.1.100:5555

# 验证连接
adb devices
# 应显示：192.168.1.100:5555    device
```

### 设备管理命令

```bash
# 列出所有已连接设备
adb devices

# 连接远程设备
adb connect 192.168.1.100:5555

# 断开指定设备
adb disconnect 192.168.1.100:5555

# 指定设备执行任务
python main.py --device-id 192.168.1.100:5555 --base-url http://localhost:8000/v1 --model "autoglm-phone-9b" "打开抖音刷视频"
```

### Python API 远程连接

```python
from phone_agent.adb import ADBConnection, list_devices

# 创建连接管理器
conn = ADBConnection()

# 连接远程设备
success, message = conn.connect("192.168.1.100:5555")
print(f"连接状态: {message}")

# 列出已连接设备
devices = list_devices()
for device in devices:
    print(f"{device.device_id} - {device.connection_type.value}")

# 在 USB 设备上启用 TCP/IP
success, message = conn.enable_tcpip(5555)
ip = conn.get_device_ip()
print(f"设备 IP: {ip}")

# 断开连接
conn.disconnect("192.168.1.100:5555")
```

### 远程连接问题排查

**连接被拒绝：**

- 确保设备和电脑在同一网络
- 检查防火墙是否阻止 5555 端口
- 确认已启用 TCP/IP 模式：`adb tcpip 5555`

**连接断开：**

- WiFi 可能断开了，使用 `--connect` 重新连接
- 部分设备重启后会禁用 TCP/IP，需要通过 USB 重新启用

**多设备：**

- 使用 `--device-id` 指定要使用的设备
- 或使用 `--list-devices` 查看所有已连接设备

## 配置

### 自定义SYSTEM PROMPT

系统提供中英文两套 prompt，通过 `--lang` 参数切换：

- `--lang cn` - 中文 prompt(默认)，配置文件：`phone_agent/config/prompts_zh.py`
- `--lang en` - 英文 prompt，配置文件：`phone_agent/config/prompts_en.py`

可以直接修改对应的配置文件来增强模型在特定领域的能力，或通过注入 app 名称禁用某些 app。

### 环境变量

#### 核心配置
| 变量                           | 描述                    | 默认值                        |
|------------------------------|-----------------------|----------------------------|
| `PHONE_AGENT_BASE_URL`       | 模型 API 地址            | `http://localhost:8000/v1` |
| `PHONE_AGENT_MODEL`          | 模型名称                 | `autoglm-phone-9b`         |
| `PHONE_AGENT_API_KEY`        | 模型认证 API Key         | `EMPTY`                    |
| `PHONE_AGENT_MAX_STEPS`      | 每个任务最大步数             | `100`                      |
| `PHONE_AGENT_DEVICE_ID`      | ADB 设备 ID            | (自动检测)                     |
| `PHONE_AGENT_LANG`           | 语言 (`cn` 或 `en`)      | `cn`                       |

#### 脚本记录
| 变量                           | 描述                    | 默认值                        |
|------------------------------|-----------------------|----------------------------|
| `PHONE_AGENT_RECORD_SCRIPT`  | 是否启用脚本记录            | `false`                    |
| `PHONE_AGENT_SCRIPT_OUTPUT_DIR` | 脚本输出目录               | `scripts`                  |

#### 🌐 Web 界面配置
| 变量                           | 描述                    | 默认值                        |
|------------------------------|-----------------------|----------------------------|
| `PHONE_AGENT_WEB_HOST`       | Web 服务监听地址          | `0.0.0.0`                  |
| `PHONE_AGENT_WEB_PORT`       | Web 服务端口              | `5000`                     |
| `PHONE_AGENT_WEB_DEBUG`      | 是否启用调试模式            | `false`                    |

#### ☁️ 云集成配置
| 变量                           | 描述                    | 默认值                        |
|------------------------------|-----------------------|----------------------------|
| `SUPABASE_URL`               | Supabase 项目 URL       | (空，表示禁用云功能)              |
| `SUPABASE_SECRET_KEY`        | Supabase 服务角色密钥      | (空，表示禁用云功能)              |
| `SCREENSHOT_AUTO_UPLOAD`     | 是否自动上传截图到云端        | `true`                     |

#### 📊 监控和跟踪
| 变量                           | 描述                    | 默认值                        |
|------------------------------|-----------------------|----------------------------|
| `STEP_TRACKING_ENABLED`      | 是否启用步骤跟踪            | `true`                     |
| `STEP_BUFFER_SIZE`           | 步骤缓冲区大小              | `50`                       |
| `STEP_FLUSH_INTERVAL`        | 步骤刷新间隔（秒）           | `5.0`                      |

### 模型配置

```python
from phone_agent.model import ModelConfig

config = ModelConfig(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",  # API 密钥(如需要)
    model_name="autoglm-phone-9b",  # 模型名称
    max_tokens=3000,  # 最大输出 token 数
    temperature=0.1,  # 采样温度
    frequency_penalty=0.2,  # 频率惩罚
)
```

### Agent 配置

```python
from phone_agent.agent import AgentConfig

config = AgentConfig(
    max_steps=100,  # 每个任务最大步数
    device_id=None,  # ADB 设备 ID(None 为自动检测)
    lang="cn",  # 语言选择：cn(中文)或 en(英文)
    verbose=True,  # 打印调试信息(包括思考过程和执行动作)
    record_script=False,  # 是否启用脚本记录
    script_output_dir="scripts",  # 脚本输出目录
    # 新增配置选项
    enable_step_tracking=True,  # 启用步骤跟踪
    screenshot_auto_upload=True,  # 自动上传截图
    supabase_url="your-supabase-url",  # Supabase URL（可选）
    supabase_key="your-supabase-key",  # Supabase Key（可选）
)
```

### 🌐 Web 界面配置

#### 使用配置文件
```python
# web/config.py
WEB_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'secret_key': 'your-secret-key',  # 生产环境请设置
    'cors_origins': ['http://localhost:3000'],  # 允许的跨域源
}
```

#### 使用环境变量
```bash
# .env 文件
PHONE_AGENT_WEB_HOST=0.0.0.0
PHONE_AGENT_WEB_PORT=8080
PHONE_AGENT_WEB_DEBUG=true
```

### ☁️ 云集成配置

#### Supabase 配置
```python
# web/supabase_manager.py
SUPABASE_CONFIG = {
    'url': os.getenv('SUPABASE_URL'),
    'key': os.getenv('SUPABASE_SECRET_KEY'),
    'storage_bucket': 'AutoGLMStorage',
    'retry_attempts': 3,
    'upload_timeout': 30,
}
```

#### 步骤跟踪配置
```python
from phone_agent.step_tracker import StepTrackerConfig

config = StepTrackerConfig(
    buffer_size=50,  # 缓冲区大小
    flush_interval=5.0,  # 刷新间隔（秒）
    enable_compression=True,  # 启用数据压缩
    auto_upload_screenshots=True,  # 自动上传截图
    local_backup=True,  # 本地备份
)
```

### Verbose 模式输出

当 `verbose=True` 时，Agent 会在每一步输出详细信息：

```
==================================================
💭 思考过程:
--------------------------------------------------
当前在系统桌面，需要先启动小红书应用
--------------------------------------------------
🎯 执行动作:
{
  "_metadata": "do",
  "action": "Launch",
  "app": "小红书"
}
==================================================

... (执行动作后继续下一步)

==================================================
💭 思考过程:
--------------------------------------------------
小红书已打开，现在需要点击搜索框
--------------------------------------------------
🎯 执行动作:
{
  "_metadata": "do",
  "action": "Tap",
  "element": [500, 100]
}
==================================================

🎉 ================================================
✅ 任务完成: 已成功搜索美食攻略
==================================================
```

这样可以清楚地看到 AI 的推理过程和每一步的具体操作。

## 支持的应用

Phone Agent 支持 50+ 款主流中文应用：

| 分类   | 应用              |
|------|-----------------|
| 社交通讯 | 微信、QQ、微博        |
| 电商购物 | 淘宝、京东、拼多多       |
| 美食外卖 | 美团、饿了么、肯德基      |
| 出行旅游 | 携程、12306、滴滴出行   |
| 视频娱乐 | bilibili、抖音、爱奇艺 |
| 音乐音频 | 网易云音乐、QQ音乐、喜马拉雅 |
| 生活服务 | 大众点评、高德地图、百度地图  |
| 内容社区 | 小红书、知乎、豆瓣       |

运行 `python main.py --list-apps` 查看完整列表。

## 可用操作

Agent 可以执行以下操作：

| 操作           | 描述              |
|--------------|-----------------|
| `Launch`     | 启动应用            |  
| `Tap`        | 点击指定坐标          |
| `Type`       | 输入文本            |
| `Swipe`      | 滑动屏幕            |
| `Back`       | 返回上一页           |
| `Home`       | 返回桌面            |
| `Long Press` | 长按              |
| `Double Tap` | 双击              |
| `Wait`       | 等待页面加载          |
| `Take_over`  | 请求人工接管(登录/验证码等) |

## 自定义回调

处理敏感操作确认和人工接管：

```python
def my_confirmation(message: str) -> bool:
    """敏感操作确认回调"""
    return input(f"确认执行 {message}？(y/n): ").lower() == "y"


def my_takeover(message: str) -> None:
    """人工接管回调"""
    print(f"请手动完成: {message}")
    input("完成后按回车继续...")


agent = PhoneAgent(
    confirmation_callback=my_confirmation,
    takeover_callback=my_takeover,
)
```

## 示例

查看 `examples/` 目录获取更多使用示例：

- `basic_usage.py` - 基础任务执行
- `script_recording_demo.py` - 脚本记录功能演示
- 单步调试模式
- 批量任务执行
- 自定义回调

## 二次开发

### 配置开发环境

二次开发需要使用开发依赖：

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/
```

### 完整项目结构

```
phone_agent/
├── __init__.py          # 包导出
├── agent.py             # PhoneAgent 主类
├── recorder.py          # 脚本记录功能
├── adb/                 # ADB 工具
│   ├── connection.py    # 远程/本地连接管理
│   ├── screenshot.py    # 屏幕截图
│   ├── input.py         # 文本输入 (ADB Keyboard)
│   └── device.py        # 设备控制 (点击、滑动等)
├── actions/             # 操作处理
│   └── handler.py       # 操作执行器
├── config/              # 配置
│   ├── apps.py          # 支持的应用映射
│   ├── prompts_zh.py    # 中文系统提示词
│   └── prompts_en.py    # 英文系统提示词
└── model/               # AI 模型客户端
    └── client.py        # OpenAI 兼容客户端

web/                     # Web 界面
├── app.py               # Flask 应用主文件
├── static/              # 静态资源
│   ├── css/
│   │   └── style.css    # 界面样式
│   └── js/
│       ├── app.js       # 主界面 JavaScript
│       └── config.js    # 配置页面 JavaScript
└── templates/           # HTML 模板
    ├── index.html       # 主界面
    └── config.html      # 配置界面

web_start.py             # Web 服务启动脚本
requirements-web.txt     # Web 界面依赖
```

## 常见问题

我们列举了一些常见的问题，以及对应的解决方案：

### 🌐 Web 界面问题

#### Web 服务启动失败
```bash
# 检查依赖是否完整
pip install -r requirements-web.txt

# 检查端口是否被占用
netstat -tulpn | grep :5000

# 使用不同端口启动
python web_start.py --port 8080
```

#### WebSocket 连接失败
- **现象**: 界面无法实时更新，显示"连接断开"
- **解决方案**:
  1. 刷新浏览器页面
  2. 检查防火墙设置
  3. 确认端口没有被阻止

#### 界面显示异常
- **清除浏览器缓存**: Ctrl+F5 强制刷新
- **检查浏览器兼容性**: 推荐使用 Chrome、Firefox、Safari
- **检查控制台错误**: F12 打开开发者工具查看错误信息

### ☁️ 云集成问题

#### Supabase 连接失败
```bash
# 检查环境变量
echo $SUPABASE_URL
echo $SUPABASE_SECRET_KEY

# 测试连接
curl -H "Authorization: Bearer $SUPABASE_SECRET_KEY" "$SUPABASE_URL/rest/v1/"
```

**解决方案**:
- 验证 Supabase URL 和 Key 格式正确
- 确认网络连接正常
- 检查 Supabase 项目状态

#### 截图上传失败
- **检查存储权限**: 确认 Supabase Storage 已正确配置
- **查看详细错误**: 检查 Web 服务日志
- **手动重试**: 使用批量上传工具重新上传

```bash
# 批量上传工具
python tools/bulk_upload_screenshots.py --dry-run  # 预览
python tools/bulk_upload_screenshots.py           # 上传
```

#### 数据同步问题
- **检查时间同步**: 确保设备时间正确
- **重新连接**: 重启 Web 服务重新建立连接
- **查看数据状态**: 在 Supabase Dashboard 中检查数据表

### 📱 设备连接问题

### 设备未找到

尝试通过重启 ADB 服务来解决：

```bash
adb kill-server
adb start-server
adb devices
```

如果仍然无法识别，请检查：

1. USB 调试是否已开启
2. 数据线是否支持数据传输(部分数据线仅支持充电)
3. 手机上弹出的授权框是否已点击「允许」
4. 尝试更换 USB 接口或数据线

### 能打开应用，但无法点击

部分机型需要同时开启两个调试选项才能正常使用：

- **USB 调试**
- **USB 调试(安全设置)**

请在 `设置 → 开发者选项` 中检查这两个选项是否都已启用。

### 文本输入不工作

1. 确保设备已安装 ADB Keyboard
2. 在设置 > 系统 > 语言和输入法 > 虚拟键盘 中启用
3. Agent 会在需要输入时自动切换到 ADB Keyboard

### 截图失败(黑屏)

这通常意味着应用正在显示敏感页面(支付、密码、银行类应用)。Agent 会自动检测并请求人工接管。

### windows 编码异常问题

报错信息形如 `UnicodeEncodeError gbk code`

解决办法: 在运行代码的命令前面加上环境变量: `PYTHONIOENCODING=utf-8`

### 交互模式非TTY环境无法使用

报错形如: `EOF when reading a line`

解决办法: 使用非交互模式直接指定任务, 或者切换到 TTY 模式的终端应用.

### 🚀 性能问题

#### Web 界面响应慢
- **检查模型服务**: 确认模型服务正常运行
- **优化截图**: 调整截图压缩设置
- **减少缓冲**: 降低步骤跟踪缓冲区大小

#### 内存占用过高
```bash
# 监控内存使用
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# 调整缓冲区大小
export STEP_BUFFER_SIZE=20
export STEP_FLUSH_INTERVAL=2.0
```

### 🔧 高级问题排查

#### 调试模式启用
```bash
# Web 界面调试
python web_start.py --debug

# 命令行详细输出
python main.py --verbose --base-url http://localhost:8000/v1 "测试任务"
```

#### 日志查看
```bash
# 查看 Web 服务日志
tail -f logs/web.log

# 查看步骤跟踪日志
tail -f logs/step_tracker.log

# 查看 Supabase 连接日志
grep "Supabase" logs/app.log
```

### 引用

如果你觉得我们的工作有帮助，请引用以下论文：

```bibtex
@article{liu2024autoglm,
  title={Autoglm: Autonomous foundation agents for guis},
  author={Liu, Xiao and Qin, Bo and Liang, Dongzhu and Dong, Guang and Lai, Hanyu and Zhang, Hanchen and Zhao, Hanlin and Iong, Iat Long and Sun, Jiadai and Wang, Jiaqi and others},
  journal={arXiv preprint arXiv:2411.00820},
  year={2024}
}
@article{xu2025mobilerl,
  title={MobileRL: Online Agentic Reinforcement Learning for Mobile GUI Agents},
  author={Xu, Yifan and Liu, Xiao and Liu, Xinghan and Fu, Jiaqi and Zhang, Hanchen and Jing, Bohao and Zhang, Shudan and Wang, Yuting and Zhao, Wenyi and Dong, Yuxiao},
  journal={arXiv preprint arXiv:2509.18119},
  year={2025}
}
```

---

## 自动化部署指南(面向 AI)

> **本章节专为 AI 助手(如 Claude Code)设计，用于自动化部署 Open-AutoGLM。**
>
> 如果你是人类读者，可以跳过本章节，按照上面的文档操作即可。

---

### 项目概述

Open-AutoGLM 是一个手机 Agent 框架：
- **输入**：用户的自然语言指令(如"打开微信发消息给张三")
- **输出**：自动操作用户的安卓手机完成任务
- **原理**：截图 → 视觉模型理解界面 → 输出点击坐标 → ADB 执行操作 → 循环

架构分为两部分：
1. **Agent 代码**(本仓库)：运行在用户电脑上，负责调用模型、解析动作、控制手机
2. **视觉模型服务**：可以是远程 API，也可以本地部署

---

### 部署前置检查

在开始部署前，请逐项向用户确认以下内容：

#### 硬件环境
- [ ] 用户有一台安卓手机(Android 7.0+)
- [ ] 用户有一根支持数据传输的 USB 数据线(不是仅充电线)
- [ ] 手机和电脑可以通过数据线连接

#### 手机端配置
- [ ] 手机已开启「开发者模式」(设置 → 关于手机 → 连续点击版本号 7 次)
- [ ] 手机已开启「USB 调试」(设置 → 开发者选项 → USB 调试)
- [ ] 部分机型需要同时开启「USB 调试(安全设置)」
- [ ] 手机已安装 ADB Keyboard 应用(下载地址：https://github.com/senzhk/ADBKeyBoard/blob/master/ADBKeyboard.apk)
- [ ] ADB Keyboard 已在系统设置中启用(设置 → 语言和输入法 → 启用 ADB Keyboard)

#### 模型服务确认(二选一)

**请明确询问用户：你是否已有可用的 AutoGLM 模型服务？**

- **选项 A：使用已部署的模型服务(推荐)**
  - 用户提供模型服务的 URL(如 `http://xxx.xxx.xxx.xxx:8000/v1`)
  - 无需本地 GPU，无需下载模型
  - 直接使用该 URL 作为 `--base-url` 参数

- **选项 B：本地部署模型(高配置要求)**
  - 需要 NVIDIA GPU(建议 24GB+ 显存)
  - 需要安装 vLLM 或 SGLang
  - 需要下载约 20GB 的模型文件
  - **如果用户是新手或不确定，强烈建议选择选项 A**

---

### 部署流程

#### 阶段一：环境准备

```bash
# 1. 安装 ADB 工具
# MacOS:
brew install android-platform-tools
# 或手动下载：https://developer.android.com/tools/releases/platform-tools

# Windows: 下载后解压，添加到 PATH 环境变量

# 2. 验证 ADB 安装
adb version
# 应输出版本信息

# 3. 连接手机并验证
# 用数据线连接手机，手机上点击「允许 USB 调试」
adb devices
# 应输出设备列表，如：
# List of devices attached
# XXXXXXXX    device
```

**如果 `adb devices` 显示空列表或 unauthorized：**
1. 检查手机上是否弹出授权框，点击「允许」
2. 检查 USB 调试是否开启
3. 尝试更换数据线或 USB 接口
4. 执行 `adb kill-server && adb start-server` 后重试

#### 阶段二：安装 Agent

```bash
# 1. 克隆仓库(如果还没有克隆)
git clone https://github.com/zai-org/Open-AutoGLM.git
cd Open-AutoGLM

# 2. 创建虚拟环境(推荐)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
pip install -e .
```

**注意：不需要 clone 模型仓库，模型通过 API 调用。**

#### 阶段三：配置模型服务

**如果用户选择选项 A(使用已部署的模型)：**

你可以使用以下第三方模型服务：

1. **智谱 BigModel**
   - 文档：https://docs.bigmodel.cn/cn/api/introduction
   - `--base-url`：`https://open.bigmodel.cn/api/paas/v4`
   - `--model`：`autoglm-phone`
   - `--apikey`：在智谱平台申请你的 API Key

2. **ModelScope(魔搭社区)**
   - 文档：https://modelscope.cn/models/ZhipuAI/AutoGLM-Phone-9B
   - `--base-url`：`https://api-inference.modelscope.cn/v1`
   - `--model`：`ZhipuAI/AutoGLM-Phone-9B`
   - `--apikey`：在 ModelScope 平台申请你的 API Key

使用示例：

```bash
# 使用智谱 BigModel
python main.py --base-url https://open.bigmodel.cn/api/paas/v4 --model "autoglm-phone" --apikey "your-bigmodel-api-key" "打开美团搜索附近的火锅店"

# 使用 ModelScope
python main.py --base-url https://api-inference.modelscope.cn/v1 --model "ZhipuAI/AutoGLM-Phone-9B" --apikey "your-modelscope-api-key" "打开美团搜索附近的火锅店"
```

或者直接使用用户提供的其他模型服务 URL，跳过本地模型部署步骤。

**如果用户选择选项 B(本地部署模型)：**

```bash
# 1. 安装 vLLM
pip install vllm

# 2. 启动模型服务(会自动下载模型，约 20GB)
python3 -m vllm.entrypoints.openai.api_server \
  --served-model-name autoglm-phone-9b \
  --allowed-local-media-path / \
  --mm-encoder-tp-mode data \
  --mm_processor_cache_type shm \
  --mm_processor_kwargs "{\"max_pixels\":5000000}" \
  --max-model-len 25480 \
  --chat-template-content-format string \
  --limit-mm-per-prompt "{\"image\":10}" \
  --model zai-org/AutoGLM-Phone-9B \
  --port 8000

# 模型服务 URL 为：http://localhost:8000/v1
```

#### 阶段四：验证部署

```bash
# 在 Open-AutoGLM 目录下执行
# 将 {MODEL_URL} 替换为实际的模型服务地址

python main.py --base-url {MODEL_URL} --model "autoglm-phone-9b" "打开微信，对文件传输助手发送消息：部署成功"
```

**预期结果：**
- 手机自动打开微信
- 自动搜索「文件传输助手」
- 自动发送消息「部署成功」

---

### 异常处理

| 错误现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `adb devices` 无输出 | USB 调试未开启或数据线问题 | 检查开发者选项，更换数据线 |
| `adb devices` 显示 unauthorized | 手机未授权 | 手机上点击「允许 USB 调试」|
| 能打开应用但无法点击 | 缺少安全调试权限 | 开启「USB 调试(安全设置)」|
| 中文输入变成乱码或无输入 | ADB Keyboard 未启用 | 在系统设置中启用 ADB Keyboard |
| 截图返回黑屏 | 敏感页面(支付/银行) | 正常现象，系统会自动处理 |
| 连接模型服务失败 | URL 错误或服务未启动 | 检查 URL，确认服务正在运行 |
| `ModuleNotFoundError` | 依赖未安装 | 执行 `pip install -r requirements.txt` |

---

### 部署要点

1. **优先确认手机连接**：在安装任何代码之前，先确保 `adb devices` 能看到设备
2. **不要跳过 ADB Keyboard**：没有它，中文输入会失败
3. **模型服务是外部依赖**：Agent 代码本身不包含模型，需要单独的模型服务
4. **遇到权限问题先检查手机设置**：大部分问题都是手机端配置不完整
5. **部署完成后用简单任务测试**：建议用「打开微信发消息给文件传输助手」作为验收标准

---

### 命令速查

```bash
# 检查 ADB 连接
adb devices

# 重启 ADB 服务
adb kill-server && adb start-server

# 安装依赖
pip install -r requirements.txt && pip install -e .

# 运行 Agent(交互模式)
python main.py --base-url {MODEL_URL} --model "autoglm-phone-9b"

# 运行 Agent(单次任务)
python main.py --base-url {MODEL_URL} --model "autoglm-phone-9b" "你的任务描述"

# 查看支持的应用列表
python main.py --list-apps
```

---

**部署完成的标志：手机能自动执行用户的自然语言指令。**
