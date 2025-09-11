/**
 * StreamlineVPN Main JavaScript Application
 * Handles all frontend functionality for the control panel
 */

class StreamlineVPNApp {
    constructor() {
        this.apiBase = window.__API_BASE__ || 'http://localhost:8080';
        this.state = {
            isConnected: false,
            statistics: {},
            configurations: [],
            sources: [],
            jobs: {},
            logs: []
        };
        
        this.elements = {};
        this.intervals = {};
        
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        this.bindElements();
        this.setupEventListeners();
        await this.checkConnection();
        this.startPeriodicUpdates();
        
        console.log('[StreamlineVPN] Application initialized');
    }

    /**
     * Bind DOM elements to properties
     */
    bindElements() {
        this.elements = {
            // Statistics elements
            totalSources: document.getElementById('totalSources'),
            totalConfigs: document.getElementById('totalConfigs'),
            activeSources: document.getElementById('activeSources'),
            lastUpdated: document.getElementById('lastUpdated'),
            
            // Lists
            configList: document.getElementById('configsList'),
            sourceList: document.getElementById('sourcesList'),
            
            // Forms and inputs
            processingForm: document.getElementById('processingForm'),
            configPath: document.getElementById('configPath'),
            formatCheckboxes: document.querySelectorAll('.format-cb'),
            
            // Buttons
            startProcessingBtn: document.getElementById('startProcessingBtn'),
            testConnectionBtn: document.getElementById('testConnectionBtn'),
            
            // Status and progress
            apiStatus: document.getElementById('apiStatus'),
            progressContainer: document.getElementById('progressContainer'),
            progressBar: document.getElementById('progressBar'),
            progressPercent: document.getElementById('progressPercent'),
            progressMessage: document.getElementById('progressMessage'),
            
            // Terminal/logs
            terminal: document.getElementById('logsContainer'),
            
            // Notifications
            notificationArea: document.getElementById('notificationArea')
        };
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Processing button
        if (this.elements.startProcessingBtn) {
            this.elements.startProcessingBtn.addEventListener('click', () => this.startProcessing());
        }

        // Test connection button
        if (this.elements.testConnectionBtn) {
            this.elements.testConnectionBtn.addEventListener('click', () => this.testConnection());
        }

        // Form submissions
        if (this.elements.processingForm) {
            this.elements.processingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startProcessing();
            });
        }

        // Add source functionality
        const addSourceBtn = document.getElementById('addSourceBtn');
        if (addSourceBtn) {
            addSourceBtn.addEventListener('click', () => this.addSource());
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshAllData();
                        break;
                    case 't':
                        e.preventDefault();
                        this.testConnection();
                        break;
                }
            }
        });
    }

    /**
     * Make API request with error handling
     */
    async makeRequest(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            this.addTerminalLine(`API Request Failed: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Check API connection
     */
    async checkConnection() {
        try {
            const response = await this.makeRequest('/health');
            this.state.isConnected = true;
            this.updateConnectionStatus('connected', 'API Connected');
            this.addTerminalLine(`API connection successful: ${response.status}`, 'success');
            this.showNotification('API connection established!', 'success');
            return true;
        } catch (error) {
            this.state.isConnected = false;
            this.updateConnectionStatus('disconnected', 'API Disconnected');
            this.addTerminalLine(`API connection failed: ${error.message}`, 'error');
            this.showNotification('API connection failed!', 'error');
            return false;
        }
    }

    /**
     * Test connection manually
     */
    async testConnection() {
        this.addTerminalLine('Testing API connection...', 'info');
        await this.checkConnection();
    }

    /**
     * Update connection status UI
     */
    updateConnectionStatus(status, message) {
        if (!this.elements.apiStatus) return;
        
        const indicator = this.elements.apiStatus.querySelector('.status-indicator');
        const text = this.elements.apiStatus.querySelector('span:last-child');
        
        if (indicator) {
            indicator.className = `status-indicator status-${status === 'connected' ? 'active' : 'inactive'}`;
        }
        
        if (text) {
            text.textContent = message;
        }
    }

    /**
     * Load statistics from API
     */
    async loadStatistics() {
        try {
            const stats = await this.makeRequest('/api/v1/statistics');
            this.state.statistics = stats;
            this.renderStatistics();
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }

    /**
     * Render statistics in UI
     */
    renderStatistics() {
        const stats = this.state.statistics;
        
        if (this.elements.totalSources) {
            this.elements.totalSources.textContent = stats.total_sources || '0';
        }
        
        if (this.elements.totalConfigs) {
            this.elements.totalConfigs.textContent = stats.total_configurations || '0';
        }
        
        if (this.elements.activeSources) {
            this.elements.activeSources.textContent = stats.active_sources || '0';
        }
        
        if (this.elements.lastUpdated) {
            this.elements.lastUpdated.textContent = this.formatDate(stats.last_updated);
        }
    }

    /**
     * Load configurations
     */
    async loadConfigurations() {
        if (!this.elements.configList) return;
        
        try {
            this.elements.configList.innerHTML = this.getLoadingHTML();
            
            const response = await this.makeRequest('/api/v1/configurations?limit=50');
            this.state.configurations = response.configurations || [];
            this.renderConfigurations();
        } catch (error) {
            this.elements.configList.innerHTML = this.getErrorHTML('Failed to load configurations');
            console.error('Failed to load configurations:', error);
        }
    }

    /**
     * Render configurations list
     */
    renderConfigurations() {
        if (!this.elements.configList) return;
        
        const configs = this.state.configurations;
        
        if (!configs || configs.length === 0) {
            this.elements.configList.innerHTML = this.getEmptyHTML('No configurations available');
            return;
        }
        
        let html = '';
        configs.forEach(config => {
            const qualityScore = Math.round((config.quality_score || 0) * 100);
            html += `
                <div class="config-item dark-glass rounded-lg p-4 mb-2">
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="font-medium">${config.protocol.toUpperCase()}</div>
                            <div class="text-sm text-gray-400">${config.server}:${config.port}</div>
                            ${config.name ? `<div class="text-xs text-gray-500">${config.name}</div>` : ''}
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-medium ${qualityScore >= 70 ? 'text-green-400' : qualityScore >= 40 ? 'text-yellow-400' : 'text-red-400'}">${qualityScore}%</div>
                            <div class="text-xs text-gray-400">Quality</div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        this.elements.configList.innerHTML = html;
    }

    /**
     * Load sources
     */
    async loadSources() {
        if (!this.elements.sourceList) return;
        
        try {
            this.elements.sourceList.innerHTML = this.getLoadingHTML();
            
            const response = await this.makeRequest('/api/v1/sources');
            this.state.sources = response.sources || [];
            this.renderSources();
        } catch (error) {
            this.elements.sourceList.innerHTML = this.getErrorHTML('Failed to load sources');
            console.error('Failed to load sources:', error);
        }
    }

    /**
     * Render sources list
     */
    renderSources() {
        if (!this.elements.sourceList) return;
        
        const sources = this.state.sources;
        
        if (!sources || sources.length === 0) {
            this.elements.sourceList.innerHTML = this.getEmptyHTML('No sources configured');
            return;
        }
        
        let html = '';
        sources.forEach(source => {
            const successRate = Math.round((source.success_rate || 0) * 100);
            html += `
                <div class="config-item dark-glass rounded-lg p-4 mb-2">
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="font-medium truncate">${source.url}</div>
                            <div class="text-sm text-gray-400">
                                Configs: ${source.configs || 0} | 
                                Success: ${successRate}% |
                                Latency: ${source.avg_response_time || 0}ms
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="status-indicator status-${source.status === 'active' ? 'active' : 'inactive'}"></span>
                            <span class="text-sm capitalize">${source.status || 'unknown'}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        this.elements.sourceList.innerHTML = html;
    }

    /**
     * Start processing pipeline
     */
    async startProcessing() {
        if (!this.elements.startProcessingBtn) return;
        
        const configPath = this.elements.configPath?.value || 'config/sources.yaml';
        const formats = Array.from(this.elements.formatCheckboxes || [])
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        if (formats.length === 0) {
            this.showNotification('Please select at least one output format', 'warning');
            return;
        }
        
        // Update UI state
        this.elements.startProcessingBtn.disabled = true;
        this.elements.startProcessingBtn.innerHTML = '<div class="spinner inline-block mr-2"></div>Processing...';
        
        if (this.elements.progressContainer) {
            this.elements.progressContainer.classList.remove('hidden');
        }
        
        try {
            const response = await this.makeRequest('/api/v1/pipeline/run', {
                method: 'POST',
                body: JSON.stringify({
                    config_path: configPath,
                    output_dir: 'output',
                    formats: formats
                })
            });
            
            const jobId = response.job_id;
            this.addTerminalLine(`Processing started (Job: ${jobId})`, 'success');
            this.showNotification('Processing pipeline started successfully!', 'success');
            
            // Start polling job status
            this.pollJobStatus(jobId);
            
        } catch (error) {
            this.addTerminalLine(`Processing failed: ${error.message}`, 'error');
            this.showNotification(`Processing failed: ${error.message}`, 'error');
            this.resetProcessingUI();
        }
    }

    /**
     * Poll job status
     */
    async pollJobStatus(jobId) {
        const pollInterval = setInterval(async () => {
            try {
                const status = await this.makeRequest(`/api/v1/pipeline/status/${jobId}`);
                
                this.updateProgress(status.progress * 100, status.status);
                
                if (status.status === 'completed') {
                    clearInterval(pollInterval);
                    this.addTerminalLine('Processing completed successfully', 'success');
                    this.showNotification('Processing completed successfully!', 'success');
                    this.resetProcessingUI();
                    await this.refreshAllData();
                } else if (status.status === 'failed') {
                    clearInterval(pollInterval);
                    this.addTerminalLine(`Processing failed: ${status.error || 'Unknown error'}`, 'error');
                    this.showNotification(`Processing failed: ${status.error || 'Unknown error'}`, 'error');
                    this.resetProcessingUI();
                }
                
            } catch (error) {
                clearInterval(pollInterval);
                this.addTerminalLine(`Status polling failed: ${error.message}`, 'error');
                this.resetProcessingUI();
            }
        }, 2000);
    }

    /**
     * Update progress UI
     */
    updateProgress(percent, message) {
        if (this.elements.progressBar) {
            this.elements.progressBar.style.width = `${percent}%`;
        }
        
        if (this.elements.progressPercent) {
            this.elements.progressPercent.textContent = `${Math.round(percent)}%`;
        }
        
        if (this.elements.progressMessage) {
            this.elements.progressMessage.textContent = message;
        }
    }

    /**
     * Reset processing UI
     */
    resetProcessingUI() {
        if (this.elements.startProcessingBtn) {
            this.elements.startProcessingBtn.disabled = false;
            this.elements.startProcessingBtn.innerHTML = 'Start Processing';
        }
        
        if (this.elements.progressContainer) {
            this.elements.progressContainer.classList.add('hidden');
        }
    }

    /**
     * Add source
     */
    async addSource() {
        const input = document.getElementById('newSourceUrl');
        if (!input) return;
        
        const url = input.value.trim();
        if (!url) {
            this.showNotification('Please enter a valid URL', 'warning');
            return;
        }
        
        try {
            const response = await this.makeRequest('/api/v1/sources/add', {
                method: 'POST',
                body: JSON.stringify({ url })
            });
            
            this.addTerminalLine(response.message || 'Source added successfully', 'success');
            this.showNotification('Source added successfully!', 'success');
            input.value = '';
            await this.loadSources();
        } catch (error) {
            this.addTerminalLine(`Add source error: ${error.message}`, 'error');
            this.showNotification(`Failed to add source: ${error.message}`, 'error');
        }
    }

    /**
     * Add terminal line
     */
    addTerminalLine(message, type = 'info') {
        if (!this.elements.terminal) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const colorMap = {
            'info': 'text-blue-400',
            'success': 'text-green-400',
            'warning': 'text-yellow-400',
            'error': 'text-red-400'
        };
        
        const logEntry = document.createElement('div');
        logEntry.className = `${colorMap[type] || 'text-gray-300'}`;
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        this.elements.terminal.appendChild(logEntry);
        this.elements.terminal.scrollTop = this.elements.terminal.scrollHeight;
        
        // Keep only last 100 lines
        const lines = this.elements.terminal.children;
        if (lines.length > 100) {
            this.elements.terminal.removeChild(lines[0]);
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        if (!this.elements.notificationArea) return;
        
        const notification = document.createElement('div');
        notification.className = `notification glassmorphism rounded-lg p-4 mb-4 notification-${type}`;
        
        const colorMap = {
            'success': 'border-green-500',
            'error': 'border-red-500',
            'warning': 'border-yellow-500',
            'info': 'border-blue-500'
        };
        
        notification.classList.add(colorMap[type] || 'border-blue-500');
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-xl hover:text-red-400">&times;</button>
            </div>
        `;
        
        this.elements.notificationArea.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Refresh all data
     */
    async refreshAllData() {
        this.addTerminalLine('Refreshing all data...', 'info');
        await Promise.all([
            this.loadStatistics(),
            this.loadConfigurations(),
            this.loadSources()
        ]);
        this.addTerminalLine('Data refresh completed', 'success');
    }

    /**
     * Start periodic updates
     */
    startPeriodicUpdates() {
        // Update statistics every 30 seconds
        this.intervals.stats = setInterval(() => this.loadStatistics(), 30000);
        
        // Check connection every 60 seconds
        this.intervals.connection = setInterval(() => this.checkConnection(), 60000);
    }

    /**
     * Stop periodic updates
     */
    stopPeriodicUpdates() {
        Object.values(this.intervals).forEach(interval => {
            clearInterval(interval);
        });
        this.intervals = {};
    }

    /**
     * Utility: Format date
     */
    formatDate(dateString) {
        if (!dateString) return 'Never';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return date.toLocaleDateString();
    }

    /**
     * Utility: Get loading HTML
     */
    getLoadingHTML() {
        return `
            <div class="text-center py-8 text-gray-400">
                <div class="spinner mx-auto mb-4"></div>
                <p>Loading...</p>
            </div>
        `;
    }

    /**
     * Utility: Get error HTML
     */
    getErrorHTML(message) {
        return `
            <div class="text-center py-8 text-red-400">
                <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Utility: Get empty HTML
     */
    getEmptyHTML(message) {
        return `
            <div class="text-center py-8 text-gray-400">
                <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m0 0V9a1 1 0 011-1h1m-1 1v4h4V9m0 0V6a1 1 0 011-1h1m3 0a1 1 0 011 1v1M9 9h4"></path>
                </svg>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Cleanup on page unload
     */
    destroy() {
        this.stopPeriodicUpdates();
    }
}

// Initialize the application when DOM is ready
let app = null;

document.addEventListener('DOMContentLoaded', function() {
    app = new StreamlineVPNApp();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (app) {
        app.destroy();
    }
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamlineVPNApp;
}
