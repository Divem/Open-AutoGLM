# 布局优化规格

## ADDED Requirements

### Requirement: 移除顶部导航栏
Web界面 **SHALL** 完全移除当前的顶部navbar，为对话区域释放垂直空间，简化界面结构。

#### Scenario: 用户访问主界面时，不再看到顶部导航栏
- **Given**: 用户访问Open-AutoGLM Web界面
- **When**: 页面加载完成
- **Then**: 界面直接从聊天header开始，无顶部navbar
- **And**: 整个界面垂直空间增加约30px

#### Scenario: 移除navbar后的品牌标识
- **Given**: 用户在主界面
- **When**: 查看界面顶部
- **Then**: 应用品牌信息"Terminal Agent"显示在聊天header中
- **And**: 保持与原设计相似的视觉层次

### Requirement: 优化聊天header布局
Web界面 **SHALL** 重新设计聊天区域header，集成原navbar的功能，保持信息显示的完整性。

#### Scenario: 连接状态显示优化
- **Given**: 用户在主界面
- **When**: Socket.IO连接状态发生变化
- **Then**: 连接状态指示器显示在聊天header右侧
- **And**: 状态样式保持视觉一致性（绿色=已连接，红色=断开）
- **And**: 会话ID继续显示，字体大小适中

#### Scenario: 配置入口重新设计
- **Given**: 用户需要在主界面访问配置
- **When**: 查看聊天header
- **Then**: 配置按钮集成到header右侧，使用齿轮图标
- **And**: 按钮悬停时显示"配置"提示文字
- **And**: 保持原配置页面的所有功能

### Requirement: 响应式布局增强
Web界面 **SHALL** 在移除navbar后，重新调整移动端和桌面端的布局，确保各设备上的最佳体验。

#### Scenario: 移动端布局优化
- **Given**: 用户在移动设备上访问界面
- **When**: 页面加载完成
- **Then**: 聊天header高度适应移动端（约50px）
- **And**: 连接状态和配置按钮保持可点击性
- **And**: 文字大小适合移动端阅读

#### Scenario: 桌面端空间利用
- **Given**: 用户在桌面端访问界面
- **When**: 窗口大小调整
- **Then**: 对话区域利用释放的垂直空间
- **And**: 保持合理的最大宽度限制
- **And**: 输入区域位置稳定

## MODIFIED Requirements

### Requirement: 主容器布局结构
Web界面 **SHALL** 调整主容器的flex布局结构，适配移除navbar后的新布局。

#### Scenario: 容器高度分配
- **Given**: 页面结构中没有navbar
- **When**: 页面渲染
- **Then**: 主容器占据100vh高度
- **And**: 聊天容器使用剩余的可用空间
- **And**: 输入区域保持在底部

#### Scenario: Flex布局调整
- **Given**: 新的页面结构
- **When**: CSS flex布局应用
- **Then**: .main-container直接包含chat-header、chat-container、input-area
- **And**: 各区域高度合理分配
- **And**: 滚动行为正确

### Requirement: 视觉层次重新平衡
Web界面 **SHALL** 在移除navbar后，重新平衡界面各元素的视觉权重和层次。

#### Scenario: 标题显示优化
- **Given**: 移除了navbar的品牌显示
- **When**: 用户查看聊天header
- **Then**: "Terminal Assistant"标题保持显著位置
- **And**: 图标和文字搭配合理
- **And**: 保持与原设计的一致性

#### Scenario: 功能元素布局
- **Given**: header集成了更多功能
- **When**: 用户查看header右侧
- **Then**: 连接状态、会话ID、配置按钮合理排列
- **And**: 各元素间距适中，视觉平衡
- **And**: 不同屏幕尺寸下保持可用性

## REMOVED Requirements

### Requirement: 顶部导航栏组件
Web界面 **SHALL NOT** 包含原有的navbar组件及其相关样式和功能。

#### Scenario: navbar元素移除
- **Given**: 原有的navbar组件存在于index.html
- **When**: 布局优化实施
- **Then**: `<nav class="navbar">` 元素完全移除
- **And**: 相关的Bootstrap navbar类不再使用
- **And**: navbar相关的CSS样式清理

#### Scenario: 导航功能重新分配
- **Given**: navbar中的配置链接功能
- **When**: navbar被移除
- **Then**: 配置功能重新集成到聊天header
- **And**: 保持原有的路由和功能不变
- **And**: 用户体验无缝过渡