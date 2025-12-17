// Phone Agent Web Interface - Main Application JavaScript

class PhoneAgentWeb {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.taskStartTime = null;
        this.updateTimer = null;
        this.stepCount = 0;

        // 消息队列管理
        this.messageQueue = [];
        this.isProcessingQueue = false;
        this.batchProcessTimer = null;

        // 初始化Markdown渲染器
        this.markdownRenderer = new MarkdownRenderer();

        this.init();
    }

    init() {
        // Initialize Socket.IO connection with robust configuration
        this.socket = io({
            transports: ['polling', 'websocket'],
            upgrade: true,
            rememberUpgrade: true,
            timeout: 20000,
            forceNew: false,
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            maxReconnectionAttempts: 5
        });
        this.setupSocketListeners();

        // Setup UI event listeners
        this.setupUIListeners();

        // Initialize smart scroller
        this.initSmartScroller();

        // Initialize floating screenshot
        this.initFloatingScreenshot();

        // Initialize session
        this.createSession();

        // Load initial data
        this.loadDevices();
        this.loadApps();
        this.loadTaskHistory();
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            // 清除之前的连接错误提示
            this.clearConnectionErrors();
        });

        this.socket.on('disconnect', (reason) => {
            console.log('Disconnected from server, reason:', reason);
            this.isConnected = false;
            this.updateConnectionStatus(false);

            // 根据断开原因提供不同的处理
            if (reason === 'io server disconnect') {
                // 服务器主动断开，需要重新连接
                this.socket.connect();
            } else if (reason === 'ping timeout') {
                console.log('连接超时，尝试重新连接...');
            }
        });

        // 添加连接错误处理
        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            this.isConnected = false;
            this.updateConnectionStatus(false);

            // 根据错误类型提供用户提示
            if (error.message && error.message.includes('Invalid frame header')) {
                console.warn('WebSocket frame error, falling back to polling');
                // 强制使用长轮询
                this.socket.io.opts.transports = ['polling'];
            } else {
                this.showToast('连接服务器失败，请检查网络连接', 'warning');
            }
        });

        // 添加重连尝试事件
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`重连尝试 ${attemptNumber}`);
            this.showToast(`正在重连服务器... (${attemptNumber}/5)`, 'info');
        });

        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`重连成功，尝试次数: ${attemptNumber}`);
            this.showToast('重新连接到服务器', 'success');
        });

        this.socket.on('reconnect_failed', () => {
            console.error('重连失败');
            this.showToast('无法连接到服务器，请刷新页面重试', 'error');
        });

        this.socket.on('joined_session', (data) => {
            console.log('Joined session:', data.session_id);
        });

        this.socket.on('task_started', (data) => {
            this.onTaskStarted(data);
        });

        this.socket.on('step_update', (data) => {
            this.onStepUpdate(data);
        });

        this.socket.on('task_completed', (data) => {
            this.onTaskCompleted(data);
        });

        this.socket.on('task_error', (data) => {
            this.onTaskError(data);
        });

        this.socket.on('task_stopped', (data) => {
            this.onTaskStopped(data);
        });
    }

    setupUIListeners() {
        const sendBtn = document.getElementById('send-btn');
        const stopBtn = document.getElementById('stop-btn');
        const taskInput = document.getElementById('task-input');
        const screenshotToggleBtn = document.getElementById('screenshot-toggle-btn');

        // Send button
        sendBtn.addEventListener('click', () => {
            this.sendTask();
        });

        // Stop button
        stopBtn.addEventListener('click', () => {
            this.stopTask();
        });

        // Enter key in input
        taskInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTask();
            }
        });

        // Screenshot toggle button
        if (screenshotToggleBtn) {
            screenshotToggleBtn.addEventListener('click', () => {
                if (this.floatingScreenshot) {
                    this.floatingScreenshot.toggleVisibility();
                }
            });
        }

        // Periodic updates
        this.updateTimer = setInterval(() => {
            this.updateExecutionTime();
        }, 1000);

        // Global keyboard shortcut for screenshot toggle (Ctrl+S)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's' && !e.shiftKey) {
                e.preventDefault();
                if (this.floatingScreenshot) {
                    this.floatingScreenshot.toggleVisibility();
                }
            }
        });
    }

    initSmartScroller() {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            try {
                // 如果已存在,先清理旧实例
                if (this.smartScroller) {
                    this.smartScroller.destroy();
                }
                this.smartScroller = new SmartScroller(chatContainer);
                console.log('Smart scroller initialized');
            } catch (error) {
                console.error('Failed to initialize smart scroller:', error);
                this.smartScroller = null;
            }
        } else {
            console.warn('Chat container not found, smart scroller disabled');
        }
    }

    async createSession() {
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: 'web_user_' + Date.now()
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                document.getElementById('session-id').textContent = `会话ID: ${this.sessionId.substring(0, 8)}...`;

                // Join session room
                this.socket.emit('join_session', { session_id: this.sessionId });

                // Enable input
                document.getElementById('task-input').disabled = false;
                document.getElementById('send-btn').disabled = false;

                this.showToast('会话已创建', 'success');
            } else {
                throw new Error('Failed to create session');
            }
        } catch (error) {
            console.error('Error creating session:', error);
            this.showToast('创建会话失败: ' + error.message, 'error');
        }
    }

    async sendTask() {
        const taskInput = document.getElementById('task-input');
        const task = taskInput.value.trim();

        if (!task || !this.isConnected) {
            return;
        }

        // Get current configuration
        const config = await this.getCurrentConfig();

        // Add user message to chat
        this.addMessage('user', task);

        // Clear input and disable controls
        taskInput.value = '';
        this.setInputEnabled(false);

        // Reset task tracking
        this.stepCount = 0;
        this.taskStartTime = new Date();
        this.updateTaskStatus('running', task);

        // Reset smart scroller for new task
        if (this.smartScroller) {
            this.smartScroller.reset();
        }

        // Send task to server
        this.socket.emit('send_task', {
            session_id: this.sessionId,
            task: task,
            config: config
        });
    }

    stopTask() {
        if (this.sessionId) {
            this.socket.emit('stop_task', {
                session_id: this.sessionId
            });
        }
    }

    onTaskStarted(data) {
        this.addMessage('system', `开始执行任务: ${data.task}`);
        this.updateTaskStatus('running', data.task);
        this.showToast('任务开始执行', 'info');
    }

    onStepUpdate(data) {
        this.stepCount++;
        const step = data.step;

        // Create step message
        let stepMessage = '';

        if (step.thinking) {
            stepMessage += `<div class="step-thinking">
                <i class="fas fa-brain me-1"></i>
                <strong>思考:</strong> ${this.escapeHtml(step.thinking)}
            </div>`;
        }

        if (step.action) {
            stepMessage += `<div class="step-action">
                <i class="fas fa-play-circle me-1"></i>
                <strong>动作:</strong> <code>${JSON.stringify(step.action)}</code>
            </div>`;
        }

        if (step.result) {
            stepMessage += `<div class="step-result">
                <i class="fas fa-check-circle me-1"></i>
                <strong>结果:</strong> ${this.escapeHtml(String(step.result))}
            </div>`;
        }

        // Add step update to chat
        this.addStepUpdate(`步骤 ${this.stepCount}`, stepMessage);

        // Update step count
        document.getElementById('step-count').textContent = this.stepCount;

        // Update screenshot if available
        if (step.screenshot) {
            this.updateScreenshot(step.screenshot);
        }
    }

    onTaskCompleted(data) {
        this.addMessage('assistant', data.result);
        this.updateTaskStatus('completed');
        this.setInputEnabled(true);
        this.showToast('任务执行完成', 'success');
    }

    onTaskError(data) {
        this.addMessage('system', `任务执行出错: ${data.error}`);
        this.updateTaskStatus('error');
        this.setInputEnabled(true);
        this.showToast('任务执行失败: ' + data.error, 'error');
    }

    onTaskStopped(data) {
        this.addMessage('system', data.message);
        this.updateTaskStatus('stopped');
        this.setInputEnabled(true);
        this.showToast('任务已停止', 'warning');
    }

    addMessage(role, content, timestamp = null) {
        const chatContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const time = timestamp || new Date().toLocaleTimeString();
        const roleIcon = this.getRoleIcon(role);
        const roleClass = role === 'user' ? '最帅的Dawin' : role === 'assistant' ? '助手' : 'Terminal Agent';

        // 检测是否为长消息
        const formattedContent = this.formatMessage(content);
        const isLongMessage = this.isLongMessage(content);
        const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        if (isLongMessage) {
            // 长消息:创建可折叠版本
            const previewContent = this.getPreviewContent(content);
            messageDiv.innerHTML = `
                <div class="message-content long-message" id="${messageId}">
                    <div class="message-header mb-1">
                        <small><i class="${roleIcon} me-1"></i>${roleClass}</small>
                    </div>
                    <div class="message-text preview">${this.formatMessage(previewContent)}</div>
                    <div class="message-text full" style="display: none;">${formattedContent}</div>
                    <button class="btn btn-sm btn-link expand-btn" onclick="phoneAgentWeb.toggleMessageExpansion('${messageId}')">
                        <i class="fas fa-chevron-down"></i> 展开全部
                    </button>
                    <div class="message-time">${time}</div>
                </div>
            `;
        } else {
            // 普通消息
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-header mb-1">
                        <small><i class="${roleIcon} me-1"></i>${roleClass}</small>
                    </div>
                    <div class="message-text">${formattedContent}</div>
                    <div class="message-time">${time}</div>
                </div>
            `;
        }

        // Remove welcome message if exists
        const welcomeMsg = chatContainer.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        chatContainer.appendChild(messageDiv);

        // 使用批量更新机制
        this.scheduleScrollUpdate();
    }

    // 检测是否为长消息
    isLongMessage(content) {
        // 判断标准:
        // 1. 文本长度超过1000个字符
        // 2. 或包含超过15行
        const charThreshold = 1000;
        const lineThreshold = 15;

        const charCount = content.length;
        const lineCount = content.split('\n').length;

        return charCount > charThreshold || lineCount > lineThreshold;
    }

    // 获取预览内容
    getPreviewContent(content) {
        const previewLines = 10;
        const previewChars = 500;

        const lines = content.split('\n');

        if (lines.length <= previewLines && content.length <= previewChars) {
            return content;
        }

        // 截取前N行或前N个字符
        let preview = lines.slice(0, previewLines).join('\n');
        if (preview.length > previewChars) {
            preview = preview.substring(0, previewChars);
        }

        return preview + '\n\n...';
    }

    // 切换消息展开/收起状态
    toggleMessageExpansion(messageId) {
        const messageContent = document.getElementById(messageId);
        if (!messageContent) return;

        const previewDiv = messageContent.querySelector('.message-text.preview');
        const fullDiv = messageContent.querySelector('.message-text.full');
        const expandBtn = messageContent.querySelector('.expand-btn');

        if (!previewDiv || !fullDiv || !expandBtn) return;

        const isExpanded = fullDiv.style.display !== 'none';

        if (isExpanded) {
            // 收起
            fullDiv.style.display = 'none';
            previewDiv.style.display = 'block';
            expandBtn.innerHTML = '<i class="fas fa-chevron-down"></i> 展开全部';
        } else {
            // 展开
            previewDiv.style.display = 'none';
            fullDiv.style.display = 'block';
            expandBtn.innerHTML = '<i class="fas fa-chevron-up"></i> 收起';

            // 展开后滚动到消息位置
            if (this.smartScroller) {
                setTimeout(() => {
                    messageContent.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        }
    }

    addStepUpdate(title, content) {
        const chatContainer = document.getElementById('chat-messages');
        const stepDiv = document.createElement('div');
        stepDiv.className = 'step-update';

        stepDiv.innerHTML = `
            <div class="step-header">
                <i class="fas fa-cogs me-1"></i>
                <strong>${title}</strong>
                <small class="text-muted ms-2">${new Date().toLocaleTimeString()}</small>
            </div>
            ${content}
        `;

        chatContainer.appendChild(stepDiv);

        // 使用批量更新机制
        this.scheduleScrollUpdate();
    }

    // 调度滚动更新 - 批量处理多个消息
    scheduleScrollUpdate() {
        // 清除之前的定时器
        if (this.batchProcessTimer) {
            clearTimeout(this.batchProcessTimer);
        }

        // 设置新的定时器,批量处理
        this.batchProcessTimer = setTimeout(() => {
            this.processBatchScroll();
        }, 50); // 50ms内的消息会被批量处理
    }

    // 批量处理滚动
    processBatchScroll() {
        if (this.smartScroller) {
            // 使用requestAnimationFrame确保在下一帧渲染
            requestAnimationFrame(() => {
                this.smartScroller.onBatchMessageAdded();
            });
        } else {
            // 降级到简单滚动
            const chatContainer = document.getElementById('chat-messages');
            if (chatContainer) {
                requestAnimationFrame(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
            }
        }
    }

    updateTaskStatus(status, task = null) {
        const statusElement = document.getElementById('task-status');
        const taskElement = document.getElementById('current-task');
        const progressBar = document.getElementById('task-progress');

        // Update status badge
        statusElement.className = 'badge status-badge ' + status;
        statusElement.textContent = this.getStatusText(status);

        // Update current task
        if (task) {
            taskElement.textContent = task.length > 30 ? task.substring(0, 30) + '...' : task;
            taskElement.title = task;
        }

        // Update progress bar
        if (status === 'running') {
            progressBar.style.width = '50%';
            progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        } else if (status === 'completed') {
            progressBar.style.width = '100%';
            progressBar.className = 'progress-bar bg-success';
        } else if (status === 'error') {
            progressBar.style.width = '100%';
            progressBar.className = 'progress-bar bg-danger';
        } else {
            progressBar.style.width = '0%';
            progressBar.className = 'progress-bar';
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');

        if (connected) {
            statusElement.className = 'badge bg-success';
            statusElement.innerHTML = '<i class="fas fa-circle me-1"></i>已连接';
        } else {
            statusElement.className = 'badge bg-danger';
            statusElement.innerHTML = '<i class="fas fa-circle me-1"></i>已断开';
        }
    }

    clearConnectionErrors() {
        // 清除控制台中的连接相关警告
        console.clear();
        console.log('连接错误已清除，系统正常运行');
    }

    updateExecutionTime() {
        if (this.taskStartTime && this.isConnected) {
            const elapsed = Math.floor((new Date() - this.taskStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            const timeString = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
            document.getElementById('execution-time').textContent = timeString;
        }
    }

    updateScreenshot(screenshotData) {
        // Update only the floating container (fixed screenshot panel removed)
        const floatingContainer = document.getElementById('floating-screenshot-container');

        if (screenshotData) {
            let imageSrc;

            // Check if it's a base64 data URL or a file path
            if (screenshotData.startsWith('data:image/')) {
                imageSrc = screenshotData;
            } else if (screenshotData.length > 100 && screenshotData.includes('/')) {
                // Likely a base64 string without data URL prefix
                imageSrc = `data:image/png;base64,${screenshotData}`;
            } else {
                // Treat as file path
                imageSrc = `/screenshots/${screenshotData}`;
            }

            const screenshotHtml = `
                <div class="screenshot-preview">
                    <img src="${imageSrc}"
                         alt="操作截图"
                         class="img-fluid"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
                         onclick="this.requestFullscreen()">
                    <div class="zoom-hint">
                        <i class="fas fa-search-plus"></i> 点击全屏
                    </div>
                    <div class="text-center text-muted" style="display: none;">
                        <i class="fas fa-exclamation-triangle"></i> 截图加载失败
                    </div>
                </div>
            `;

            // Update floating window only
            if (floatingContainer) {
                floatingContainer.innerHTML = screenshotHtml;
            }
        } else {
            // Clear floating window
            if (floatingContainer) {
                floatingContainer.innerHTML = `
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-image fa-2x mb-2"></i>
                        <p class="small mb-0">等待截图...</p>
                    </div>
                `;
            }
        }
    }

    setInputEnabled(enabled) {
        document.getElementById('task-input').disabled = !enabled;
        document.getElementById('send-btn').disabled = !enabled;
        document.getElementById('stop-btn').disabled = enabled;

        if (enabled) {
            document.getElementById('task-input').focus();
        }
    }

    async loadDevices() {
        try {
            const response = await fetch('/api/devices');
            if (response.ok) {
                const devices = await response.json();
                this.updateDeviceList(devices);
            }
        } catch (error) {
            console.error('Error loading devices:', error);
            this.updateDeviceList([]);
        }
    }

    async loadApps() {
        try {
            const response = await fetch('/api/apps');
            if (response.ok) {
                const apps = await response.json();
                this.updateAppsList(apps);
            }
        } catch (error) {
            console.error('Error loading apps:', error);
            this.updateAppsList([]);
        }
    }

    async loadTaskHistory() {
        try {
            // 显示加载状态
            this.showTaskHistoryLoading(true);

            console.log('🔄 开始加载任务历史...');
            const response = await fetch('/api/tasks');

            console.log('📡 API响应状态:', response.status, response.statusText);

            if (response.ok) {
                const data = await response.json();

                // 数据流追踪 - 步骤1: 记录API返回的原始数据
                console.group('🔍 [数据流追踪] loadTaskHistory - API响应数据');
                console.log('完整响应数据:', data);
                console.log('任务数组:', data.data?.tasks);
                console.log('任务数量:', data.data?.tasks?.length || 0);

                if (data.data?.tasks && data.data.tasks.length > 0) {
                    console.log('第一个任务的时间戳详情:');
                    const firstTask = data.data.tasks[0];
                    console.log('- start_time:', firstTask.start_time);
                    console.log('- start_time 类型:', typeof firstTask.start_time);
                    console.log('- created_at:', firstTask.created_at);
                    console.log('- created_at 类型:', typeof firstTask.created_at);
                    console.log('- updated_at:', firstTask.updated_at);
                    console.log('- updated_at 类型:', typeof firstTask.updated_at);

                    // 分析所有任务的时间戳格式
                    console.log('\n所有任务的时间戳分析:');
                    data.data.tasks.forEach((task, index) => {
                        console.log(`任务${index + 1}:`, {
                            task_id: task.task_id,
                            start_time: task.start_time,
                            start_time_type: typeof task.start_time,
                            created_at: task.created_at,
                            created_at_type: typeof task.created_at
                        });
                    });
                }
                console.groupEnd();

                // 适配新的API响应格式
                this.updateTaskHistoryList(data.data?.tasks || []);
            } else {
                console.error('❌ API请求失败，状态码:', response.status);
                let errorMessage = `请求失败 (${response.status} ${response.statusText})`;

                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (parseError) {
                    console.warn('无法解析错误响应:', parseError);
                }

                // 使用专门的错误显示方法
                this.showTaskHistoryError(errorMessage);
                this.showToast(errorMessage, 'error');
            }
        } catch (error) {
            console.error('❌ 网络请求异常:', error);
            console.error('错误详情:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });

            // 提供更具体的错误信息
            let userMessage = '网络连接失败，请检查:';
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                userMessage = '无法连接到服务器，请检查服务是否运行在正确的端口';
            } else if (error.name === 'AbortError') {
                userMessage = '请求超时，请重试';
            } else {
                userMessage = `加载失败: ${error.message}`;
            }

            // 使用专门的错误显示方法
            this.showTaskHistoryError(userMessage);
            this.showToast(userMessage, 'error');
        } finally {
            this.showTaskHistoryLoading(false);
        }
    }

    async stopHistoryTask(taskId) {
        // 参数验证
        if (!taskId || taskId === 'undefined' || taskId === 'null' || typeof taskId !== 'string') {
            console.error('无效的任务ID:', taskId);
            this.showToast('无效的任务ID，请刷新页面重试', 'error');
            return;
        }

        console.log('停止任务:', taskId);

        try {
            const response = await fetch(`/api/tasks/${taskId}/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            console.log('停止任务响应状态:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('停止任务成功:', data);
                this.showToast(data.message, 'success');
                // 刷新任务历史
                await this.loadTaskHistory();
            } else {
                const errorData = await response.json();
                console.error('停止任务失败:', errorData);
                this.showToast(errorData.error || '停止任务失败', 'error');
            }
        } catch (error) {
            console.error('停止任务异常:', error);
            this.showToast(`停止任务失败: ${error.message}`, 'error');
        }
    }

    async viewTaskDetails(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`);
            if (response.ok) {
                const data = await response.json();
                // 适配新的API响应格式，取出实际的任务数据
                const task = data.data?.task;
                if (task) {
                    this.showTaskDetails(task);
                } else {
                    this.showToast('任务详情数据格式错误', 'error');
                }
            } else {
                const errorData = await response.json();
                this.showToast(errorData.error || '获取任务详情失败', 'error');
            }
        } catch (error) {
            console.error('Error viewing task details:', error);
            this.showToast('获取任务详情失败', 'error');
        }
    }

    async viewScript(scriptId) {
        try {
            this.showToast('正在加载脚本详情...', 'info');
            const response = await fetch(`/api/scripts/${scriptId}`);

            if (response.ok) {
                const data = await response.json();
                const script = data.data?.script || data.data;

                if (script) {
                    this.showScriptDetails(script);
                } else {
                    this.showToast('脚本详情数据格式错误', 'error');
                }
            } else {
                const errorData = await response.json();
                this.showToast(errorData.error || '获取脚本详情失败', 'error');
            }
        } catch (error) {
            console.error('Error viewing script details:', error);
            this.showToast('获取脚本详情失败', 'error');
        }
    }

    showScriptDetails(script) {
        // 创建脚本详情模态框
        const modalHtml = `
            <div class="modal fade" id="scriptDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-code me-2"></i>脚本详情
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6><i class="fas fa-info-circle me-2"></i>基本信息</h6>
                                    <table class="table table-sm">
                                        <tr><td><strong>任务名称:</strong></td><td>${script.task_name || 'N/A'}</td></tr>
                                        <tr><td><strong>描述:</strong></td><td>${script.description || 'N/A'}</td></tr>
                                        <tr><td><strong>总步骤数:</strong></td><td>${script.total_steps || 0}</td></tr>
                                        <tr><td><strong>成功率:</strong></td><td>${script.success_rate || 0}%</td></tr>
                                        <tr><td><strong>执行时间:</strong></td><td>${script.execution_time || 0}秒</td></tr>
                                        <tr><td><strong>设备ID:</strong></td><td>${script.device_id || 'N/A'}</td></tr>
                                        <tr><td><strong>模型:</strong></td><td>${script.model_name || 'N/A'}</td></tr>
                                        <tr><td><strong>创建时间:</strong></td><td>${script.created_at ? this.formatDateTime(script.created_at) : 'N/A'}</td></tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fas fa-tools me-2"></i>操作</h6>
                                    <div class="d-grid gap-2">
                                        <button class="btn btn-outline-primary btn-sm" onclick="phoneAgentWeb.exportScript('${script.id}', 'json')">
                                            <i class="fas fa-download me-1"></i>导出JSON
                                        </button>
                                        <button class="btn btn-outline-success btn-sm" onclick="phoneAgentWeb.exportScript('${script.id}', 'python')">
                                            <i class="fas fa-file-code me-1"></i>导出Python脚本
                                        </button>
                                        <button class="btn btn-outline-warning btn-sm" onclick="phoneAgentWeb.replayScript('${script.id}')">
                                            <i class="fas fa-play me-1"></i>重放脚本
                                        </button>
                                        <button class="btn btn-outline-danger btn-sm" onclick="phoneAgentWeb.deleteScript('${script.id}')">
                                            <i class="fas fa-trash me-1"></i>删除脚本
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <hr>

                            <h6><i class="fas fa-list-ol me-2"></i>执行步骤</h6>
                            <div class="script-steps" style="max-height: 400px; overflow-y: auto;">
                                ${this.renderScriptSteps(script.script_data?.steps || [])}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除现有模态框
        const existingModal = document.getElementById('scriptDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框到页面
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('scriptDetailsModal'));
        modal.show();

        // 模态框关闭后移除DOM
        document.getElementById('scriptDetailsModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    renderScriptSteps(steps) {
        if (!steps || steps.length === 0) {
            return '<p class="text-muted">暂无执行步骤</p>';
        }

        return steps.map((step, index) => {
            const successClass = step.success ? 'text-success' : 'text-danger';
            const successIcon = step.success ? 'fa-check-circle' : 'fa-times-circle';

            return `
                <div class="card mb-2">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>
                            <i class="fas ${successIcon} ${successClass} me-2"></i>
                            <strong>步骤 ${step.step_number}: ${step.action_type}</strong>
                        </span>
                        <small class="text-muted">${step.timestamp ? new Date(step.timestamp).toLocaleTimeString() : ''}</small>
                    </div>
                    <div class="card-body">
                        ${step.thinking ? `<p class="mb-2"><em>思考过程:</em> ${step.thinking}</p>` : ''}
                        ${step.action_data ? `<pre class="bg-light p-2 rounded"><code>${JSON.stringify(step.action_data, null, 2)}</code></pre>` : ''}
                        ${step.error_message ? `<div class="alert alert-danger alert-sm mt-2">${step.error_message}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    async exportScript(scriptId, format) {
        try {
            const response = await fetch(`/api/scripts/${scriptId}/export?format=${format}`);

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `script_${scriptId}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                this.showToast(`脚本已导出为${format.toUpperCase()}格式`, 'success');
            } else {
                const errorData = await response.json();
                this.showToast(errorData.error || '导出脚本失败', 'error');
            }
        } catch (error) {
            console.error('Error exporting script:', error);
            this.showToast('导出脚本失败', 'error');
        }
    }

    async replayScript(scriptId) {
        try {
            const device_id = prompt('请输入设备ID（留空使用默认设备）:');
            const delay = prompt('请输入操作延迟（秒，默认1.0）:') || '1.0';

            const response = await fetch(`/api/scripts/${scriptId}/replay`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: device_id || null,
                    delay: parseFloat(delay)
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.showToast(data.message || '脚本重放已启动', 'success');

                // 在实际实现中，这里可以启动一个实时进度显示
                console.log('Replay data:', data);
            } else {
                const errorData = await response.json();
                this.showToast(errorData.error || '启动脚本重放失败', 'error');
            }
        } catch (error) {
            console.error('Error replaying script:', error);
            this.showToast('启动脚本重放失败', 'error');
        }
    }

    async deleteScript(scriptId) {
        if (!confirm('确定要删除这个脚本吗？此操作无法撤销。')) {
            return;
        }

        try {
            const response = await fetch(`/api/scripts/${scriptId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                const data = await response.json();
                this.showToast(data.message || '脚本已删除', 'success');

                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('scriptDetailsModal'));
                if (modal) {
                    modal.hide();
                }

                // 刷新任务历史
                await this.loadTaskHistory();
            } else {
                const errorData = await response.json();
                this.showToast(errorData.error || '删除脚本失败', 'error');
            }
        } catch (error) {
            console.error('Error deleting script:', error);
            this.showToast('删除脚本失败', 'error');
        }
    }

    async getCurrentConfig() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const configs = await response.json();
                return configs.default || {};
            }
        } catch (error) {
            console.error('Error loading config:', error);
        }
        return {};
    }

    updateDeviceList(devices) {
        const container = document.getElementById('device-list');

        if (devices.length === 0) {
            container.innerHTML = `
                <div class="text-warning">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    未找到连接的设备
                </div>
            `;
            return;
        }

        const devicesHtml = devices.map(device => `
            <div class="device-item ${device.connection_type}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${device.device_id}</strong>
                        <div class="small text-muted">${device.model || 'Unknown'}</div>
                    </div>
                    <span class="badge bg-${device.connection_type === 'usb' ? 'success' : 'info'}">
                        ${device.connection_type.toUpperCase()}
                    </span>
                </div>
            </div>
        `).join('');

        container.innerHTML = devicesHtml;
    }

    updateAppsList(apps) {
        const container = document.getElementById('apps-list');

        if (apps.length === 0) {
            container.innerHTML = `
                <div class="text-muted">加载应用列表失败</div>
            `;
            return;
        }

        const appsHtml = apps.slice(0, 20).map(app =>
            `<span class="app-badge">${app}</span>`
        ).join('');

        container.innerHTML = appsHtml +
            (apps.length > 20 ? `<div class="text-muted small mt-2">...等 ${apps.length} 个应用</div>` : '');
    }

    getRoleIcon(role) {
        const icons = {
            'user': 'fas fa-user',
            'assistant': 'fas fa-robot',
            'system': 'fas fa-cog'
        };
        return icons[role] || 'fas fa-comment';
    }

    getStatusText(status) {
        const texts = {
            'idle': '空闲',
            'running': '执行中',
            'completed': '已完成',
            'error': '错误',
            'stopped': '已停止'
        };
        return texts[status] || status;
    }

    formatMessage(content) {
        // 首先检查是否包含 Markdown 语法
        const hasMarkdown = this.hasMarkdownSyntax(content);

        if (hasMarkdown) {
            // 使用 Marked.js 渲染 Markdown
            try {
                // 配置 Marked.js 选项
                marked.setOptions({
                    breaks: true,  // 支持换行
                    gfm: true,     // 支持GitHub风格的Markdown
                    sanitize: false, // 允许HTML（已通过escapeHtml处理）
                    smartLists: true,
                    smartypants: true
                });

                // 渲染 Markdown
                content = marked.parse(content);
            } catch (error) {
                console.error('Markdown 渲染错误:', error);
                // 如果渲染失败，回退到原始格式化方法
                return this.formatBasicMessage(content);
            }
        } else {
            // 如果没有 Markdown 语法，使用基础格式化
            return this.formatBasicMessage(content);
        }

        return content;
    }

    hasMarkdownSyntax(content) {
        // 检查常见的 Markdown 语法模式
        const markdownPatterns = [
            /^#{1,6}\s/m,           // 标题 # ## ###
            /^\*{1,2}(.+?)\*{1,2}/m, // 斜体 *text* 或粗体 **text**
            /^_{1,2}(.+?)_{1,2}/m,    // 斜体 _text_ 或粗体 __text__
            /^\[.+\]\(.+\)/m,        // 链接 [text](url)
            /^`{1,3}(.+?)`{1,3}/m,   // 代码 `code` 或 ```code```
            /^\d+\.\s/m,             // 有序列表 1. 2. 3.
            /^[-\*+]\s/m,            // 无序列表 - * +
            /^>\s/m,                 // 引用 >
            /^\|.*\|/m,              // 表格
            /^-{3,}/m,               // 分割线 ---
            /^\*{3,}/m               // 分割线 ***
        ];

        return markdownPatterns.some(pattern => pattern.test(content));
    }

    formatBasicMessage(content) {
        // 基础格式化（原有的逻辑）
        content = this.escapeHtml(content);

        // Convert URLs to links
        content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');

        // 处理代码块
        content = content.replace(/```(\w*)\n([\s\S]*?)\n```/g, (match, language, code) => {
            const lang = language || '';
            return `<div class="code-block mt-2 mb-2">
                <div class="code-header">
                    <small class="text-muted">${lang || 'code'}</small>
                </div>
                <pre><code class="language-${lang}">${this.escapeHtml(code.trim())}</code></pre>
            </div>`;
        });

        // 处理行内代码
        content = content.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

        // 处理粗体和斜体
        content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        content = content.replace(/\*(.+?)\*/g, '<em>$1</em>');
        content = content.replace(/__(.+?)__/g, '<strong>$1</strong>');
        content = content.replace(/_(.+?)_/g, '<em>$1</em>');

        // 处理换行
        content = content.replace(/\n/g, '<br>');

        return content;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 渲染任务结果内容（支持Markdown）
     */
    renderTaskResult(content) {
        if (!content) return '';

        const isMarkdown = this.markdownRenderer.isMarkdownContent(content);
        const renderedContent = this.markdownRenderer.render(content);

        return `
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
    }

    /**
     * 渲染任务错误信息（支持Markdown）
     */
    renderTaskError(content) {
        if (!content) return '';

        const isMarkdown = this.markdownRenderer.isMarkdownContent(content);
        const renderedContent = this.markdownRenderer.render(content);

        return `
            <div class="row mb-3">
                <div class="col-sm-3"><strong>错误信息:</strong></div>
                <div class="col-sm-9">
                    <div class="task-error-container ${isMarkdown ? 'markdown-content' : ''}">
                        ${isMarkdown ?
                            `<div class="markdown-body">${renderedContent}</div>` :
                            `<pre>${renderedContent}</pre>`
                        }
                    </div>
                </div>
            </div>
        `;
    }

    updateTaskHistoryList(tasks) {
        try {
            // 数据流追踪 - 步骤2: 记录接收到的任务数据
            console.group('🔍 [数据流追踪] updateTaskHistoryList - 任务数据处理');
            console.log('接收到的任务数组:', tasks);
            console.log('任务数量:', tasks.length);

            // ✅ 修复：在函数开始处统一声明container变量并添加DOM验证
            const container = document.getElementById('task-history-list');
            if (!container) {
                console.error('Task history container element not found');
                this.showToast('页面元素错误，请刷新页面', 'error');
                console.groupEnd();
                return;
            }

            if (!tasks || tasks.length === 0) {
                console.log('没有任务数据，显示空状态');
                console.groupEnd();

                container.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <div class="mb-3">
                            <i class="fas fa-history fa-3x opacity-50"></i>
                        </div>
                        <h5 class="mb-2">暂无任务历史</h5>
                        <p class="small">
                            还没有执行过任何任务。<br>
                            <a href="#" onclick="phoneAgentWeb.switchTab('control')" class="text-primary">
                                点击这里开始执行第一个任务
                            </a>
                        </p>
                    </div>
                `;
                return;
            }

        // 前端排序：按创建时间降序（作为后端排序的备用）
        console.log('\n开始前端排序...');
        const sortedTasks = tasks.sort((a, b) => {
            const timeA = new Date(a.start_time);
            const timeB = new Date(b.start_time);

            console.log(`排序比较 - 任务A(${a.task_id}):`, {
                start_time: a.start_time,
                parsed: timeA,
                isValid: !isNaN(timeA.getTime())
            });
            console.log(`排序比较 - 任务B(${b.task_id}):`, {
                start_time: b.start_time,
                parsed: timeB,
                isValid: !isNaN(timeB.getTime())
            });

            // 处理无效时间戳
            if (isNaN(timeA.getTime()) && isNaN(timeB.getTime())) return 0;
            if (isNaN(timeA.getTime())) return 1;
            if (isNaN(timeB.getTime())) return -1;

            return timeB - timeA; // 降序排列
        });

        console.log('排序完成，前3个任务:');
        sortedTasks.slice(0, 3).forEach((task, index) => {
            console.log(`${index + 1}. ${task.task_id}: ${task.start_time}`);
        });
        console.groupEnd();

        // 数据流追踪 - 步骤3: 追踪时间格式化
        console.group('🔍 [数据流追踪] 任务渲染 - 时间格式化处理');

        const tasksHtml = sortedTasks.map((task, index) => {
            const statusClass = task.status;
            const statusText = this.getStatusText(task.status);

            console.log(`\n任务${index + 1} (${task.task_id}) 时间处理:`, {
                start_time: task.start_time,
                start_time_type: typeof task.start_time
            });

            // 调用 getTimeAgo 前记录
            console.log('调用 getTimeAgo 前...');
            const timeAgo = this.getTimeAgo(task.start_time);
            console.log('getTimeAgo 返回:', timeAgo);

            // 调用 formatFullDateTime 前记录
            console.log('调用 formatFullDateTime 前...');
            const fullDateTime = this.formatFullDateTime(task.start_time);
            console.log('formatFullDateTime 返回:', fullDateTime);

            return `
                <div class="task-history-item ${statusClass}" data-task-id="${task.task_id}">
                    <div class="task-header">
                        <div class="task-title" title="${task.task_description || '无任务描述'}">
                            ${task.task_description ? task.task_description.substring(0, 30) + (task.task_description.length > 30 ? '...' : '') : '无任务描述'}
                        </div>
                        <span class="task-status bg-${statusClass === 'running' ? 'success' : statusClass === 'completed' ? 'primary' : statusClass === 'error' ? 'danger' : statusClass === 'stopped' ? 'warning' : 'secondary'} text-white">
                            ${statusText}
                        </span>
                    </div>
                    ${task.task_description && task.task_description.length > 30 ? `<div class="task-description">${task.task_description}</div>` : ''}
                    <div class="task-footer">
                        <div class="task-time" title="${this.formatFullDateTime(task.start_time)}">${timeAgo}</div>
                        <div class="task-actions">
                            ${task.status === 'running' ? `
                                <button class="btn-sm stop-btn" onclick="phoneAgentWeb.stopHistoryTask('${task.task_id}')" title="停止任务">
                                    <i class="fas fa-stop"></i> 停止
                                </button>
                            ` : ''}
                            ${task.status === 'completed' || task.status === 'error' || task.status === 'stopped' ? `
                                <button class="btn-sm report-btn" onclick="phoneAgentWeb.viewTaskReport('${task.task_id}')" title="查看执行报告">
                                    <i class="fas fa-chart-line"></i> 报告
                                </button>
                            ` : ''}
                            ${task.script_id ? `
                                <button class="btn-sm script-btn" onclick="phoneAgentWeb.viewScript('${task.script_id}')" title="查看脚本">
                                    <i class="fas fa-code"></i> 脚本
                                </button>
                            ` : ''}
                            <button class="btn-sm view-btn" onclick="phoneAgentWeb.viewTaskDetails('${task.task_id}')" title="查看详情">
                                <i class="fas fa-eye"></i> 查看
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        console.groupEnd(); // 结束数据流追踪 - 步骤3

        container.innerHTML = tasksHtml;

        } catch (error) {
            console.error('任务历史渲染错误:', error);

            // 根据错误类型提供不同的错误提示
            if (error instanceof ReferenceError) {
                this.showToast('页面脚本错误，请刷新页面重试', 'error');
            } else if (error instanceof TypeError) {
                this.showToast('数据格式错误，请联系技术支持', 'error');
            } else {
                this.showToast('渲染失败，请重试', 'warning');
            }

            // 确保调试信息完整
            console.groupEnd();
        }
    }

    showTaskDetails(task) {
        // 渲染任务结果和错误信息
        const resultContent = this.renderTaskResult(task.result);
        const errorContent = this.renderTaskError(task.error_message);

        // 创建模态框显示任务详情
        const modalHtml = `
            <div class="modal fade" id="taskDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">任务详情</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-sm-3"><strong>任务ID:</strong></div>
                                <div class="col-sm-9"><code>${task.task_id}</code></div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-sm-3"><strong>任务描述:</strong></div>
                                <div class="col-sm-9">${task.task_description || '无'}</div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-sm-3"><strong>状态:</strong></div>
                                <div class="col-sm-9">
                                    <span class="badge bg-${task.status === 'running' ? 'success' : task.status === 'completed' ? 'primary' : task.status === 'error' ? 'danger' : task.status === 'stopped' ? 'warning' : 'secondary'}">
                                        ${this.getStatusText(task.status)}
                                    </span>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-sm-3"><strong>会话ID:</strong></div>
                                <div class="col-sm-9"><code>${task.session_id}</code></div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-sm-3"><strong>开始时间:</strong></div>
                                <div class="col-sm-9">${this.formatDateTime(task.start_time)}</div>
                            </div>
                            ${task.end_time ? `
                                <div class="row mb-3">
                                    <div class="col-sm-3"><strong>结束时间:</strong></div>
                                    <div class="col-sm-9">${this.formatDateTime(task.end_time)}</div>
                                </div>
                            ` : ''}
                            ${resultContent}
                            ${errorContent}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            ${task.status === 'running' ? `
                                <button type="button" class="btn btn-danger" onclick="phoneAgentWeb.stopHistoryTask('${task.task_id}'); bootstrap.Modal.getInstance(document.getElementById('taskDetailsModal')).hide();">
                                    <i class="fas fa-stop"></i> 停止任务
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除现有的模态框
        const existingModal = document.getElementById('taskDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新的模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('taskDetailsModal'));
        modal.show();
    }

    // ========== 时间格式化相关函数 ==========

    /**
     * 统一的日期时间格式化函数
     * @param {string} timestamp - ISO格式的时间戳
     * @param {Object} options - 格式化选项
     * @returns {string} 格式化后的时间字符串
     */
    formatDateTime(timestamp, options = {}) {
        // 调试：记录原始时间戳
        console.log('[formatDateTime] 输入时间戳:', {
            value: timestamp,
            type: typeof timestamp,
            length: timestamp ? timestamp.length : 'N/A'
        });

        // 验证时间戳
        if (!timestamp) {
            console.warn('[formatDateTime] 时间戳为空:', timestamp);
            return options.defaultIfEmpty || '时间未知';
        }

        // 清理时间戳字符串
        let cleanTimestamp = timestamp;
        if (typeof timestamp === 'string') {
            cleanTimestamp = timestamp.trim();
            // 移除可能的换行符
            cleanTimestamp = cleanTimestamp.replace(/\n/g, '').replace(/\r/g, '');
            console.log('[formatDateTime] 清理后的时间戳:', cleanTimestamp);
        }

        let date = new Date(cleanTimestamp);
        let parseMethod = 'standard';

        // 检查日期是否有效，如果无效则尝试通用解析器
        if (isNaN(date.getTime())) {
            console.log('[formatDateTime] 标准解析失败，尝试通用解析器...');

            // 尝试使用通用解析器
            if (window.parseAnyTimestamp) {
                const fallbackDate = window.parseAnyTimestamp(timestamp);
                if (fallbackDate) {
                    date = fallbackDate;
                    parseMethod = 'universal';
                    console.log('[formatDateTime] 通用解析器成功:', fallbackDate);
                } else {
                    console.log('[formatDateTime] 通用解析器也失败了');
                }
            }

            // 如果仍然无效
            if (isNaN(date.getTime())) {
                console.error('[formatDateTime] 无效的时间戳:', {
                    original: timestamp,
                    cleaned: cleanTimestamp,
                    type: typeof timestamp,
                    parsed: date.toString()
                });

            // 增强的降级显示
            if (options.showOriginalOnError !== false) {
                // 显示原始时间戳，便于调试
                const originalStr = String(timestamp);
                const shortOriginal = originalStr.length > 50 ?
                    originalStr.substring(0, 47) + '...' : originalStr;

                return `[${shortOriginal}] 时间格式错误`;
            }

            return options.defaultIfInvalid || '时间格式错误';
        }
        }

        // 记录成功解析的信息
        console.log('[formatDateTime] 解析成功:', {
            method: parseMethod,
            original: timestamp,
            parsed: date
        });

        try {
            // 获取时区偏移
            const offset = -date.getTimezoneOffset();
            const offsetHours = Math.floor(Math.abs(offset) / 60);
            const offsetMinutes = Math.abs(offset) % 60;
            const offsetSign = offset >= 0 ? '+' : '-';
            const timezoneString = `UTC${offsetSign}${offsetHours.toString().padStart(2, '0')}:${offsetMinutes.toString().padStart(2, '0')}`;

            // 格式化日期时间
            const year = date.getFullYear();
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            const day = date.getDate().toString().padStart(2, '0');
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            const seconds = date.getSeconds().toString().padStart(2, '0');

            if (options.includeSeconds !== false) {
                return `${year}-${month}-${day} ${hours}:${minutes}:${seconds} (${timezoneString})`;
            } else {
                return `${year}-${month}-${day} ${hours}:${minutes} (${timezoneString})`;
            }
        } catch (error) {
            console.error('[formatDateTime] 格式化时出错:', error);
            return options.defaultIfError || '格式化失败';
        }
    }

    /**
     * 格式化相对时间
     * @param {string} timestamp - ISO格式的时间戳
     * @returns {string} 相对时间描述
     */
    formatRelativeTime(timestamp) {
        // 验证时间戳
        if (!timestamp) {
            console.warn('[formatRelativeTime] 时间戳为空:', timestamp);
            return '时间未知';
        }

        // 清理时间戳
        let cleanTimestamp = timestamp;
        if (typeof timestamp === 'string') {
            cleanTimestamp = timestamp.trim().replace(/\n/g, '').replace(/\r/g, '');
        }

        let date = new Date(cleanTimestamp);
        let parseMethod = 'standard';

        // 检查日期是否有效，如果无效则尝试通用解析器
        if (isNaN(date.getTime())) {
            console.log('[formatRelativeTime] 标准解析失败，尝试通用解析器...');

            // 尝试使用通用解析器
            if (window.parseAnyTimestamp) {
                const fallbackDate = window.parseAnyTimestamp(timestamp);
                if (fallbackDate) {
                    date = fallbackDate;
                    parseMethod = 'universal';
                    console.log('[formatRelativeTime] 通用解析器成功:', fallbackDate);
                } else {
                    console.log('[formatRelativeTime] 通用解析器也失败了');
                }
            }

            // 如果仍然无效
            if (isNaN(date.getTime())) {
                console.error('[formatRelativeTime] 无效的时间戳:', {
                    original: timestamp,
                    cleaned: cleanTimestamp,
                    parsed: date.toString()
                });

                // 增强的降级显示
                const originalStr = String(timestamp);
                const shortOriginal = originalStr.length > 20 ?
                    originalStr.substring(0, 17) + '...' : originalStr;

                return `[${shortOriginal}] 时间错误`;
            }
        }

        // 记录成功解析的信息
        console.log('[formatRelativeTime] 解析成功:', {
            method: parseMethod,
            original: timestamp,
            parsed: date
        });

        const now = new Date();
        const diffMs = now - date;
        const diff = Math.floor(diffMs / 1000); // 秒数差

        // 检查时间戳是否在未来
        if (diff < 0) {
            return '未来时间';
        }

        // 计算相对时间
        if (diff < 60) {
            return diff <= 1 ? '刚刚' : `${diff} 秒前`;
        } else if (diff < 3600) {
            const minutes = Math.floor(diff / 60);
            const seconds = diff % 60;
            return seconds < 10 ? `${minutes} 分钟前` : `${minutes} 分${seconds} 秒前`;
        } else if (diff < 86400) {
            const hours = Math.floor(diff / 3600);
            const minutes = Math.floor((diff % 3600) / 60);
            return minutes === 0 ? `${hours} 小时前` : `${hours} 小时${minutes} 分前`;
        } else if (diff < 604800) {
            const days = Math.floor(diff / 86400);
            const hours = Math.floor((diff % 86400) / 3600);
            return hours === 0 ? `${days} 天前` : `${days} 天${hours} 小时前`;
        } else {
            // 超过7天显示具体日期
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        }
    }

    /**
     * 格式化完整的日期时间（用于标题和提示）
     * @param {string} timestamp - ISO格式的时间戳
     * @returns {string} 完整的时间信息
     */
    formatFullDateTime(timestamp) {
        if (!timestamp) {
            return '时间未知';
        }

        // 使用格式化函数（避免重复解析）
        const localTime = this.formatDateTime(timestamp, { includeSeconds: false });

        // 如果解析失败，返回错误信息
        if (localTime === '时间未知' || localTime === '时间格式错误') {
            return localTime;
        }

        // 解析UTC时间（使用清理后的时间戳）
        let cleanTimestamp = timestamp;
        if (typeof timestamp === 'string') {
            cleanTimestamp = timestamp.trim().replace(/\n/g, '').replace(/\r/g, '');
        }

        const date = new Date(cleanTimestamp);
        if (isNaN(date.getTime())) {
            return localTime; // 返回本地时间，不添加UTC信息
        }

        // UTC时间
        const utcTime = date.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';

        // 使用空格而不是换行符分隔（HTML title属性兼容）
        return `${localTime} | UTC: ${utcTime}`;
    }

    getTimeAgo(timestamp) {
        // 使用新的统一格式化函数
        return this.formatRelativeTime(timestamp);
    }

    showTaskHistoryLoading(show) {
        const container = document.getElementById('task-history-list');
        if (!container) return;

        if (show) {
            container.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-2 text-muted">正在加载任务历史...</p>
                </div>
            `;
        }
    }

    showTaskHistoryError(error) {
        const container = document.getElementById('task-history-list');
        if (!container) {
            console.error('Task history container element not found');
            return;
        }

        container.innerHTML = `
            <div class="text-center text-danger py-5">
                <div class="mb-3">
                    <i class="fas fa-exclamation-triangle fa-3x opacity-50"></i>
                </div>
                <h5 class="mb-2">加载任务历史失败</h5>
                <p class="small mb-3">${error}</p>
                <button class="btn btn-primary btn-sm" onclick="phoneAgentWeb.loadTaskHistory()">
                    <i class="fas fa-redo"></i> 重试
                </button>
                <div class="mt-3">
                    <small class="text-muted">
                        请检查网络连接或<a href="#" onclick="location.reload()">刷新页面</a>
                    </small>
                </div>
            </div>
        `;
    }

    viewTaskReport(taskId) {
        // 在新窗口中打开任务报告页面
        window.open(`/tasks/${taskId}/report`, '_blank');
    }

    showToast(message, type = 'info') {
        const toastElement = document.getElementById('toast');
        const toastMessage = document.getElementById('toast-message');
        const toastHeader = toastElement.querySelector('.toast-header strong');

        // Update toast content
        toastMessage.textContent = message;

        // Update toast style based on type
        toastElement.className = 'toast';
        toastHeader.className = 'me-auto';

        if (type === 'success') {
            toastElement.classList.add('bg-success', 'text-white');
            toastHeader.textContent = '成功';
        } else if (type === 'error') {
            toastElement.classList.add('bg-danger', 'text-white');
            toastHeader.textContent = '错误';
        } else if (type === 'warning') {
            toastElement.classList.add('bg-warning', 'text-dark');
            toastHeader.textContent = '警告';
        } else {
            toastHeader.textContent = '信息';
        }

        // Show toast
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }

    initFloatingScreenshot() {
        try {
            this.floatingScreenshot = new FloatingScreenshotManager();
            console.log('Floating screenshot initialized');
        } catch (error) {
            console.error('Failed to initialize floating screenshot:', error);
            this.floatingScreenshot = null;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.phoneAgentWeb = new PhoneAgentWeb();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.phoneAgentWeb) {
        // 清理定时器
        if (window.phoneAgentWeb.updateTimer) {
            clearInterval(window.phoneAgentWeb.updateTimer);
        }
        if (window.phoneAgentWeb.batchProcessTimer) {
            clearTimeout(window.phoneAgentWeb.batchProcessTimer);
        }
        // 清理SmartScroller
        if (window.phoneAgentWeb.smartScroller) {
            window.phoneAgentWeb.smartScroller.destroy();
        }
    }
});

/**
 * Floating Screenshot Manager
 * Manages the floating screenshot window functionality
 */
class FloatingScreenshotManager {
    constructor() {
        this.window = document.getElementById('floating-screenshot');
        this.header = document.querySelector('.floating-screenshot-header');
        this.toggleBtn = document.getElementById('screenshot-toggle-btn');

        this.isVisible = false;
        this.isDragging = false;
        this.isMinimized = false;
        this.isMaximized = false;

        // Position management
        this.position = {
            x: 0,
            y: 0
        };

        // Drag state
        this.dragState = {
            startX: 0,
            startY: 0,
            startLeft: 0,
            startTop: 0
        };

        this.init();
    }

    init() {
        if (!this.window) {
            console.warn('Floating screenshot window not found');
            return;
        }

        // Load saved state
        this.loadState();

        // Setup event listeners
        this.setupDragListeners();
        this.setupControlButtons();
        this.setupKeyboardListeners();

        // Initialize position
        this.initializePosition();

        // Setup window resize handling
        this.setupResizeHandling();

        console.log('Floating screenshot manager initialized');
    }

    loadState() {
        try {
            const savedState = localStorage.getItem('floating-screenshot-state');
            if (savedState) {
                const state = JSON.parse(savedState);
                this.isVisible = state.isVisible !== false; // Default to true
                this.position = state.position || { x: 0, y: 0 };
                this.isMinimized = state.isMinimized || false;
                this.isMaximized = state.isMaximized || false;
            }
        } catch (error) {
            console.warn('Failed to load floating screenshot state:', error);
        }
    }

    saveState() {
        try {
            const state = {
                isVisible: this.isVisible,
                position: this.position,
                isMinimized: this.isMinimized,
                isMaximized: this.isMaximized
            };
            localStorage.setItem('floating-screenshot-state', JSON.stringify(state));
        } catch (error) {
            console.warn('Failed to save floating screenshot state:', error);
        }
    }

    initializePosition() {
        // Set initial position from saved state or defaults
        if (this.position.x !== 0 || this.position.y !== 0) {
            this.setPosition(this.position.x, this.position.y);
        } else {
            // Default position - top right of chat area
            const chatArea = document.querySelector('.chat-area');
            if (chatArea) {
                const rect = chatArea.getBoundingClientRect();
                const windowWidth = 300; // Default width
                const windowX = rect.right - windowWidth - 20;
                const windowY = rect.top + 80; // Below header
                this.setPosition(windowX, windowY);
            }
        }

        // Apply initial visibility
        if (this.isVisible) {
            this.show();
        } else {
            this.hide();
        }

        // Apply minimized/maximized state
        if (this.isMinimized) {
            this.minimize();
        } else if (this.isMaximized) {
            this.maximize();
        }
    }

    setupDragListeners() {
        if (!this.header) return;

        // Mouse events
        this.header.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));

        // Touch events
        this.header.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this));

        // Prevent text selection during drag
        this.header.addEventListener('selectstart', (e) => {
            if (this.isDragging) {
                e.preventDefault();
            }
        });
    }

    setupControlButtons() {
        const minimizeBtn = this.window.querySelector('.minimize-btn');
        const maximizeBtn = this.window.querySelector('.maximize-btn');
        const closeBtn = this.window.querySelector('.close-btn');

        if (minimizeBtn) {
            minimizeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.minimize();
            });
        }

        if (maximizeBtn) {
            maximizeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.isMaximized) {
                    this.restore();
                } else {
                    this.maximize();
                }
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.hide();
            });
        }
    }

    setupKeyboardListeners() {
        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hide();
            }
        });

        // Double click header to maximize/restore
        if (this.header) {
            this.header.addEventListener('dblclick', () => {
                if (this.isMaximized) {
                    this.restore();
                } else {
                    this.maximize();
                }
            });
        }
    }

    setupResizeHandling() {
        // Adjust position on window resize to keep it visible
        window.addEventListener('resize', () => {
            if (this.isVisible && !this.isMaximized) {
                this.constrainToViewport();
            }
        });
    }

    handleMouseDown(e) {
        if (this.isMaximized) return;

        this.isDragging = true;
        this.dragState.startX = e.clientX;
        this.dragState.startY = e.clientY;
        this.dragState.startLeft = this.position.x;
        this.dragState.startTop = this.position.y;

        this.window.classList.add('dragging');
        document.body.style.userSelect = 'none';

        e.preventDefault();
    }

    handleMouseMove(e) {
        if (!this.isDragging) return;

        const deltaX = e.clientX - this.dragState.startX;
        const deltaY = e.clientY - this.dragState.startY;

        const newX = this.dragState.startLeft + deltaX;
        const newY = this.dragState.startTop + deltaY;

        this.setPosition(newX, newY);
    }

    handleMouseUp(e) {
        if (!this.isDragging) return;

        this.isDragging = false;
        this.window.classList.remove('dragging');
        document.body.style.userSelect = '';

        this.saveState();
    }

    handleTouchStart(e) {
        if (this.isMaximized) return;

        const touch = e.touches[0];
        this.handleMouseDown({
            clientX: touch.clientX,
            clientY: touch.clientY,
            preventDefault: () => e.preventDefault()
        });
    }

    handleTouchMove(e) {
        if (!this.isDragging) return;

        const touch = e.touches[0];
        this.handleMouseMove({
            clientX: touch.clientX,
            clientY: touch.clientY
        });
    }

    handleTouchEnd(e) {
        this.handleMouseUp({});
    }

    setPosition(x, y) {
        this.position.x = x;
        this.position.y = y;

        this.constrainToViewport();

        this.window.style.left = `${this.position.x}px`;
        this.window.style.top = `${this.position.y}px`;
    }

    constrainToViewport() {
        const windowRect = this.window.getBoundingClientRect();
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };

        // Constrain horizontally
        if (this.position.x < 10) {
            this.position.x = 10;
        } else if (this.position.x + windowRect.width > viewport.width - 10) {
            this.position.x = viewport.width - windowRect.width - 10;
        }

        // Constrain vertically
        if (this.position.y < 10) {
            this.position.y = 10;
        } else if (this.position.y + windowRect.height > viewport.height - 10) {
            this.position.y = viewport.height - windowRect.height - 10;
        }
    }

    toggleVisibility() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        this.isVisible = true;
        this.window.classList.remove('hidden');

        if (this.toggleBtn) {
            this.toggleBtn.classList.add('active');
            this.toggleBtn.querySelector('i').className = 'fas fa-eye-slash';
        }

        this.saveState();
    }

    hide() {
        this.isVisible = false;
        this.window.classList.add('hidden');

        if (this.toggleBtn) {
            this.toggleBtn.classList.remove('active');
            this.toggleBtn.querySelector('i').className = 'fas fa-eye';
        }

        this.saveState();
    }

    minimize() {
        this.isMinimized = true;
        this.isMaximized = false;
        this.window.classList.add('minimized');
        this.window.classList.remove('maximized');

        // Update maximize button icon
        const maximizeBtn = this.window.querySelector('.maximize-btn i');
        if (maximizeBtn) {
            maximizeBtn.className = 'fas fa-expand';
        }

        this.saveState();
    }

    maximize() {
        this.isMinimized = false;
        this.isMaximized = true;
        this.window.classList.add('maximized');
        this.window.classList.remove('minimized');

        // Update maximize button icon
        const maximizeBtn = this.window.querySelector('.maximize-btn i');
        if (maximizeBtn) {
            maximizeBtn.className = 'fas fa-compress';
        }

        this.saveState();
    }

    restore() {
        this.isMinimized = false;
        this.isMaximized = false;
        this.window.classList.remove('minimized', 'maximized');

        // Update maximize button icon
        const maximizeBtn = this.window.querySelector('.maximize-btn i');
        if (maximizeBtn) {
            maximizeBtn.className = 'fas fa-expand';
        }

        this.saveState();
    }

    destroy() {
        // Remove event listeners
        if (this.header) {
            this.header.removeEventListener('mousedown', this.handleMouseDown.bind(this));
            this.header.removeEventListener('touchstart', this.handleTouchStart.bind(this));
        }

        document.removeEventListener('mousemove', this.handleMouseMove.bind(this));
        document.removeEventListener('mouseup', this.handleMouseUp.bind(this));
        document.removeEventListener('touchmove', this.handleTouchMove.bind(this));
        document.removeEventListener('touchend', this.handleTouchEnd.bind(this));

        // Clear references
        this.window = null;
        this.header = null;
        this.toggleBtn = null;
    }
}

