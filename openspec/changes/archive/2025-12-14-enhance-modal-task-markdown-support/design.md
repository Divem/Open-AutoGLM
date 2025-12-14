# Design: 任务详情弹框Markdown渲染增强设计

## Context
基于已实现的滚动显示功能（`optimize-modal-task-details-display`），当前执行结果使用 `<pre>` 标签显示纯文本内容：

```javascript
// 现有实现 - app.js 第1170-1179行
${task.result ? `
    <div class="row mb-3">
        <div class="col-sm-3"><strong>执行结果:</strong></div>
        <div class="col-sm-9">
            <div class="task-result-container">
                <pre>${this.escapeHtml(task.result)}</pre>
            </div>
        </div>
    </div>
` : ''}
```

项目已引入 marked.js 库（`index.html:228`），为Markdown渲染提供了基础。需要在此功能基础上增强，支持富文本内容的正确渲染。

### 技术背景
- **Markdown库**: marked.js v9.1.6 (已引入)
- **滚动容器**: `.task-result-container` 和 `.task-error-container` (已实现)
- **安全考虑**: 需要防止XSS攻击
- **性能要求**: 长内容渲染不阻塞UI

## Goals / Non-Goals
- **Goals**:
  - 智能检测Markdown格式内容并正确渲染
  - 保持现有滚动功能和样式不变
  - 实施严格的安全防护，防止XSS攻击
  - 提供优雅的降级机制，纯文本内容正常显示
  - 优化渲染性能，确保流畅的用户体验
  - 支持常见Markdown元素：标题、列表、代码块、链接、粗体、斜体等

- **Non-Goals**:
  - 不修改现有的滚动容器结构和样式
  - 不改变弹框的基本交互行为
  - 不支持复杂的Markdown扩展语法
  - 不提供Markdown编辑功能
  - 不改变其他任务信息的显示方式

## Decisions

### Decision 1: 智能内容检测策略
**理由**：
- 避免对纯文本内容进行不必要的渲染
- 减少性能开销和安全风险
- 提供更好的用户体验

**检测规则**：
```javascript
// Markdown内容检测函数
function isMarkdownContent(text) {
    const markdownPatterns = [
        /^#+\s/m,                    // 标题
        /^\*{1,2}[^*]+\*{1,2}/m,    // 粗体/斜体
        /^[-*+]\s+/m,                // 无序列表
        /^\d+\.\s+/m,                // 有序列表
        /^\[.*\]\(.*\)/m,            // 链接
        /^```[\s\S]*```/m,           // 代码块
        /^`[^`]+`/m,                 // 行内代码
        /^\>[\s\S]/m,                // 引用块
    ];
    return markdownPatterns.some(pattern => pattern.test(text));
}
```

### Decision 2: 安全渲染方案
**理由**：
- 防止XSS攻击是首要考虑
- 需要保留安全的HTML标签和属性
- 与现有安全策略保持一致

**安全策略**：
```javascript
// 使用marked.js的配置选项
marked.setOptions({
    headerIds: false,           // 禁用自动生成ID
    mangle: false,              // 禁用邮箱地址混淆
    sanitize: false,            // 使用自定义清理
    renderer: new marked.Renderer()
});

// 自定义HTML清理函数
function sanitizeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}
```

### Decision 3: 渲染容器设计
**理由**：
- 保持现有滚动功能
- 为Markdown内容提供合适的样式
- 确保内容在不同主题下的可读性

**实现方案**：
```javascript
// 条件渲染逻辑
const content = task.result;
const isMarkdown = isMarkdownContent(content);
const renderedContent = isMarkdown ? marked.parse(content) : this.escapeHtml(content);

const html = `
    <div class="row mb-3">
        <div class="col-sm-3"><strong>执行结果:</strong></div>
        <div class="col-sm-9">
            <div class="task-result-container ${isMarkdown ? 'markdown-content' : ''}">
                ${isMarkdown ?
                    `<div class="markdown-body">${renderedContent}</div>` :
                    `<pre>${renderedContent}</pre>`
                }
            </div>
        </div>
    </div>
`;
```

### Decision 4: 样式隔离策略
**理由**：
- 避免Markdown样式影响弹框其他部分
- 提供专门的内容样式
- 支持深色模式

**CSS策略**：
```css
/* Markdown内容样式容器 */
.markdown-body {
    padding: 1rem;
    line-height: 1.6;
}

