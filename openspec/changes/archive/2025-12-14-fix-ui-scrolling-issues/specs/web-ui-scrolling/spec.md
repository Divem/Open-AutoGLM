# Spec: Web UI Scrolling and Input Accessibility

## ADDED Requirements

### Requirement: Page Must Support Vertical Scrolling
Web界面 **SHALL** 支持垂直滚动以访问所有页面内容。

#### Scenario: Vertical scrollbar appears when content overflows
- **WHEN** 页面内容高度超过视口高度
- **THEN** 浏览器**SHALL**显示垂直滚动条
- **AND** 用户**SHALL**能够通过滚动访问所有内容
- **AND** 滚动条**SHALL**出现在页面右侧(标准位置)

#### Scenario: User can scroll to access all content
- **WHEN** 用户使用鼠标滚轮、触摸手势或滚动条
- **THEN** 页面**SHALL**垂直滚动
- **AND** 用户**SHALL**能够访问页面顶部到底部的所有内容
- **AND** 滚动**SHALL**平滑且响应迅速

#### Scenario: body element overflow property allows scrolling
- **WHEN** 检查body元素的CSS overflow属性
- **THEN** overflow属性**SHALL**设置为`auto`或默认值(非`hidden`)
- **AND** overflow-y**SHALL NOT**设置为`hidden`
- **AND** 页面**SHALL**允许垂直滚动行为

### Requirement: Input Box Must Be Always Accessible
对话输入框 **SHALL** 在所有情况下都可访问。

#### Scenario: Input box is visible on page load
- **WHEN** 用户首次打开Web界面
- **THEN** 对话输入框**SHALL**完全可见
- **AND** 输入框**SHALL**位于聊天区域底部
- **AND** 发送按钮和停止按钮**SHALL**可见

#### Scenario: Input box remains accessible when content overflows
- **WHEN** 聊天消息数量增加导致内容溢出
- **THEN** 用户**SHALL**能够通过滚动到达输入框
- **AND** 输入框**SHALL**完全可见,不被遮挡
- **AND** 输入框**SHALL**可以正常输入和提交

#### Scenario: Input box is accessible on small screens
- **WHEN** 在小屏幕设备上使用(< 768px宽度)
- **THEN** 输入框**SHALL**仍然可访问
- **AND** 用户**SHALL**能够滚动到输入框位置
- **AND** 输入框**SHALL**响应式适配屏幕宽度

### Requirement: Internal Scroll Areas Must Work Independently
内部滚动区域 **SHALL** 独立于页面滚动工作。

#### Scenario: Chat container scrolls independently
- **WHEN** 聊天消息填满聊天容器
- **THEN** 聊天容器**SHALL**在其内部显示滚动条
- **AND** 聊天容器滚动**SHALL NOT**触发页面整体滚动
- **AND** 页面滚动**SHALL NOT**影响聊天容器滚动位置

#### Scenario: Side panel scrolls independently
- **WHEN** 右侧面板内容超过其容器高度
- **THEN** 侧边面板**SHALL**显示独立的滚动条
- **AND** 侧边面板滚动**SHALL NOT**触发页面整体滚动
- **AND** 页面滚动**SHALL NOT**影响侧边面板滚动位置

#### Scenario: Multiple scroll areas do not interfere
- **WHEN** 页面存在多个滚动区域(页面、聊天容器、侧边面板)
- **THEN** 每个滚动区域**SHALL**独立工作
- **AND** 滚动一个区域**SHALL NOT**影响其他区域
- **AND** 滚动事件**SHALL**正确隔离(event.stopPropagation where needed)

### Requirement: Scrolling Must Work Across All Screen Sizes
滚动功能 **SHALL** 在所有屏幕尺寸上正常工作。

#### Scenario: Scrolling works on desktop screens
- **WHEN** 在桌面屏幕使用(≥ 1024px宽度)
- **THEN** 垂直滚动**SHALL**正常工作
- **AND** 输入框**SHALL**可访问
- **AND** 滚动条**SHALL**可见且可操作

#### Scenario: Scrolling works on tablet screens
- **WHEN** 在平板设备使用(768px - 1023px宽度)
- **THEN** 垂直滚动**SHALL**正常工作
- **AND** 输入框**SHALL**可访问
- **AND** 触摸滚动手势**SHALL**正常响应

#### Scenario: Scrolling works on mobile screens
- **WHEN** 在手机设备使用(< 768px宽度)
- **THEN** 垂直滚动**SHALL**正常工作
- **AND** 输入框**SHALL**可访问
- **AND** 触摸滚动手势**SHALL**平滑响应
- **AND** 布局**SHALL**响应式适配

### Requirement: Scrolling Must Be Browser Compatible
滚动功能 **SHALL** 兼容所有主流浏览器。

#### Scenario: Scrolling works in Chrome/Edge
- **WHEN** 在Chrome或Edge浏览器使用
- **THEN** 所有滚动功能**SHALL**正常工作
- **AND** 滚动行为**SHALL**符合浏览器标准
- **AND** 无特定浏览器bug

#### Scenario: Scrolling works in Firefox
- **WHEN** 在Firefox浏览器使用
- **THEN** 所有滚动功能**SHALL**正常工作
- **AND** 滚动条样式**SHALL**使用浏览器默认或自定义样式
- **AND** 无特定浏览器bug

#### Scenario: Scrolling works in Safari
- **WHEN** 在Safari浏览器使用(macOS/iOS)
- **THEN** 所有滚动功能**SHALL**正常工作
- **AND** 触摸滚动**SHALL**平滑且自然(iOS)
- **AND** 无特定浏览器bug

