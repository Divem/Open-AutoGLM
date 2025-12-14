# Change: Fix Mac Menu Bar Overflow Issue

## Why
用户在Mac设备上使用Web界面时，报告下方的对话输入区域被系统菜单栏或Dock栏遮挡，导致无法正常输入和交互。这影响了Mac用户的基本使用体验，需要通过安全的区域适配和响应式布局来解决。

## What Changes
- 为Web界面添加Mac系统特定的安全区域适配（safe area inset）
- 实现动态底部间距调整机制，避免Dock栏和菜单栏遮挡
- 增强响应式布局，确保在不同屏幕尺寸下输入区域可访问
- 添加CSS环境变量检测，支持Mac特有的UI元素空间预留
- 优化滚动行为，确保内容区域正确适配系统UI

## Impact
- **Affected specs**: web-ui-scrolling
- **Affected code**: web/static/css/style.css, web/templates/index.html
- **Platform impact**: 主要改善Mac用户体验，同时保持跨平台兼容性
- **User experience**: 解决输入遮挡问题，提升Mac用户的操作便利性