/**
 * Markdown渲染器类 - 支持安全地将Markdown内容渲染为HTML
 */
class MarkdownRenderer {
    constructor() {
        this.initMarked();
        this.MAX_CONTENT_LENGTH = 50000; // 最大内容长度限制
    }

    /**
     * 初始化marked.js配置
     */
    initMarked() {
        if (typeof marked === 'undefined') {
            console.warn('marked.js not loaded, falling back to plain text');
            return;
        }

        // 配置marked.js选项
        marked.setOptions({
            gfm: true,              // 启用GitHub风格Markdown
            breaks: true,           // 支持换行
            headerIds: false,       // 禁用自动ID生成
            sanitize: false,        // 使用自定义清理
            smartLists: true,       // 智能列表
            smartypants: false      // 禁用智能标点
        });

        // 自定义渲染器
        const renderer = new marked.Renderer();
        this.configureRenderer(renderer);
        marked.setOptions({ renderer });
    }

    /**
     * 配置自定义渲染器
     */
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

        // 自定义图片渲染 - 添加安全属性
        renderer.image = (href, title, text) => {
            const safeHref = this.sanitizeUrl(href);
            const titleAttr = title ? ` title="${this.escapeHtml(title)}"` : '';
            const altAttr = text ? ` alt="${this.escapeHtml(text)}"` : '';
            return `<img src="${safeHref}"${altAttr}${titleAttr} style="max-width: 100%; height: auto;">`;
        };
    }

    /**
     * 检测内容是否为Markdown格式
     */
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

    /**
     * 渲染Markdown内容
     */
    render(content) {
        try {
            // 内容长度限制
            if (content.length > this.MAX_CONTENT_LENGTH) {
                console.warn('Content too long for safe rendering:', content.length);
                return this.escapeHtml(content);
            }

            // 检测是否为Markdown
            if (!this.isMarkdownContent(content)) {
                return this.escapeHtml(content);
            }

            // 检查marked.js是否可用
            if (typeof marked === 'undefined') {
                console.warn('marked.js not available, falling back to plain text');
                return this.escapeHtml(content);
            }

            // 渲染Markdown
            const html = marked.parse(content);

            // 清理HTML
            return this.sanitizeHtml(html);

        } catch (error) {
            console.error('Markdown rendering error:', error);
            return this.escapeHtml(content);
        }
    }

    /**
     * 转义HTML字符
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 清理HTML内容，移除危险元素
     */
    sanitizeHtml(html) {
        // 移除危险的HTML标签
        const dangerousTags = /<(script|iframe|object|embed|form|input|button|textarea|select|option|style|link|meta)[^>]*>/gi;

        // 移除危险的属性和事件处理器
        const dangerousAttrs = /(on\w+|javascript:|data:text\/html|vbscript:|data:script)/gi;

        // 移除危险的CSS样式
        const dangerousStyles = /(expression|behavior|javascript:|@import|binding)/gi;

        return html
            .replace(dangerousTags, '')
            .replace(dangerousAttrs, '')
            .replace(dangerousStyles, '');
    }

    /**
     * 清理URL，确保安全性
     */
    sanitizeUrl(url) {
        try {
            if (!url) return '#';

            // 只允许http/https/mailto/tel协议
            const parsed = new URL(url, window.location.origin);
            if (['http:', 'https:', 'mailto:', 'tel:'].includes(parsed.protocol)) {
                return parsed.toString();
            }
        } catch (e) {
            // URL解析失败，返回安全的默认值
            console.warn('Invalid URL:', url);
        }
        return '#';
    }

    /**
     * 验证代码语言是否在白名单中
     */
    isValidLanguage(language) {
        if (!language) return true;

        // 常见的代码语言白名单
        const validLanguages = [
            'javascript', 'js', 'typescript', 'ts', 'python', 'py', 'java', 'cpp', 'c', 'c++',
            'html', 'css', 'json', 'xml', 'yaml', 'yml', 'bash', 'shell', 'sh', 'sql',
            'markdown', 'md', 'go', 'rust', 'rs', 'php', 'ruby', 'rb', 'swift', 'kotlin',
            'kt', 'scala', 'r', 'dart', 'lua', 'perl', 'pl', 'objc', 'vb', 'dockerfile',
            'diff', 'patch', 'log', 'txt', 'text', 'plain', 'nginx', 'apache', 'ini'
        ];
        return validLanguages.includes(language.toLowerCase());
    }
}

