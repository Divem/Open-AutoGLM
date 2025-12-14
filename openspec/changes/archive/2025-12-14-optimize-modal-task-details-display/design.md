# Design: 任务详情弹框内执行结果显示优化

## Context
当前任务详情弹框的执行结果显示存在以下问题：
- 执行结果直接显示在弹框的 `.modal-body` 中
- 长文本内容会撑高整个弹框，影响用户体验
- 缺乏独立的滚动控制，用户难以浏览大量输出
- 在小屏幕设备上显示效果不佳

### 现有实现分析
```javascript
// 当前实现 - 执行结果直接显示
${task.result ? `
    <div class="row mb-3">
        <div class="col-sm-3"><strong>执行结果:</strong></div>
        <div class="col-sm-9">
            <div class="alert alert-info">
                <pre style="white-space: pre-wrap; margin: 0;">${this.escapeHtml(task.result)}</pre>
            </div>
        </div>
    </div>
` : ''}
```

## Goals / Non-Goals
- **Goals**:
  - 为执行结果提供独立的滚动显示区域
  - 限制弹框的最大高度，避免界面撑满屏幕
  - 提供良好的长内容浏览体验
  - 保持弹框的整体布局结构不变
  - 确保在不同屏幕尺寸下的响应式表现

- **Non-Goals**:
  - 不改变弹框的基本交互行为
  - 不影响其他任务信息的显示方式
  - 不增加额外的JavaScript复杂度
  - 不改变弹框的触发和关闭机制

## Decisions

### Decision 1: 使用CSS固定高度和滚动容器
**理由**：
- 简单可靠的解决方案，性能良好
- 无需复杂的JavaScript逻辑
- 浏览器原生滚动支持，兼容性好

**实现方式**：
```css
.task-result-container {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
}
```

### Decision 2: 保持现有弹框尺寸，优化内容布局
**理由**：
- 不破坏用户的使用习惯
- `modal-lg` 尺寸已经足够显示大部分内容
- 通过内容优化而非容器尺寸调整来改善体验

**布局策略**：
- 执行结果区域使用固定最大高度
- 其他任务信息保持现有布局
- 滚动区域有明确的视觉边界

### Decision 3: 视觉层次优化
**理由**：
- 明确区分可滚动区域和固定内容
- 提供清晰的视觉提示
- 保持与现有设计风格一致

**设计要素**：
- 使用边框和背景色区分滚动区域
- 添加轻微的阴影效果
- 保持Bootstrap样式的统一性

### Decision 4: 响应式适配
**考虑因素**：
- 小屏幕设备的空间限制
- 移动设备的滚动体验
- 不同分辨率下的显示效果

**适配策略**：
- 在小屏幕上降低滚动区域的最大高度
- 使用相对单位而非固定像素
- 确保触摸滚动体验良好

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 内容截断 | 低 | 设置合理的最大高度，提供完整滚动访问 |
| 样式冲突 | 低 | 使用具体的选择器，避免影响其他模态框 |
| 性能影响 | 极低 | 纯CSS解决方案，无JavaScript开销 |
| 兼容性问题 | 低 | 使用标准CSS属性，现代浏览器支持良好 |

### Trade-offs
- **固定高度 vs. 自适应高度**: 选择固定最大高度以避免界面撑满，提供更可控的用户体验
- **简单性 vs. 功能性**: 选择简单的CSS滚动解决方案，避免过度工程化

## Implementation Details

### CSS样式设计
```css
/* 执行结果容器样式 */
.task-result-container,
.task-error-container {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    background-color: #f8f9fa;
    margin-top: 0.5rem;
}

/* 滚动条样式优化 */
.task-result-container::-webkit-scrollbar,
.task-error-container::-webkit-scrollbar {
    width: 6px;
}

.task-result-container::-webkit-scrollbar-track,
.task-error-container::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

.task-result-container::-webkit-scrollbar-thumb,
.task-error-container::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

.task-result-container::-webkit-scrollbar-thumb:hover,
.task-error-container::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

/* 响应式调整 */
@media (max-height: 768px) {
    .task-result-container,
    .task-error-container {
        max-height: 200px;
    }
}
```

### HTML结构调整
```javascript
// 新的HTML结构
${task.result ? `
    <div class="row mb-3">
        <div class="col-sm-3"><strong>执行结果:</strong></div>
        <div class="col-sm-9">
            <div class="task-result-container">
                <pre style="white-space: pre-wrap; margin: 0; padding: 1rem;">${this.escapeHtml(task.result)}</pre>
            </div>
        </div>
    </div>
` : ''}
```

## Migration Plan

### 阶段1：CSS样式添加
1. 在 `style.css` 中添加滚动容器样式
2. 添加响应式断点调整
3. 优化滚动条外观

### 阶段2：JavaScript结构调整
1. 修改任务详情弹框的HTML生成逻辑
2. 为执行结果和错误信息添加滚动容器
3. 调整内容区域的间距和布局

### 阶段3：测试和优化
1. 测试不同长度的内容显示效果
2. 验证响应式布局在不同设备上的表现
3. 优化用户体验细节

### 回滚计划
如需回滚：
- 保留原始HTML结构注释
- 维护CSS样式的版本控制
- 记录修改的具体位置和内容

## Open Questions
- 是否需要在滚动区域顶部添加"执行结果"标题？
- 是否为超长内容提供"展开全部"的选项？
- 是否需要添加内容复制到剪贴板的功能？
- 滚动区域的最大高度是否需要根据内容长度动态调整？

## Accessibility Considerations
- 确保滚动区域支持键盘导航（Tab/方向键）
- 提供适当的ARIA标签（`role="region"`, `aria-label`）
- 确保屏幕阅读器能够正确读取滚动内容
- 维持足够的颜色对比度
- 支持高对比度模式显示