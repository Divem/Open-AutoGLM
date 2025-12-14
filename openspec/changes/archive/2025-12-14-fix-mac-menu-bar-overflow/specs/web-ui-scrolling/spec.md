## ADDED Requirements

### Requirement: Mac Safe Area Adaptation
Web界面 **SHALL** 在Mac设备上自动适配系统UI元素占用的空间。

#### Scenario: Input area avoids Dock bar on Mac
- **WHEN** 在macOS设备上使用Web界面
- **THEN** 输入区域**SHALL**自动添加底部安全间距
- **AND** 安全间距**SHALL**至少等于系统Dock栏的高度
- **AND** 输入框**SHALL**完全可见且可操作
- **AND** 安全间距**SHALL**使用CSS env(safe-area-inset-bottom)计算

#### Scenario: CSS safe-area-inset support
- **WHEN** 浏览器支持CSS环境变量
- **THEN** 样式表**SHALL**使用env(safe-area-inset-*)属性
- **AND** padding-bottom**SHALL**设置为env(safe-area-inset-bottom)
- **AND** 备用值**SHALL**提供回退支持
- **AND** **SHALL NOT**在不支持的浏览器中产生错误

#### Scenario: Dynamic height calculation for Mac
- **WHEN** 页面在Mac设备上加载
- **THEN** 主容器高度**SHALL**考虑可用视口空间
- **AND** 聊天容器高度**SHALL**自动调整以适应屏幕
- **AND** 输入区域**SHALL**始终保持在可见区域内
- **AND** 滚动行为**SHALL**保持流畅和自然

### Requirement: Mac Browser Specific Optimization
Web界面 **SHALL** 针对Mac上的主流浏览器进行特殊优化。

#### Scenario: Safari browser optimization
- **WHEN** 在macOS Safari浏览器中使用
- **THEN** **SHALL**应用Safari特定的CSS优化
- **AND** **SHALL**使用-webkit-appearance确保原生外观
- **AND** **SHALL**避免Safari已知的布局bug
- **AND** 触摸滚动**SHALL**保持平滑响应

#### Scenario: Chrome browser optimization
- **WHEN** 在macOS Chrome浏览器中使用
- **THEN** **SHALL**应用Chrome特定的CSS前缀
- **AND** **SHALL**优化渲染性能
- **AND** **SHALL**确保与Safari行为一致
- **AND** 滚动条样式**SHALL**与系统主题匹配

#### Scenario: Firefox browser optimization
- **WHEN** 在macOS Firefox浏览器中使用
- **THEN** **SHALL**应用Firefox特定的样式调整
- **AND** **SHALL**确保与其他浏览器体验一致
- **AND** **SHALL**处理Firefox特有的布局差异

### Requirement: Responsive Layout for Mac Screens
Web界面 **SHALL** 在Mac的不同屏幕尺寸和分辨率下正常工作。

#### Scenario: MacBook Air/Pro adaptation
- **WHEN** 在MacBook笔记本屏幕上使用
- **THEN** 布局**SHALL**自动适配较小屏幕尺寸
- **AND** 输入区域**SHALL**保持可访问性
- **AND** 侧边面板**SHALL**可适当缩放或调整
- **AND** 所有UI元素**SHALL**在视口内可见

#### Scenario: External monitor support
- **WHEN** 连接外部显示器使用
- **THEN** 布局**SHALL**利用更大的屏幕空间
- **AND** 安全区域计算**SHALL**基于主显示器设置
- **AND** 用户**SHALL**能够在显示器间移动窗口
- **AND** 布局**SHALL**保持比例和美观

#### Scenario: Retina display optimization
- **WHEN** 在高分辨率Retina显示屏上使用
- **THEN** 所有UI元素**SHALL**保持清晰锐利
- **AND** 图标和文字**SHALL**适当缩放
- **AND** 边框和阴影**SHALL**渲染精细
- **AND** 触摸目标**SHALL**保持适当大小

### Requirement: Cross-Platform Compatibility
Mac适配 **SHALL** 不影响其他平台的用户体验。

#### Scenario: Windows platform unaffected
- **WHEN** 在Windows系统上使用相同代码
- **THEN** 所有功能**SHALL**正常工作
- **AND** 输入区域**SHALL**保持原有布局
- **AND** **SHALL NOT**出现不必要的间距
- **AND** 性能**SHALL**不受影响

#### Scenario: Linux platform unaffected
- **WHEN** 在Linux系统上使用相同代码
- **THEN** Web界面**SHALL**正常显示
- **AND** 所有交互功能**SHALL**可用
- **AND** **SHALL NOT**出现Mac特有的样式
- **AND** 浏览器兼容性**SHALL**保持

#### Scenario: Mobile devices unaffected
- **WHEN** 在iOS或Android设备上访问
- **THEN** 移动优化**SHALL**继续工作
- **AND** 触摸交互**SHALL**正常响应
- **AND** **SHALL NOT**引入桌面特定的样式问题
- **AND** 响应式布局**SHALL**保持稳定

### Requirement: Performance and Accessibility
Mac适配 **SHALL** 保持良好的性能和可访问性。

#### Scenario: Performance impact minimal
- **WHEN** 应用Mac适配代码
- **THEN** 页面加载时间**SHALL**不受明显影响
- **AND** 滚动性能**SHALL**保持流畅
- **AND** JavaScript执行**SHALL**高效
- **AND** 内存使用**SHALL**不显著增加

#### Scenario: Accessibility standards maintained
- **WHEN** 屏幕阅读器访问Web界面
- **THEN** 所有元素**SHALL**保持可访问
- **AND** 键盘导航**SHALL**正常工作
- **AND** ARIA标签**SHALL**保持准确
- **AND** 焦点管理**SHALL**不被破坏

#### Scenario: Animation and transitions preserved
- **WHEN** 界面元素状态变化
- **THEN** 现有动画效果**SHALL**继续工作
- **AND** 过渡效果**SHALL**保持流畅
- **AND** **SHALL NOT**出现视觉断层
- **AND** 用户体验**SHALL**保持连贯

## MODIFIED Requirements

### Requirement: Input Box Must Be Always Accessible
对话输入框 **SHALL** 在所有情况下都可访问，包括Mac系统的UI遮挡场景。

#### Scenario: Input box accessible on Mac with Dock
- **WHEN** 在Mac设备上，Dock栏可能遮挡内容
- **THEN** 输入框**SHALL**通过安全区域适配保持可见
- **AND** 输入框底部**SHALL**保持与Dock栏的安全距离
- **AND** 用户**SHALL**能够正常点击和输入
- **AND** 输入框**SHALL**不会被系统UI元素遮挡

#### Scenario: Input box visible during page load on Mac
- **WHEN** Mac用户首次加载Web界面
- **THEN** 输入区域**SHALL**立即考虑安全区域
- **AND** **SHALL NOT**出现布局抖动
- **AND** 输入框位置**SHALL**立即正确
- **AND** 用户**SHALL**能够立即开始输入

#### Scenario: Input box remains accessible when window resized on Mac
- **WHEN** Mac用户调整浏览器窗口大小
- **THEN** 输入区域**SHALL**动态调整安全间距
- **AND** 输入框**SHALL**始终保持可见
- **AND** 滚动行为**SHALL**保持正确
- **AND** 布局**SHALL**不出现错乱