## Context
Open-AutoGLM的Web界面在Mac设备上遇到UI遮挡问题，特别是底部的对话输入区域被系统的Dock栏或菜单栏遮挡。这影响了Mac用户的基本交互体验。Mac操作系统有独特的UI布局，包括底部的Dock栏和顶部的菜单栏，这些系统UI元素会占用屏幕空间，导致Web应用的内容区域被压缩或遮挡。

## Goals / Non-Goals
### Goals
- 确保Mac用户可以无障碍地访问对话输入区域
- 保持跨平台的一致性和兼容性
- 实现自动化的布局适配，无需用户手动调整
- 遵循Apple的Human Interface Guidelines
- 支持不同的Dock栏大小和位置设置

### Non-Goals
- 修改系统UI行为或外观
- 仅支持特定版本的macOS
- 使用复杂的第三方库或框架
- 改变整体的设计风格和布局结构

## Decisions

### Decision 1: 使用CSS Safe Area Insets
- **What**: 采用CSS的env()函数和safe-area-inset-*变量
- **Why**: 这是Apple推荐的标准做法，自动适配不同设备的安全区域
- **Alternatives considered**:
  - 固定底部间距（不够灵活）
  - JavaScript动态计算（性能开销大）
  - 媒体查询硬编码（无法适应Dock栏大小变化）

### Decision 2: 渐进增强策略
- **What**: 在现有布局基础上添加Mac特定适配，不破坏其他平台
- **Why**: 确保向后兼容性，降低引入新bug的风险
- **Alternatives considered**:
  - 重写整个布局系统（风险太高）
  - 创建Mac专属版本（维护成本高）

### Decision 3: 多层适配机制
- **What**: 结合CSS safe-area-inset、媒体查询和JavaScript检测
- **Why**: 最大化兼容性，处理不同浏览器和系统版本的差异
- **Alternatives considered**:
  - 仅使用CSS（某些旧版浏览器不支持）
  - 仅使用JavaScript（性能和可靠性问题）

## Risks / Trade-offs

### Risks
- **浏览器兼容性**: 旧版Safari可能不完全支持safe-area-inset
- **性能影响**: 动态计算可能影响滚动性能
- **视觉不一致**: 不同Mac设备上的显示效果可能略有差异

### Trade-offs
- **代码复杂性 vs 用户体验**: 增加了一些CSS和JavaScript复杂性，但显著改善了用户体验
- **维护成本 vs 平台覆盖**: 需要维护跨平台代码，但确保了所有用户的良好体验

## Migration Plan

### Phase 1: CSS适配（低风险）
1. 添加safe-area-inset支持到现有CSS
2. 修改.input-area和.main-container的样式
3. 测试基本功能不受影响

### Phase 2: 增强适配（中风险）
1. 添加Mac特定的媒体查询
2. 实现JavaScript动态检测和调整
3. 进行全面的跨平台测试

### Phase 3: 优化和文档（低风险）
1. 根据测试结果进行微调
2. 完善文档和注释
3. 准备生产部署

### Rollback Plan
- 保留原始CSS类的备份
- 使用特性检测确保降级方案
- 准备快速回滚脚本

## Open Questions
- 是否需要检测Dock栏的位置（底部 vs 侧边）？
- 如何处理外接显示器的情况？
- 是否需要支持全屏模式下的特殊适配？
- 如何测试不同Dock栏大小设置的效果？