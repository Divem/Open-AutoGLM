# Change: 增强任务详情弹框支持Markdown格式内容渲染

## Why
当前任务详情弹框已实现滚动显示功能（`optimize-modal-task-details-display`），但执行结果仅支持纯文本显示。随着AI生成内容的复杂度增加，执行结果可能包含格式化的Markdown内容（如标题、列表、代码块、链接等），当前实现存在以下限制：

1. **格式丢失** - Markdown格式无法正确渲染，影响内容可读性
2. **结构混乱** - 代码块、列表等结构以纯文本形式显示，难以理解
3. **用户体验差** - 富文本内容显示为纯文本，降低信息传达效率
4. **功能局限** - 无法利用Markdown的优势（如链接可点击、代码高亮等）

需要在现有滚动功能基础上，增加Markdown渲染能力，提升内容展示效果。

## What Changes
- **扩展现有滚动容器功能**：在保持滚动显示的基础上，增加Markdown内容渲染支持
- **智能内容检测**：自动检测内容是否为Markdown格式，选择性渲染
- **安全性增强**：实现XSS防护，确保渲染的Markdown内容安全
- **向后兼容**：保持对纯文本内容的完全兼容，不影响现有功能
- **性能优化**：优化Markdown渲染性能，避免阻塞UI

## Impact
- **Affected specs**: web-ui-modal-display（修改现有规范）
- **Affected code**:
  - `web/static/js/app.js` - 扩展任务详情弹框渲染逻辑（第1170-1189行）
  - `web/static/css/style.css` - 添加Markdown渲染样式支持
  - `web/templates/index.html` - 确保marked.js库可用（已存在）
- **User Experience**: 显著提升富文本内容的可读性和交互体验
- **Breaking Changes**: 否，完全向后兼容的增强功能
- **Security**: 需要实施XSS防护措施

## Technical Considerations
- **Markdown渲染引擎**: 使用已引入的marked.js库进行渲染
- **XSS防护**: 使用DOMPurify或自定义过滤器清理HTML
- **内容检测策略**: 检测常见的Markdown语法模式
- **性能优化**: 对超长内容实施分段渲染或虚拟滚动
- **样式隔离**: 确保Markdown样式不影响弹框其他部分
- **响应式设计**: 在滚动容器内保持良好的响应式表现