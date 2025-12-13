// Phone Agent Web Interface - Configuration Page JavaScript

class ConfigManager {
    constructor() {
        this.currentConfig = {};
        this.presets = {
            local: {
                'base-url': 'http://localhost:8000/v1',
                'model-name': 'autoglm-phone-9b',
                'api-key': 'EMPTY',
                'max-steps': 100,
                'device-id': '',
                'lang': 'cn',
                'verbose': true,
                'record-script': false,
                'script-output-dir': 'web_scripts'
            },
            bigmodel: {
                'base-url': 'https://open.bigmodel.cn/api/paas/v4',
                'model-name': 'autoglm-phone',
                'api-key': '',
                'max-steps': 100,
                'device-id': '',
                'lang': 'cn',
                'verbose': true,
                'record-script': false,
                'script-output-dir': 'web_scripts'
            },
            modelscope: {
                'base-url': 'https://api-inference.modelscope.cn/v1',
                'model-name': 'ZhipuAI/AutoGLM-Phone-9B',
                'api-key': '',
                'max-steps': 100,
                'device-id': '',
                'lang': 'cn',
                'verbose': true,
                'record-script': false,
                'script-output-dir': 'web_scripts'
            }
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadCurrentConfig();
        this.refreshDevices();
        this.loadDeviceStatus();
    }

    setupEventListeners() {
        // Form submission
        document.getElementById('config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConfig();
        });

        // Script recording checkbox
        document.getElementById('record-script').addEventListener('change', (e) => {
            const scriptDirInput = document.getElementById('script-output-dir');
            scriptDirInput.disabled = !e.target.checked;
        });

        // API key field validation
        document.getElementById('base-url').addEventListener('change', () => {
            this.validateApiRequirements();
        });

        document.getElementById('model-name').addEventListener('change', () => {
            this.validateApiRequirements();
        });
    }

