// 智能滚动系统
class SmartScroller {
    constructor(container) {
        this.container = container;
        this.isAutoScrollEnabled = true;
        this.userScrolling = false;
        this.scrollThreshold = 50; // 距离底部的阈值
        this.scrollTimeout = null;
        this.newMessageCount = 0;
        this.init();
    }

    init() {
        try {
            // 验证容器是否存在
            if (!this.container) {
                throw new Error('SmartScroller: 容器元素不存在');
            }

            // 监听滚动事件
            this.container.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });

            // 监听鼠标进入/离开
            this.container.addEventListener('mouseenter', this.handleMouseEnter.bind(this), { passive: true });
            this.container.addEventListener('mouseleave', this.handleMouseLeave.bind(this), { passive: true });

            // 监听滚轮事件
            this.container.addEventListener('wheel', this.handleWheel.bind(this), { passive: true });

            // 初始化滚动到底部按钮
            this.initScrollButton();
        } catch (error) {
            console.error('SmartScroller初始化失败:', error);
            // 降级处理：即使初始化失败，也提供基础滚动功能
            this.fallbackMode = true;
        }
    }

    handleScroll() {
        const isAtBottom = this.isNearBottom();
        const wasAtBottom = this.isAutoScrollEnabled;

        // 更新自动滚动状态
        this.isAutoScrollEnabled = isAtBottom;

        // 如果用户手动滚动离开底部，显示滚动到底部按钮
        if (!isAtBottom) {
            this.showScrollButton();
        } else {
            this.hideScrollButton();
            this.newMessageCount = 0;
            this.updateNewMessageIndicator();
        }

        // 检测用户是否在主动滚动
        clearTimeout(this.scrollTimeout);
        this.userScrolling = true;
        this.scrollTimeout = setTimeout(() => {
            this.userScrolling = false;
        }, 150);
    }

    handleMouseEnter() {
        // 鼠标进入时可能是在查看历史消息
        // 不立即禁用自动滚动，等用户实际滚动再说
    }

    handleMouseLeave() {
        // 鼠标离开时，如果在底部附近，恢复自动滚动
        if (this.isNearBottom()) {
            this.isAutoScrollEnabled = true;
        }
    }

    handleWheel(event) {
        // 向上滚动表示用户可能想查看历史消息
        if (event.deltaY < 0) {
            this.userScrolling = true;
            setTimeout(() => {
                if (this.isNearBottom()) {
                    this.userScrolling = false;
                }
            }, 1000);
        }
        // 向下滚动到最底时重新启用自动滚动
        else if (event.deltaY > 0 && this.isNearBottom()) {
            this.isAutoScrollEnabled = true;
            this.userScrolling = false;
        }
    }

    isNearBottom() {
        try {
            if (!this.container || this.fallbackMode) return true;

            const { scrollTop, scrollHeight, clientHeight } = this.container;

            // 验证数值有效性
            if (isNaN(scrollTop) || isNaN(scrollHeight) || isNaN(clientHeight)) {
                console.warn('SmartScroller: 无效的滚动数值');
                return true;
            }

            return scrollHeight - scrollTop - clientHeight <= this.scrollThreshold;
        } catch (error) {
            console.error('SmartScroller.isNearBottom 错误:', error);
            return true; // 出错时默认允许滚动
        }
    }

    smoothScrollToBottom() {
        try {
            if (!this.container || this.fallbackMode) return;

            this.container.scrollTo({
                top: this.container.scrollHeight,
                behavior: 'smooth'
            });
        } catch (error) {
            console.warn('SmartScroller.smoothScrollToBottom 错误，使用即时滚动:', error);
            this.instantScrollToBottom();
        }
    }

    instantScrollToBottom() {
        try {
            if (!this.container || this.fallbackMode) return;

            this.container.scrollTop = this.container.scrollHeight;
        } catch (error) {
            console.error('SmartScroller.instantScrollToBottom 错误:', error);
        }
    }

    autoScrollIfEnabled(force = false) {
        if (this.isAutoScrollEnabled || force) {
            // 使用requestAnimationFrame确保DOM更新后再滚动
            requestAnimationFrame(() => {
                this.smoothScrollToBottom();
            });
        } else {
            // 如果不在底部，增加新消息计数
            this.newMessageCount++;
            this.updateNewMessageIndicator();
            this.showScrollButton();
        }
    }

    initScrollButton() {
        this.scrollButton = document.getElementById('scroll-to-bottom');
        if (this.scrollButton) {
            this.scrollButton.addEventListener('click', () => {
                this.isAutoScrollEnabled = true;
                this.newMessageCount = 0;
                this.updateNewMessageIndicator();
                this.smoothScrollToBottom();
                this.hideScrollButton();
            });
        }
    }

    showScrollButton() {
        if (this.scrollButton) {
            this.scrollButton.classList.add('visible');
        }
    }

    hideScrollButton() {
        if (this.scrollButton) {
            this.scrollButton.classList.remove('visible');
        }
    }

    updateNewMessageIndicator() {
        if (this.scrollButton && this.newMessageCount > 0) {
            const indicator = this.scrollButton.querySelector('.new-message-indicator');
            if (indicator) {
                indicator.textContent = this.newMessageCount > 99 ? '99+' : `${this.newMessageCount}条新消息`;
                indicator.style.display = this.newMessageCount > 0 ? 'block' : 'none';
            }
        }
    }

    // 处理消息添加时的智能滚动
    onMessageAdded() {
        // 延迟检查，确保DOM已经更新
        setTimeout(() => {
            this.autoScrollIfEnabled();
        }, 50);
    }

    // 处理批量消息添加
    onBatchMessageAdded() {
        // 批量添加后，如果用户之前在底部，自动滚动到新的底部
        setTimeout(() => {
            if (this.isNearBottom()) {
                this.isAutoScrollEnabled = true;
                this.instantScrollToBottom();
            } else {
                this.newMessageCount++;
                this.updateNewMessageIndicator();
                this.showScrollButton();
            }
        }, 100);
    }

    // 重置滚动状态
    reset() {
        this.isAutoScrollEnabled = true;
        this.userScrolling = false;
        this.newMessageCount = 0;
        this.updateNewMessageIndicator();
        this.hideScrollButton();
    }

    // 销毁事件监听器
    destroy() {
        try {
            if (this.scrollTimeout) {
                clearTimeout(this.scrollTimeout);
            }

            if (!this.container) return;

            // 移除事件监听器
            this.container.removeEventListener('scroll', this.handleScroll);
            this.container.removeEventListener('mouseenter', this.handleMouseEnter);
            this.container.removeEventListener('mouseleave', this.handleMouseLeave);
            this.container.removeEventListener('wheel', this.handleWheel);

            if (this.scrollButton) {
                this.scrollButton.removeEventListener('click', this.scrollToBottom);
            }

            // 清理引用
            this.container = null;
            this.scrollButton = null;
        } catch (error) {
            console.error('SmartScroller.destroy 错误:', error);
        }
    }
}

// 导出类以供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SmartScroller;
}