/* Markdown元素样式 */
.markdown-body h1, .markdown-body h2, .markdown-body h3,
.markdown-body h4, .markdown-body h5, .markdown-body h6 {
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

.markdown-body p {
    margin: 0.5rem 0;
}

.markdown-body ul, .markdown-body ol {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
}

.markdown-body blockquote {
    margin: 0.5rem 0;
    padding: 0.5rem 1rem;
    border-left: 4px solid #ddd;
    background-color: #f8f9fa;
}

/* 代码块样式 */
.markdown-body pre {
    background-color: #f1f3f4;
    padding: 0.75rem;
    border-radius: 0.375rem;
    overflow-x: auto;
    margin: 0.5rem 0;
}

.markdown-body code {
    background-color: #f1f3f4;
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-size: 0.875em;
}

/* 链接样式 */
.markdown-body a {
    color: #007bff;
    text-decoration: none;
}

.markdown-body a:hover {
    text-decoration: underline;
}
```

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| XSS攻击 | 高 | 实施严格的HTML清理，使用白名单策略 |
| 性能问题 | 中 | 实施内容长度限制，使用异步渲染 |
| 样式冲突 | 低 | 使用scoped CSS，增加样式隔离 |
| 渲染错误 | 低 | 提供降级机制，错误时回退到纯文本 |
| 兼容性问题 | 低 | 使用标准API，测试主流浏览器 |

### Trade-offs
- **安全性 vs. 功能性**: 优先安全性，禁用可能有风险的Markdown功能
- **性能 vs. 完整性**: 对超长内容实施截断或分页，保证渲染性能
- **复杂度 vs. 可维护性**: 使用简单可靠的方案，避免过度复杂的实现

## Implementation Details

### JavaScript实现架构

```javascript
// Markdown渲染管理器
class MarkdownRenderer {
    constructor() {
        this.initMarked();
    }

    initMarked() {
        // 配置marked.js选项
        marked.setOptions({
            gfm: true,              // 启用GitHub风格Markdown
            breaks: true,           // 支持换行
            headerIds: false,       // 禁用自动ID
            sanitize: false,        // 使用自定义清理
            smartLists: true,       // 智能列表
            smartypants: false      // 禁用智能标点
        });

        // 自定义渲染器
        const renderer = new marked.Renderer();
        this.configureRenderer(renderer);
        marked.setOptions({ renderer });
    }

    configureRenderer(renderer) {
        // 自定义链接渲染 - 添加安全属性
        renderer.link = (href, title, text) => {
            const safeHref = this.sanitizeUrl(href);
            const titleAttr = title ? ` title="${this.escapeHtml(title)}"` : '';
            return `<a href="${safeHref}" target="_blank" rel="noopener noreferrer"${titleAttr}>${text}</a>`;
        };

        // 自定义代码块渲染 - 添加语言标识
        renderer.code = (code, language) => {
            const validLanguage = this.isValidLanguage(language) ? language : '';
            const langClass = validLanguage ? ` class="language-${validLanguage}"` : '';
            return `<pre><code${langClass}>${this.escapeHtml(code)}</code></pre>`;
        };
    }

    isMarkdownContent(text) {
        if (!text || typeof text !== 'string') return false;

        // 快速检查常见Markdown模式
        const patterns = [
            /^#{1,6}\s/m,                    // 标题
            /^\*{1,2}[^*\n]+\*{1,2}/m,      // 粗体/斜体
            /^[-*+]\s+/m,                    // 无序列表
            /^\d+\.\s+/m,                    // 有序列表
            /^\[.*?\]\(.*?\)/m,              // 链接
            /```[\s\S]*?```/m,               // 代码块
            /`[^`\n]+`/m,                    // 行内代码
            /^>[\s\S]/m,                     // 引用
            /^\|.*\|/m                       // 表格
        ];

        // 如果文本太短，不太可能是复杂的Markdown
        if (text.length < 20) return false;

        // 检查是否包含多个Markdown元素
        const matchCount = patterns.reduce((count, pattern) => {
            return pattern.test(text) ? count + 1 : count;
        }, 0);

        return matchCount >= 2; // 至少包含2个Markdown元素
    }

    render(content) {
        try {
            // 内容长度限制
            if (content.length > 50000) {
                console.warn('Content too long for safe rendering');
                return this.escapeHtml(content);
            }

            // 检测是否为Markdown
            if (!this.isMarkdownContent(content)) {
                return this.escapeHtml(content);
            }

            // 渲染Markdown
            const html = marked.parse(content);

            // 清理HTML（简化版，生产环境建议使用DOMPurify）
            return this.sanitizeHtml(html);

        } catch (error) {
            console.error('Markdown rendering error:', error);
            return this.escapeHtml(content);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    sanitizeHtml(html) {
        // 简单的HTML清理 - 移除危险属性和标签
        const dangerousTags = /<(script|iframe|object|embed|form|input|button)[^>]*>/gi;
        const dangerousAttrs = /(on\w+|javascript:|data:text\/html)/gi;

        return html
            .replace(dangerousTags, '')
            .replace(dangerousAttrs, '');
    }

    sanitizeUrl(url) {
        try {
            // 只允许http/https/mailto协议
            const parsed = new URL(url, window.location.origin);
            if (['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
                return parsed.toString();
            }
        } catch (e) {
            // URL解析失败
        }
        return '#';
    }

    isValidLanguage(language) {
        // 常见的代码语言白名单
        const validLanguages = [
            'javascript', 'js', 'typescript', 'ts', 'python', 'py', 'java', 'cpp', 'c',
            'html', 'css', 'json', 'xml', 'yaml', 'yml', 'bash', 'shell', 'sql',
            'markdown', 'md', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin'
        ];
        return !language || validLanguages.includes(language.toLowerCase());
    }
}

// 在app.js中集成
const markdownRenderer = new MarkdownRenderer();

// 修改现有的任务详情生成逻辑
generateTaskDetailsModal(task) {
    const resultContent = task.result ? this.renderTaskResult(task.result) : '';
    const errorContent = task.error_message ? this.renderTaskError(task.error_message) : '';

    // 其余代码保持不变...
}

renderTaskResult(content) {
    const rendered = markdownRenderer.render(content);
    const isMarkdown = markdownRenderer.isMarkdownContent(content);

    return `
        <div class="row mb-3">
            <div class="col-sm-3"><strong>执行结果:</strong></div>
            <div class="col-sm-9">
                <div class="task-result-container ${isMarkdown ? 'markdown-content' : ''}">
                    ${isMarkdown ?
                        `<div class="markdown-body">${rendered}</div>` :
                        `<pre>${rendered}</pre>`
                    }
                </div>
            </div>
        </div>
    `;
}
```

### CSS样式扩展

```css
/* Markdown内容容器 */
.task-result-container.markdown-content {
    padding: 0;
}

.task-result-container .markdown-body {
    padding: 1rem;
    font-size: 0.875rem;
    line-height: 1.6;
    color: #212529;
    word-wrap: break-word;
}

/* Markdown标题样式 */
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    font-weight: 600;
    line-height: 1.25;
    color: inherit;
}

.markdown-body h1 { font-size: 1.5rem; }
.markdown-body h2 { font-size: 1.375rem; }
.markdown-body h3 { font-size: 1.25rem; }
.markdown-body h4 { font-size: 1.125rem; }
.markdown-body h5 { font-size: 1rem; }
.markdown-body h6 { font-size: 0.875rem; }

.markdown-body h1:first-child,
.markdown-body h2:first-child,
.markdown-body h3:first-child {
    margin-top: 0;
}

/* 段落样式 */
.markdown-body p {
    margin-top: 0;
    margin-bottom: 1rem;
}

/* 列表样式 */
.markdown-body ul,
.markdown-body ol {
    margin-top: 0;
    margin-bottom: 1rem;
    padding-left: 2rem;
}

.markdown-body li {
    margin-bottom: 0.25rem;
}

.markdown-body li > p {
    margin-bottom: 0;
}

/* 引用块样式 */
.markdown-body blockquote {
    margin: 1rem 0;
    padding: 0.5rem 1rem;
    border-left: 4px solid #6c757d;
    background-color: #f8f9fa;
    color: #495057;
}

.markdown-body blockquote p:last-child {
    margin-bottom: 0;
}

/* 代码样式 */
.markdown-body code {
    padding: 0.2rem 0.4rem;
    margin: 0;
    font-size: 85%;
    background-color: rgba(27, 31, 35, 0.05);
    border-radius: 3px;
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body pre {
    padding: 1rem;
    margin: 1rem 0;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
    background-color: #f6f8fa;
    border-radius: 6px;
}

.markdown-body pre code {
    display: inline;
    max-width: auto;
    padding: 0;
    margin: 0;
    overflow: visible;
    line-height: inherit;
    word-wrap: normal;
    background-color: transparent;
    border: 0;
}

/* 表格样式 */
.markdown-body table {
    display: block;
    width: 100%;
    margin: 1rem 0;
    overflow: auto;
}

.markdown-body table th,
.markdown-body table td {
    padding: 6px 13px;
    border: 1px solid #dfe2e5;
}

.markdown-body table th {
    font-weight: 600;
    background-color: #f6f8fa;
}

.markdown-body table tr {
    background-color: #fff;
    border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
    background-color: #f6f8fa;
}

/* 分隔线样式 */
.markdown-body hr {
    height: 0.25em;
    padding: 0;
    margin: 2rem 0;
    background-color: #e1e4e8;
    border: 0;
}

/* 链接样式 */
.markdown-body a {
    color: #0366d6;
    text-decoration: none;
}

.markdown-body a:hover {
    text-decoration: underline;
}

/* 图片样式 - 在执行结果中可能不太常见，但提供支持 */
.markdown-body img {
    max-width: 100%;
    height: auto;
    margin: 0.5rem 0;
    border-radius: 4px;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .markdown-body {
        padding: 0.75rem;
        font-size: 0.8rem;
    }

    .markdown-body ul,
    .markdown-body ol {
        padding-left: 1.5rem;
    }

    .markdown-body pre {
        padding: 0.75rem;
    }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
    .task-result-container .markdown-body {
        color: #e2e8f0;
    }

    .markdown-body blockquote {
        background-color: #2d3748;
        border-left-color: #4a5568;
        color: #cbd5e0;
    }

    .markdown-body code {
        background-color: rgba(255, 255, 255, 0.1);
    }

    .markdown-body pre {
        background-color: #2d3748;
    }

    .markdown-body table th {
        background-color: #2d3748;
    }

    .markdown-body table tr {
        background-color: transparent;
        border-top-color: #4a5568;
    }

    .markdown-body table tr:nth-child(2n) {
        background-color: #2d3748;
    }

    .markdown-body hr {
        background-color: #4a5568;
    }

    .markdown-body a {
        color: #63b3ed;
    }
}

/* 滚动容器与Markdown内容的协调 */
.task-result-container .markdown-body:last-child {
    margin-bottom: 0;
}

/* 确保代码块在滚动容器内正确显示 */
.task-result-container .markdown-body pre {
    max-width: 100%;
    overflow-x: auto;
}
```

## Migration Plan

### 阶段1：核心功能实现（1-2天）
1. 创建 `MarkdownRenderer` 类
2. 实现内容检测和基础渲染功能
3. 添加基本的安全防护

### 阶段2：样式和优化（1天）
1. 创建完整的Markdown样式表
2. 实现深色模式支持
3. 优化响应式设计

### 阶段3：集成和测试（1天）
1. 修改 `app.js` 中的任务详情生成逻辑
2. 测试各种Markdown内容格式
3. 验证安全性和性能

### 阶段4：错误处理和降级（0.5天）
1. 完善错误处理机制
2. 确保纯文本内容的正常显示
3. 添加调试日志

### 回滚计划
如需回滚：
- 保留原始渲染逻辑作为备份
- 通过配置开关控制功能启用
- 维护独立的CSS文件，便于快速移除

## Open Questions
- 是否需要添加代码语法高亮功能（如Prism.js）？
- 是否需要支持表格内容的横向滚动？
- 是否为超长内容提供"展开/折叠"功能？
- 是否需要添加复制Markdown内容的功能？
- 错误信息是否也需要支持Markdown渲染？

## Accessibility Considerations
- 确保Markdown内容支持屏幕阅读器
- 维持足够的颜色对比度
- 支持键盘导航
- 为链接添加适当的 `aria-label`
- 确保代码块的可访问性
- 提供跳过长内容块的快捷方式