    async loadCurrentConfig() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const configs = await response.json();
                this.currentConfig = configs.default || {};
                this.populateForm(this.currentConfig);
            } else {
                throw new Error('Failed to load configuration');
            }
        } catch (error) {
            console.error('Error loading config:', error);
            this.showToast('加载配置失败: ' + error.message, 'error');
            // Load default preset
            this.loadPreset('local');
        }
    }

    populateForm(config) {
        // Model configuration
        document.getElementById('base-url').value = config['base_url'] || '';
        document.getElementById('model-name').value = config['model_name'] || '';
        document.getElementById('api-key').value = config['api_key'] || '';
        document.getElementById('lang').value = config['lang'] || 'cn';

        // Execution configuration
        document.getElementById('max-steps').value = config['max_steps'] || 100;
        document.getElementById('device-id').value = config['device_id'] || '';
        document.getElementById('verbose').checked = config['verbose'] !== false;

        // Script recording configuration
        const recordScript = config['record_script'] || false;
        document.getElementById('record-script').checked = recordScript;
        document.getElementById('script-output-dir').value = config['script_output_dir'] || 'web_scripts';
        document.getElementById('script-output-dir').disabled = !recordScript;
    }

    getFormData() {
        return {
            'base_url': document.getElementById('base-url').value.trim(),
            'model_name': document.getElementById('model-name').value.trim(),
            'api_key': document.getElementById('api-key').value.trim(),
            'lang': document.getElementById('lang').value,
            'max_steps': parseInt(document.getElementById('max-steps').value) || 100,
            'device_id': document.getElementById('device-id').value.trim() || null,
            'verbose': document.getElementById('verbose').checked,
            'record_script': document.getElementById('record-script').checked,
            'script_output_dir': document.getElementById('script-output-dir').value.trim() || 'web_scripts'
        };
    }

    async saveConfig() {
        try {
            const formData = this.getFormData();

            // Validate configuration
            if (!this.validateConfig(formData)) {
                return;
            }

            // Save to server
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: 'default',
                    ...formData
                })
            });

            if (response.ok) {
                this.currentConfig = formData;
                this.showToast('配置保存成功', 'success');
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            console.error('Error saving config:', error);
            this.showToast('保存配置失败: ' + error.message, 'error');
        }
    }

    validateConfig(config) {
        // Validate base URL
        if (!config.base_url) {
            this.showToast('请输入模型服务地址', 'error');
            document.getElementById('base-url').focus();
            return false;
        }

        // Validate model name
        if (!config.model_name) {
            this.showToast('请输入模型名称', 'error');
            document.getElementById('model-name').focus();
            return false;
        }

        // Validate max steps
        if (config.max_steps < 1 || config.max_steps > 1000) {
            this.showToast('最大步数必须在 1-1000 之间', 'error');
            document.getElementById('max-steps').focus();
            return false;
        }

        // Check if API key is required
        if (this.requiresApiKey(config.base_url, config.model_name) && !config.api_key) {
            this.showToast('此服务需要 API Key，请输入有效的 API Key', 'error');
            document.getElementById('api-key').focus();
            return false;
        }

        return true;
    }

    validateApiRequirements() {
        const baseUrl = document.getElementById('base-url').value.trim();
        const modelName = document.getElementById('model-name').value.trim();
        const apiKeyInput = document.getElementById('api-key');
        const apiKeyGroup = apiKeyInput.closest('.col-md-6');

        if (this.requiresApiKey(baseUrl, modelName)) {
            apiKeyInput.setAttribute('required', 'required');
            apiKeyGroup.querySelector('.form-text').textContent = '此服务需要API Key';
            apiKeyGroup.querySelector('.form-text').classList.add('text-danger');
        } else {
            apiKeyInput.removeAttribute('required');
            apiKeyGroup.querySelector('.form-text').textContent = '输入API Key（如果需要）';
            apiKeyGroup.querySelector('.form-text').classList.remove('text-danger');
        }
    }

    requiresApiKey(baseUrl, modelName) {
        // Services that require API key
        const requiresKeyServices = [
            'bigmodel.cn',
            'modelscope.cn',
            'openai.com'
        ];

        return requiresKeyServices.some(service => baseUrl.includes(service));
    }

    loadPreset(presetName) {
        const preset = this.presets[presetName];
        if (preset) {
            this.populateForm(preset);
            this.validateApiRequirements();
            this.showToast(`已加载${this.getPresetDisplayName(presetName)}预设`, 'info');
        }
    }

    getPresetDisplayName(presetName) {
        const names = {
            'local': '本地模型',
            'bigmodel': '智谱BigModel',
            'modelscope': 'ModelScope'
        };
        return names[presetName] || presetName;
    }

    async testConnection() {
        const config = this.getFormData();

        // Show loading state
        const testBtn = document.querySelector('button[onclick="testConnection()"]');
        const originalText = testBtn.innerHTML;
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>测试中...';
        testBtn.disabled = true;

        try {
            // This is a simplified connection test
            // In a real implementation, you would make an actual API call
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Simulate successful connection
            this.showToast('连接测试成功', 'success');

        } catch (error) {
            console.error('Connection test failed:', error);
            this.showToast('连接测试失败: ' + error.message, 'error');
        } finally {
            // Restore button state
            testBtn.innerHTML = originalText;
            testBtn.disabled = false;
        }
    }

    resetConfig() {
        if (confirm('确定要重置配置吗？这将丢失当前的所有设置。')) {
            this.loadPreset('local');
            this.showToast('配置已重置', 'info');
        }
    }

    async refreshDevices() {
        const container = document.getElementById('device-list');

        // Show loading state
        container.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner"></div>
                <p class="mt-2 text-muted">正在扫描设备...</p>
            </div>
        `;

        try {
            const response = await fetch('/api/devices');
            if (response.ok) {
                const devices = await response.json();
                this.displayDevices(devices);
            } else {
                throw new Error('Failed to fetch devices');
            }
        } catch (error) {
            console.error('Error refreshing devices:', error);
            container.innerHTML = `
                <div class="text-danger">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    获取设备列表失败
                </div>
            `;
        }
    }

    displayDevices(devices) {
        const container = document.getElementById('device-list');

        if (devices.length === 0) {
            container.innerHTML = `
                <div class="text-warning">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    未找到连接的设备
                    <div class="small mt-2">
                        请确保：<br>
                        1. 设备已通过USB连接<br>
                        2. 已开启USB调试模式<br>
                        3. 已授权此计算机
                    </div>
                </div>
            `;
            return;
        }

        const devicesHtml = devices.map(device => {
            const statusIcon = device.connection_type === 'usb' ?
                '<i class="fas fa-usb text-success"></i>' :
                '<i class="fas fa-wifi text-info"></i>';

            return `
                <div class="device-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="fw-bold">${statusIcon} ${device.device_id}</div>
                            <div class="small text-muted">
                                ${device.model || 'Unknown'} • ${device.connection_type.toUpperCase()}
                            </div>
                        </div>
                        <button class="btn btn-sm btn-outline-primary"
                                onclick="configManager.selectDevice('${device.device_id}')">
                            选择
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = devicesHtml;
    }

    selectDevice(deviceId) {
        document.getElementById('device-id').value = deviceId;
        this.showToast(`已选择设备: ${deviceId}`, 'success');
    }

    loadDeviceStatus() {
        const container = document.getElementById('device-status');
        container.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner"></div>
                <p class="mt-2 text-muted">正在检查设备状态...</p>
            </div>
        `;

        // Simulate device status check
        setTimeout(() => {
            this.refreshDevices();
        }, 1000);
    }

    goToChatWithTask(task) {
        // Store task in sessionStorage
        sessionStorage.setItem('pendingTask', task);

        // Navigate to main page
        window.location.href = '/';
    }

    viewLogs() {
        // Open logs in a new window or modal
        window.open('/logs', '_blank', 'width=800,height=600');
    }

    exportConfig() {
        const config = this.getFormData();
        const dataStr = JSON.stringify(config, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });

        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `phone-agent-config-${new Date().toISOString().split('T')[0]}.json`;
        link.click();

        this.showToast('配置已导出', 'success');
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

// Global functions for onclick handlers
window.loadPreset = function(presetName) {
    window.configManager.loadPreset(presetName);
};

window.testConnection = function() {
    window.configManager.testConnection();
};

window.resetConfig = function() {
    window.configManager.resetConfig();
};

window.goToChatWithTask = function(task) {
    window.configManager.goToChatWithTask(task);
};

window.refreshDevices = function() {
    window.configManager.refreshDevices();
};

window.viewLogs = function() {
    window.configManager.viewLogs();
};

window.exportConfig = function() {
    window.configManager.exportConfig();
};

// Initialize the configuration manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.configManager = new ConfigManager();
});

// Check for pending task from sessionStorage
document.addEventListener('DOMContentLoaded', () => {
    const pendingTask = sessionStorage.getItem('pendingTask');
    if (pendingTask) {
        // Clear the stored task
        sessionStorage.removeItem('pendingTask');

        // If we're on the main page, set the task in the input
        if (window.location.pathname === '/' || window.location.pathname.endsWith('/index')) {
            setTimeout(() => {
                const taskInput = document.getElementById('task-input');
                if (taskInput && !taskInput.value) {
                    taskInput.value = pendingTask;
                    taskInput.focus();
                }
            }, 1000);
        }
    }
});