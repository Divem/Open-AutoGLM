// Phone Agent Web Interface - Main Application JavaScript

class PhoneAgentWeb {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.taskStartTime = null;
        this.updateTimer = null;
        this.stepCount = 0;

        this.init();
    }

    init() {
        // Initialize Socket.IO connection
        this.socket = io();
        this.setupSocketListeners();

        // Setup UI event listeners
        this.setupUIListeners();

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
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.isConnected = false;
            this.updateConnectionStatus(false);
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

        // Periodic updates
        this.updateTimer = setInterval(() => {
            this.updateExecutionTime();
        }, 1000);
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
        const roleClass = role === 'user' ? '用户' : role === 'assistant' ? '助手' : '系统';

        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-header mb-1">
                    <small><i class="${roleIcon} me-1"></i>${roleClass}</small>
                </div>
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;

        // Remove welcome message if exists
        const welcomeMsg = chatContainer.querySelector('.text-center.text-muted');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
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
        chatContainer.scrollTop = chatContainer.scrollHeight;
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
        const container = document.getElementById('screenshot-container');

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

            container.innerHTML = `
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
        } else {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-image fa-2x mb-2"></i>
                    <p class="small">暂无截图</p>
                </div>
            `;
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
            const response = await fetch('/api/tasks');
            if (response.ok) {
                const data = await response.json();
                this.updateTaskHistoryList(data.tasks);
            }
        } catch (error) {
            console.error('Error loading task history:', error);
            this.updateTaskHistoryList([]);
        }
    }

    async stopHistoryTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.showToast(data.message, 'success');
                // 刷新任务历史
                await this.loadTaskHistory();
            } else {
                const errorData = await response.json();
                this.showToast(errorData.error || '停止任务失败', 'error');
            }
        } catch (error) {
            console.error('Error stopping history task:', error);
            this.showToast('停止任务失败', 'error');
        }
    }

    async viewTaskDetails(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`);
            if (response.ok) {
                const task = await response.json();
                // 显示任务详情
                this.showTaskDetails(task);
            } else {
                this.showToast('获取任务详情失败', 'error');
            }
        } catch (error) {
            console.error('Error viewing task details:', error);
            this.showToast('获取任务详情失败', 'error');
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
        // Convert URLs to links
        content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');

        // Convert newlines to <br>
        content = content.replace(/\n/g, '<br>');

        // Format JSON blocks
        content = content.replace(/```json\n([\s\S]*?)\n```/g,
            '<div class="code-block mt-2 mb-2"><pre><code>$1</code></pre></div>');

        return content;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    updateTaskHistoryList(tasks) {
        const container = document.getElementById('task-history-list');

        if (!tasks || tasks.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <p class="small">暂无任务历史</p>
                </div>
            `;
            return;
        }

        const tasksHtml = tasks.map(task => {
            const statusClass = task.status;
            const statusText = this.getStatusText(task.status);
            const timeAgo = this.getTimeAgo(task.start_time);

            return `
                <div class="task-history-item ${statusClass}" data-task-id="${task.global_task_id}">
                    <div class="task-header">
                        <div class="task-title" title="${task.task || '无任务描述'}">
                            ${task.task ? task.task.substring(0, 30) + (task.task.length > 30 ? '...' : '') : '无任务描述'}
                        </div>
                        <span class="task-status bg-${statusClass === 'running' ? 'success' : statusClass === 'completed' ? 'primary' : statusClass === 'error' ? 'danger' : statusClass === 'stopped' ? 'warning' : 'secondary'} text-white">
                            ${statusText}
                        </span>
                    </div>
                    <div class="task-time">${timeAgo}</div>
                    ${task.task && task.task.length > 30 ? `<div class="task-description">${task.task}</div>` : ''}
                    <div class="task-actions">
                        ${task.status === 'running' ? `
                            <button class="stop-btn" onclick="phoneAgentWeb.stopHistoryTask('${task.global_task_id}')">
                                <i class="fas fa-stop"></i> 停止
                            </button>
                        ` : ''}
                        <button class="view-btn" onclick="phoneAgentWeb.viewTaskDetails('${task.global_task_id}')">
                            <i class="fas fa-eye"></i> 查看
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = tasksHtml;
    }

    showTaskDetails(task) {
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
                                <div class="col-sm-9"><code>${task.global_task_id}</code></div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-sm-3"><strong>任务描述:</strong></div>
                                <div class="col-sm-9">${task.task || '无'}</div>
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
                                <div class="col-sm-9">${new Date(task.start_time).toLocaleString()}</div>
                            </div>
                            ${task.end_time ? `
                                <div class="row mb-3">
                                    <div class="col-sm-3"><strong>结束时间:</strong></div>
                                    <div class="col-sm-9">${new Date(task.end_time).toLocaleString()}</div>
                                </div>
                            ` : ''}
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
                            ${task.error ? `
                                <div class="row mb-3">
                                    <div class="col-sm-3"><strong>错误信息:</strong></div>
                                    <div class="col-sm-9">
                                        <div class="alert alert-danger">
                                            <pre style="white-space: pre-wrap; margin: 0;">${this.escapeHtml(task.error)}</pre>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            ${task.status === 'running' ? `
                                <button type="button" class="btn btn-danger" onclick="phoneAgentWeb.stopHistoryTask('${task.global_task_id}'); bootstrap.Modal.getInstance(document.getElementById('taskDetailsModal')).hide();">
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

    getTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = Math.floor((now - time) / 1000); // 秒数差

        if (diff < 60) {
            return '刚刚';
        } else if (diff < 3600) {
            return `${Math.floor(diff / 60)} 分钟前`;
        } else if (diff < 86400) {
            return `${Math.floor(diff / 3600)} 小时前`;
        } else if (diff < 604800) {
            return `${Math.floor(diff / 86400)} 天前`;
        } else {
            return time.toLocaleDateString();
        }
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
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.phoneAgentWeb = new PhoneAgentWeb();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.phoneAgentWeb && window.phoneAgentWeb.updateTimer) {
        clearInterval(window.phoneAgentWeb.updateTimer);
    }
});

// Global function for refreshing task history (called from HTML)
function refreshTaskHistory() {
    if (window.phoneAgentWeb) {
        window.phoneAgentWeb.loadTaskHistory();
    }
}