// Global function for refreshing task history (called from HTML)
function refreshTaskHistory() {
    if (window.phoneAgentWeb) {
        window.phoneAgentWeb.loadTaskHistory();
    }
}

// 调试工具 - 时间戳深度分析
window.debugTimestamps = async function() {
    console.group('🛠️ [调试工具] 时间戳深度分析');

    try {
        // 获取任务数据
        const response = await fetch('/api/tasks');
        if (!response.ok) {
            console.error('无法获取任务数据:', response.status);
            return;
        }

        const data = await response.json();
        const tasks = data.data?.tasks || [];

        console.log('=== 任务时间戳分析报告 ===');
        console.log(`总任务数: ${tasks.length}`);
        console.log('');

        if (tasks.length === 0) {
            console.log('没有任务数据可分析');
            console.groupEnd();
            return;
        }

        // 分析每个任务的时间戳
        const analysis = tasks.map((task, index) => {
            const timestamp = task.start_time;
            console.log(`--- 任务 ${index + 1}: ${task.task_id} ---`);
            console.log('原始时间戳:', timestamp);
            console.log('数据类型:', typeof timestamp);

            // 测试多种解析方法
            const results = {
                original: timestamp,
                type: typeof timestamp,
                methods: {}
            };

            // 方法1: 直接new Date()
            try {
                const direct = new Date(timestamp);
                results.methods.direct = {
                    result: direct,
                    isValid: !isNaN(direct.getTime()),
                    string: direct.toString(),
                    iso: direct.toISOString()
                };
                console.log('直接解析:', results.methods.direct.isValid ? '✅' : '❌', results.methods.direct.string);
            } catch (e) {
                results.methods.direct = { error: e.message };
                console.log('直接解析: ❌ 错误:', e.message);
            }

            // 方法2: 清理后解析（移除可能的Z后缀）
            try {
                const cleaned = timestamp.toString().replace('Z', '');
                const cleanedDate = new Date(cleaned);
                results.methods.cleaned = {
                    result: cleanedDate,
                    isValid: !isNaN(cleanedDate.getTime()),
                    string: cleanedDate.toString(),
                    cleaned: cleaned
                };
                console.log('清理后解析:', results.methods.cleaned.isValid ? '✅' : '❌', results.methods.cleaned.string);
            } catch (e) {
                results.methods.cleaned = { error: e.message };
                console.log('清理后解析: ❌ 错误:', e.message);
            }

            // 方法3: 数字类型检查
            const numValue = Number(timestamp);
            if (!isNaN(numValue)) {
                try {
                    const numDate = new Date(numValue);
                    // 判断是毫秒还是秒
                    const isMs = numValue > 1000000000000; // 大于这个值认为是毫秒
                    const adjustedDate = isMs ? numDate : new Date(numValue * 1000);

                    results.methods.numeric = {
                        result: adjustedDate,
                        isValid: !isNaN(adjustedDate.getTime()),
                        string: adjustedDate.toString(),
                        isMs: isMs,
                        numericValue: numValue
                    };
                    console.log('数字解析:', results.methods.numeric.isValid ? '✅' : '❌',
                              `${results.methods.numeric.string} (${isMs ? 'ms' : 's'})`);
                } catch (e) {
                    results.methods.numeric = { error: e.message };
                    console.log('数字解析: ❌ 错误:', e.message);
                }
            } else {
                console.log('数字解析: ❌ 不是数字');
                results.methods.numeric = { error: '不是数字' };
            }

            // 方法4: Base64解码尝试
            try {
                const decoded = atob(timestamp);
                const base64Date = new Date(decoded);
                results.methods.base64 = {
                    result: base64Date,
                    isValid: !isNaN(base64Date.getTime()),
                    string: base64Date.toString(),
                    decoded: decoded
                };
                console.log('Base64解码:', results.methods.base64.isValid ? '✅' : '❌',
                          results.methods.base64.isValid ? results.methods.base64.string : '无效');
            } catch (e) {
                results.methods.base64 = { error: e.message };
                console.log('Base64解码: ❌ 不是Base64格式');
            }

            // 检查是否有有效的方法
            const validMethods = Object.values(results.methods).filter(m => m.isValid);
            results.hasValidMethod = validMethods.length > 0;
            results.bestMethod = validMethods[0] || null;

            console.log('最佳方法:', results.bestMethod ? '✅ 找到' : '❌ 无效');
            console.log('');

            return results;
        });

        // 生成总结报告
        console.log('=== 总结报告 ===');
        const validTasks = analysis.filter(a => a.hasValidMethod);
        const invalidTasks = analysis.filter(a => !a.hasValidMethod);

        console.log(`有效时间戳: ${validTasks.length}/${tasks.length}`);
        console.log(`无效时间戳: ${invalidTasks.length}/${tasks.length}`);

        if (invalidTasks.length > 0) {
            console.log('\n无效时间戳的任务:');
            invalidTasks.forEach(a => {
                console.log(`- ${a.original} (${a.type})`);
            });
        }

        // 提供复制功能
        console.log('\n=== 复制到剪贴板 ===');
        const reportData = {
            summary: {
                total: tasks.length,
                valid: validTasks.length,
                invalid: invalidTasks.length
            },
            analysis: analysis,
            timestamp: new Date().toISOString()
        };

        // 创建可复制的JSON字符串
        const jsonString = JSON.stringify(reportData, null, 2);
        console.log('复制以下命令到剪贴板来导出完整报告:');
        console.log('copy(' + JSON.stringify(jsonString) + ')');

        // 自动复制到剪贴板
        if (navigator.clipboard) {
            navigator.clipboard.writeText(jsonString).then(() => {
                console.log('✅ 报告已自动复制到剪贴板');
            }).catch(() => {
                console.log('❌ 自动复制失败，请手动复制上面的命令');
            });
        }

    } catch (error) {
        console.error('调试工具执行出错:', error);
    }

    console.groupEnd();
};

