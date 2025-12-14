# Change: Optimize Task Details Display Layout

## Why
用户反馈当前执行结果详情在对话框中显示时，内容过长会超出屏幕边界，导致用户体验不佳。现有的模态框方式无法很好地处理长文本内容的展示和滚动。

## What Changes
- **优化任务详情布局结构**：将执行结果从模态框中分离，使用专门的列或区域显示
- **实现垂直滚动支持**：为长内容添加独立滚动区域，确保内容不会超出视口
- **改进响应式设计**：在不同屏幕尺寸下都能提供良好的查看体验
- **增强用户交互**：提供更好的滚动控制和内容导航功能

## Impact
- **Affected specs**: web-ui-scrolling（现有规格需要扩展）
- **Affected code**:
  - web/templates/index.html（布局结构调整）
  - web/static/css/style.css（新增滚动和布局样式）
  - web/static/js/app.js（任务详情显示逻辑重构）
- **User experience**: 显著改善长任务结果的可读性和操作便利性
- **Compatibility**: 保持与现有功能的兼容性，不破坏当前交互流程

## Technical Considerations
- **Breaking changes**: 否，所有改动都是增量式优化
- **Performance impact**: 最小化，主要使用CSS优化和少量JavaScript调整
- **Browser compatibility**: 支持所有现代浏览器的滚动特性
- **Accessibility**: 确保键盘导航和屏幕阅读器支持