### Requirement: Page Layout Must Remain Stable
页面布局 **SHALL** 在修复滚动问题后保持稳定。

#### Scenario: Flexbox layout continues to work correctly
- **WHEN** 修复`body overflow`属性后
- **THEN** 现有flexbox布局**SHALL**保持不变
- **AND** 聊天区域**SHALL**占据剩余空间(flex: 1)
- **AND** 侧边面板**SHALL**保持固定宽度(380px)
- **AND** 输入框**SHALL**固定在聊天区域底部(flex-shrink: 0)

#### Scenario: No visual regressions occur
- **WHEN** 修复应用后
- **THEN** 所有UI元素**SHALL**保持正确位置
- **AND** 颜色、字体、间距**SHALL**不变
- **AND** 动画和过渡效果**SHALL**正常工作
- **AND** 无布局错乱或重叠

#### Scenario: No double scrollbars appear
- **WHEN** 页面和内部容器都可滚动
- **THEN** **SHALL NOT**出现双滚动条问题
- **AND** 页面滚动和内部滚动**SHALL**清晰区分
- **AND** 用户体验**SHALL**直观且自然

## Acceptance Criteria

### 核心功能验收

1. ✅ **输入框可访问性**:
   - 任何情况下都可以滚动到输入框
   - 输入框完全可见,无遮挡
   - 可以正常输入和提交

2. ✅ **垂直滚动功能**:
   - 内容溢出时出现滚动条
   - 可以使用鼠标、键盘、触摸滚动
   - 可以访问所有页面内容

3. ✅ **内部滚动独立性**:
   - 聊天容器独立滚动
   - 侧边面板独立滚动
   - 不同滚动区域互不干扰

### 跨平台验收

4. ✅ **多屏幕尺寸支持**:
   - 桌面(≥1024px)正常工作
   - 平板(768-1023px)正常工作
   - 手机(<768px)正常工作

5. ✅ **浏览器兼容性**:
   - Chrome/Edge正常工作
   - Firefox正常工作
   - Safari正常工作(如有条件)

### 质量验收

6. ✅ **无副作用**:
   - 现有布局保持不变
   - 无视觉回归问题
   - 无双滚动条问题

7. ✅ **用户体验**:
   - 滚动平滑响应
   - 触摸手势自然
   - 无性能问题

## Non-Functional Requirements

### 性能要求
- 滚动帧率≥60fps
- 滚动响应延迟<16ms
- 无卡顿或掉帧

### 可访问性要求
- 符合WCAG 2.1 AA级标准
- 键盘导航支持(Tab, Space, Arrow keys)
- 屏幕阅读器兼容

### 兼容性要求
- 支持Chrome 90+
- 支持Firefox 88+
- 支持Safari 14+
- 支持Edge 90+

## Testing Strategy

### 手动测试
```
测试用例1: 输入框可见性
前置条件: 打开Web界面
步骤:
1. 发送20条测试消息
2. 滚动到页面底部
3. 检查输入框是否完全可见
期望: ✅ 输入框完全可见且可交互
```

```
测试用例2: 垂直滚动
前置条件: 打开Web界面
步骤:
1. 发送足够多的消息使内容溢出
2. 观察是否出现垂直滚动条
3. 使用鼠标滚轮滚动
4. 使用滚动条拖动滚动
期望: ✅ 滚动功能正常工作
```

```
测试用例3: 多屏幕尺寸
前置条件: 打开Web界面
步骤:
1. 使用浏览器开发工具调整窗口大小
2. 测试1920x1080, 1366x768, 768x1024, 375x667
3. 验证每个尺寸下滚动和输入框可见性
期望: ✅ 所有尺寸正常工作
```

### 自动化测试(可选)
```javascript
// Cypress E2E测试
describe('UI Scrolling', () => {
    it('should show input when scrolled to bottom', () => {
        cy.visit('/');
        // 发送多条消息
        for (let i = 0; i < 20; i++) {
            cy.get('#task-input').type(`Test ${i}{enter}`);
        }
        // 滚动到底部
        cy.scrollTo('bottom');
        // 验证输入框可见
        cy.get('#task-input').should('be.visible');
        cy.get('#send-btn').should('be.visible');
    });

    it('should have correct overflow property', () => {
        cy.visit('/');
        cy.get('body').should('have.css', 'overflow')
          .and('not.equal', 'hidden');
    });
});
```

## Migration Plan

### 阶段1: CSS修复
1. 修改`web/static/css/style.css:10`
2. 移除或修改`overflow: hidden`为`overflow: auto`

### 阶段2: 验证
1. 清除浏览器缓存
2. 手动测试所有场景
3. 多浏览器测试

### 阶段3: 监控
1. 收集用户反馈
2. 监控错误日志
3. 必要时微调

## Rollback Plan

如果出现问题,回滚步骤:

1. **立即回滚**: 恢复`body { overflow: hidden; }`
2. **清除缓存**: 强制刷新页面
3. **调查根因**: 检查是否其他CSS冲突
4. **替代方案**: 考虑其他布局方案

**触发条件**:
- 出现双滚动条且无法解决
- 布局严重错乱
- 用户无法正常使用

## Related Specifications

- Web Content Accessibility Guidelines (WCAG) 2.1
- CSS Flexible Box Layout Module
- HTML Living Standard - Scrolling
- Bootstrap 5 Documentation

## References

- Current implementation: `web/static/css/style.css`
- Current template: `web/templates/index.html`
- Related issue: 对话输入框被遮挡,垂直滚动条消失