// 通用时间戳解析器
window.parseAnyTimestamp = function(timestamp) {
    console.group('🔧 [通用解析器] 解析时间戳');
    console.log('输入:', timestamp, '类型:', typeof timestamp);

    const results = [];

    // 尝试1: 直接解析
    try {
        const direct = new Date(timestamp);
        if (!isNaN(direct.getTime())) {
            results.push({ method: 'direct', date: direct, confidence: 5 });
            console.log('✅ 直接解析成功:', direct);
        }
    } catch (e) {
        console.log('❌ 直接解析失败:', e.message);
    }

    // 尝试2: 清理Z后缀
    if (typeof timestamp === 'string') {
        const cleaned = timestamp.replace('Z', '');
        try {
            const cleanedDate = new Date(cleaned);
            if (!isNaN(cleanedDate.getTime())) {
                results.push({ method: 'cleaned', date: cleanedDate, confidence: 4 });
                console.log('✅ 清理后解析成功:', cleanedDate);
            }
        } catch (e) {
            console.log('❌ 清理后解析失败:', e.message);
        }
    }

    // 尝试3: 数字解析（毫秒/秒）
    const numValue = Number(timestamp);
    if (!isNaN(numValue) && numValue > 0) {
        try {
            const isMs = numValue > 1000000000000;
            const adjustedValue = isMs ? numValue : numValue * 1000;
            const numDate = new Date(adjustedValue);
            if (!isNaN(numDate.getTime())) {
                results.push({
                    method: 'numeric',
                    date: numDate,
                    confidence: 3,
                    details: `作为${isMs ? '毫秒' : '秒'}处理`
                });
                console.log('✅ 数字解析成功:', numDate, `(${isMs ? '毫秒' : '秒'})`);
            }
        } catch (e) {
            console.log('❌ 数字解析失败:', e.message);
        }
    }

    // 尝试4: Base64解码
    if (typeof timestamp === 'string' && timestamp.length > 4) {
        try {
            const decoded = atob(timestamp);
            const base64Date = new Date(decoded);
            if (!isNaN(base64Date.getTime())) {
                results.push({
                    method: 'base64',
                    date: base64Date,
                    confidence: 2,
                    details: `解码为: ${decoded}`
                });
                console.log('✅ Base64解析成功:', base64Date);
            }
        } catch (e) {
            console.log('❌ Base64解析失败:', e.message);
        }
    }

    // 尝试5: 特殊格式处理
    if (typeof timestamp === 'string') {
        // 处理可能的格式如 "/Date(1234567890)/"
        const dateMatch = timestamp.match(/\/Date\((\d+)\)\//);
        if (dateMatch) {
            try {
                const dotNetDate = new Date(parseInt(dateMatch[1]));
                if (!isNaN(dotNetDate.getTime())) {
                    results.push({
                        method: 'dotnet',
                        date: dotNetDate,
                        confidence: 3,
                        details: 'ASP.NET MVC格式'
                    });
                    console.log('✅ .NET格式解析成功:', dotNetDate);
                }
            } catch (e) {
                console.log('❌ .NET格式解析失败:', e.message);
            }
        }
    }

    // 选择最佳结果（按置信度排序）
    const bestResult = results.sort((a, b) => b.confidence - a.confidence)[0];

    if (bestResult) {
        console.log(`🎯 最佳解析方法: ${bestResult.method}`, bestResult.date, bestResult.details || '');
        console.groupEnd();
        return bestResult.date;
    } else {
        console.log('❌ 所有解析方法都失败了');
        console.groupEnd();
        return null;
    }
};

// 添加到控制台的帮助信息
console.log('🛠️ 时间戳调试工具已加载！');
console.log('使用 debugTimestamps() 分析所有任务的时间戳');
console.log('使用 parseAnyTimestamp(timestamp) 解析单个时间戳');