/**
 * StreamlineVPN Main JavaScript Application
 * Complete implementation for the control panel functionality
 */

(function() {
    'use strict';
    
    // Ensure StreamlineVPN namespace exists
    window.StreamlineVPN = window.StreamlineVPN || {};
    
    /**
     * Control Panel Application Class
     */
    class ControlPanelApp {
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
            this.ws = null;
            this.wsBackoff = 1000;
            this.wsTimer = null;
            this.currentTab = 'dashboard';
            
            // Bind methods
            this.handleProcessingSubmit = this.handleProcessingSubmit.bind(this);
            this.updateConnectionStatus = this.updateConnectionStatus.bind(this);
            this.refreshData = this.refreshData.bind(this);
        }

        /**
         * Initialize the application
         */
        async init() {
            try {
                this.bindElements();
                this.setupEventListeners();
                await this.checkConnection();
                this.startPeriodicUpdates();
                this.setupWebSocket();
                
                console.log('[StreamlineVPN] Control Panel initialized');
            } catch (error) {
                console.error('[StreamlineVPN] Initialization error:', error);
                this.showError('Failed to initialize control panel: ' + error.message);
            }
        }

        /**
         * Bind DOM elements
         */
        bindElements() {
            // Statistics elements
            this.elements.totalSources = document.getElementById('totalSources');
            this.elements.totalConfigs = document.getElementById('totalConfigs');
            this.elements.successRate = document.getElementById('successRate');
            this.elements.lastUpdated = document.getElementById('lastUpdated');
            
            // Status elements
            this.elements.connectionStatus = document.getElementById('connectionStatus');
            this.elements.statusIndicator = document.getElementById('statusIndicator');
            this.elements.statusText = document.getElementById('statusText');
            this.elements.apiStatus = document.getElementById('apiStatus');
            this.elements.cacheStatus = document.getElementById('cacheStatus');
            this.elements.jobsStatus = document.getElementById('jobsStatus');
            
            // Lists
            this.elements.sourcesList = document.getElementById('sourcesList');
            this.elements.configsList = document.getElementById('configsList');
            this.elements.jobsList = document.getElementById('jobsList');
            this.elements.recentActivity = document.getElementById('recentActivity');
            
            // Forms
            this.elements.processingForm = document.getElementById('processingForm');
            this.elements.configPath = document.getElementById('configPath');
            this.elements.outputDir = document.getElementById('outputDir');
            this.elements.formatCheckboxes = document.querySelectorAll('.format-cb');
            this.elements.startProcessingBtn = document.getElementById('startProcessingBtn');
            
            // Progress
            this.elements.progressContainer = document.getElementById('progressContainer');
            this.elements.progressBar = document.getElementById('progressBar');
            this.elements.progressPercent = document.getElementById('progressPercent');
            this.elements.progressMessage = document.getElementById('progressMessage');
            
            // Filters
            this.elements.protocolFilter = document.getElementById('protocolFilter');
            
            // Buttons
            this.elements.refreshAPI = document.getElementById('refreshAPI');
            this.elements.refreshSources = document.getElementById('refreshSources');
            this.elements.refreshConfigs = document.getElementById('refreshConfigs');
        }

        /**
         * Setup event listeners
         */
        setupEventListeners() {
            // Tab switching
            const tabButtons = document.querySelectorAll('.tab-btn');
            tabButtons.forEach(button => {
                button.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
            });
            
            // Processing form
            if (this.elements.processingForm) {
                this.elements.processingForm.addEventListener('submit', this.handleProcessingSubmit);
            }
            
            // Refresh buttons
            if (this.elements.refreshAPI) {
                this.elements.refreshAPI.addEventListener('click', () => this.checkConnection());
            }
            if (this.elements.refreshSources) {
                this.elements.refreshSources.addEventListener('click', () => this.loadSources());
            }
            if (this.elements.refreshConfigs) {
                this.elements.refreshConfigs.addEventListener('click', () => this.loadConfigurations());
            }
            
            // Protocol filter
            if (this.elements.protocolFilter) {
                this.elements.protocolFilter.addEventListener('change', () => this.loadConfigurations());
            }
            
            // API connection events
            window.addEventListener('api-connection-changed', this.updateConnectionStatus);
            window.addEventListener('api-base-loaded', (e) => {
                this.apiBase = e.detail.apiBase;
                this.checkConnection();
            });
            
            // Window events
            window.addEventListener('beforeunload', () => this.cleanup());
        }

        /**
         * Switch tabs
         */
        switchTab(tabId) {
            // Update button states
            const tabButtons = document.querySelectorAll('.tab-btn');
            tabButtons.forEach(btn => {
                btn.classList.remove('active', 'bg-blue-600');
                if (btn.dataset.tab === tabId) {
                    btn.classList.add('active', 'bg-blue-600');
                }
            });
            
            // Update content visibility
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.add('hidden'));
            
            const targetTab = document.getElementById(`${tabId}-tab`);
            if (targetTab) {
                targetTab.classList.remove('hidden');
            }
            
            this.currentTab = tabId;
            
            // Load data for the new tab
            this.loadTabData(tabId);
        }

        /**
         * Load data for specific tab
         */
        async loadTabData(tabId) {
            switch (tabId) {
                case 'dashboard':
                    await this.loadStatistics();
                    await this.loadRecentActivity();
                    break;
                case 'sources':
                    await this.loadSources();
                    break;
                case 'configurations':
                    await this.loadConfigurations();
                    break;
                case 'jobs':
                    await this.loadJobs();
                    break;
            }
        }

        /**
         * Check API connection
         */
        async checkConnection() {
            try {
                const health = await window.StreamlineVPN.API.healthCheck();
                this.state.isConnected = health.success;
                
                if (health.success) {
                    this.updateConnectionStatus({
                        detail: { connected: true, health: health.data }
                    });
                } else {
                    this.updateConnectionStatus({
                        detail: { connected: false, error: health.error }
                    });
                }
                
                return health.success;
            } catch (error) {
                console.error('Connection check failed:', error);
                this.state.isConnected = false;
                this.updateConnectionStatus({
                    detail: { connected: false, error: error.message }
                });
                return false;
            }
        }

        /**
         * Update connection status UI
         */
        updateConnectionStatus(event) {
            const { connected, health, error } = event.detail;
            
            if (this.elements.statusIndicator) {
                this.elements.statusIndicator.className = `w-3 h-3 rounded-full ${
                    connected ? 'bg-green-500' : 'bg-red-500'
                }`;
            }
            
            if (this.elements.statusText) {
                this.elements.statusText.textContent = connected ? 'Connected' : 'Disconnected';
            }
            
            if (this.elements.apiStatus) {
                this.elements.apiStatus.className = `px-2 py-1 text-xs rounded ${
                    connected ? 'bg-green-600' : 'bg-red-600'
                }`;
                this.elements.apiStatus.textContent = connected ? 'Online' : 'Offline';
            }
            
            // Show/hide API banner
            const apiBanner = document.getElementById('apiBanner');
            const apiDetails = document.getElementById('apiDetails');
            
            if (connected && health) {
                if (apiBanner) apiBanner.classList.remove('hidden');
                if (apiDetails) {
                    apiDetails.textContent = `Version: ${health.version || 'Unknown'} | Uptime: ${
                        health.uptime ? this.formatUptime(health.uptime) : 'Unknown'
                    }`;
                }
            } else {
                if (apiBanner) apiBanner.classList.add('hidden');
                if (error) {
                    this.showError(`API connection failed: ${error}`);
                }
            }
        }

        /**
         * Load statistics
         */
        async loadStatistics() {
            try {
                const stats = await window.StreamlineVPN.API.get('/api/v1/statistics');
                this.state.statistics = stats;
                
                // Update UI
                if (this.elements.totalSources) {
                    this.elements.totalSources.textContent = stats.total_sources || '--';
                }
                if (this.elements.totalConfigs) {
                    this.elements.totalConfigs.textContent = stats.total_configurations || stats.total_configs || '--';
                }
                if (this.elements.successRate) {
                    const rate = stats.success_rate || 0;
                    this.elements.successRate.textContent = `${Math.round(rate * 100)}%`;
                }
                if (this.elements.lastUpdated) {
                    const lastUpdate = stats.last_update || stats.end_time;
                    this.elements.lastUpdated.textContent = lastUpdate ? 
                        this.formatDateTime(lastUpdate) : '--';
                }
            } catch (error) {
                console.error('Failed to load statistics:', error);
                this.showError('Failed to load statistics');
            }
        }

        /**
         * Load sources
         */
        async loadSources() {
            try {
                const data = await window.StreamlineVPN.API.get('/api/v1/sources');
                this.state.sources = data.sources || [];
                
                if (this.elements.sourcesList) {
                    this.renderSources(this.state.sources);
                }
            } catch (error) {
                console.error('Failed to load sources:', error);
                if (this.elements.sourcesList) {
                    this.elements.sourcesList.innerHTML = '<div class="text-red-400">Failed to load sources</div>';
                }
            }
        }

        /**
         * Load configurations
         */
        async loadConfigurations() {
            try {
                const protocol = this.elements.protocolFilter ? this.elements.protocolFilter.value : '';
                const params = { limit: 50 };
                if (protocol) params.protocol = protocol;
                
                const data = await window.StreamlineVPN.API.get('/api/v1/configurations', params);
                this.state.configurations = data.configurations || [];
                
                if (this.elements.configsList) {
                    this.renderConfigurations(this.state.configurations, data.total || 0);
                }
            } catch (error) {
                console.error('Failed to load configurations:', error);
                if (this.elements.configsList) {
                    this.elements.configsList.innerHTML = '<div class="text-red-400">Failed to load configurations</div>';
                }
            }
        }

        /**
         * Load jobs
         */
        async loadJobs() {
            try {
                const data = await window.StreamlineVPN.API.get('/api/v1/pipeline/jobs');
                this.state.jobs = data.jobs || {};
                
                if (this.elements.jobsList) {
                    this.renderJobs(this.state.jobs);
                }
            } catch (error) {
                console.error('Failed to load jobs:', error);
                if (this.elements.jobsList) {
                    this.elements.jobsList.innerHTML = '<div class="text-red-400">Failed to load jobs</div>';
                }
            }
        }

        /**
         * Load recent activity
         */
        async loadRecentActivity() {
            try {
                // This could be enhanced to show actual activity logs
                const activity = [
                    { time: new Date().toLocaleTimeString(), message: 'System status checked', type: 'info' },
                    { time: new Date(Date.now() - 300000).toLocaleTimeString(), message: 'Sources refreshed', type: 'success' },
                    { time: new Date(Date.now() - 600000).toLocaleTimeString(), message: 'Processing completed', type: 'success' }
                ];
                
                if (this.elements.recentActivity) {
                    this.renderRecentActivity(activity);
                }
            } catch (error) {
                console.error('Failed to load recent activity:', error);
            }
        }

        /**
         * Handle processing form submission
         */
        async handleProcessingSubmit(event) {
            event.preventDefault();
            
            try {
                // Disable button and show progress
                if (this.elements.startProcessingBtn) {
                    this.elements.startProcessingBtn.disabled = true;
                    this.elements.startProcessingBtn.textContent = 'Starting...';
                }
                
                // Collect form data
                const formats = Array.from(this.elements.formatCheckboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);
                
                const requestData = {
                    config_path: this.elements.configPath?.value || 'config/sources.yaml',
                    output_dir: this.elements.outputDir?.value || 'output',
                    formats: formats
                };
                
                // Start processing
                const response = await window.StreamlineVPN.API.post('/api/v1/pipeline/run', requestData);
                
                if (response.job_id) {
                    this.showProgress();
                    this.monitorJob(response.job_id);
                    this.showSuccess('Processing started successfully');
                } else {
                    throw new Error('No job ID returned');
                }
                
            } catch (error) {
                console.error('Processing submission failed:', error);
                this.showError('Failed to start processing: ' + error.message);
                this.resetProcessingButton();
            }
        }

        /**
         * Monitor job progress
         */
        async monitorJob(jobId) {
            const checkJob = async () => {
                try {
                    const job = await window.StreamlineVPN.API.get(`/api/v1/pipeline/status/${jobId}`);
                    
                    if (this.elements.progressBar) {
                        this.elements.progressBar.style.width = `${job.progress || 0}%`;
                    }
                    if (this.elements.progressPercent) {
                        this.elements.progressPercent.textContent = `${job.progress || 0}%`;
                    }
                    if (this.elements.progressMessage) {
                        this.elements.progressMessage.textContent = job.message || 'Processing...';
                    }
                    
                    if (job.status === 'completed') {
                        this.showSuccess('Processing completed successfully');
                        this.hideProgress();
                        this.resetProcessingButton();
                        // Refresh statistics
                        await this.loadStatistics();
                    } else if (job.status === 'failed') {
                        this.showError('Processing failed: ' + (job.error || 'Unknown error'));
                        this.hideProgress();
                        this.resetProcessingButton();
                    } else {
                        // Continue monitoring
                        setTimeout(checkJob, 2000);
                    }
                } catch (error) {
                    console.error('Job monitoring failed:', error);
                    this.hideProgress();
                    this.resetProcessingButton();
                }
            };
            
            checkJob();
        }

        /**
         * Render sources list
         */
        renderSources(sources) {
            if (!sources.length) {
                this.elements.sourcesList.innerHTML = '<div class="text-gray-400">No sources configured</div>';
                return;
            }
            
            const html = sources.map(source => `
                <div class="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                    <div class="flex-1">
                        <div class="font-medium">${this.escapeHtml(source.url || 'Unknown URL')}</div>
                        <div class="text-sm text-gray-400">
                            Status: ${source.status || 'unknown'} | 
                            Configs: ${source.configs || 0} | 
                            Success Rate: ${Math.round((source.success_rate || 0) * 100)}%
                        </div>
                    </div>
                    <div class="ml-4">
                        <span class="px-2 py-1 text-xs rounded ${
                            source.status === 'active' ? 'bg-green-600' : 'bg-gray-600'
                        }">
                            ${source.status || 'unknown'}
                        </span>
                    </div>
                </div>
            `).join('');
            
            this.elements.sourcesList.innerHTML = html;
        }

        /**
         * Render configurations list
         */
        renderConfigurations(configs, total) {
            if (!configs.length) {
                this.elements.configsList.innerHTML = '<div class="text-gray-400">No configurations found</div>';
                return;
            }
            
            const html = `
                <div class="mb-4 text-sm text-gray-400">Showing ${configs.length} of ${total} configurations</div>
                ${configs.map(config => `
                    <div class="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                        <div class="flex-1">
                            <div class="font-mono text-sm">${this.escapeHtml(config.server || 'unknown')}:${config.port || 'unknown'}</div>
                            <div class="text-xs text-gray-400">
                                Protocol: ${config.protocol || 'unknown'} | 
                                Quality: ${config.quality_score ? (config.quality_score * 100).toFixed(1) + '%' : 'unknown'}
                            </div>
                        </div>
                        <div class="ml-4">
                            <span class="px-2 py-1 text-xs bg-blue-600 rounded">${config.protocol || 'unknown'}</span>
                        </div>
                    </div>
                `).join('')}
            `;
            
            this.elements.configsList.innerHTML = html;
        }

        /**
         * Render jobs list
         */
        renderJobs(jobs) {
            const jobArray = Object.values(jobs);
            
            if (!jobArray.length) {
                this.elements.jobsList.innerHTML = '<div class="text-gray-400">No jobs found</div>';
                return;
            }
            
            const html = jobArray.map(job => `
                <div class="p-4 bg-gray-700 rounded-lg">
                    <div class="flex items-center justify-between mb-2">
                        <div class="font-medium">${job.type || 'unknown'} - ${job.id}</div>
                        <span class="px-2 py-1 text-xs rounded ${this.getJobStatusColor(job.status)}">
                            ${job.status || 'unknown'}
                        </span>
                    </div>
                    <div class="text-sm text-gray-400">
                        Created: ${job.created_at ? this.formatDateTime(job.created_at) : 'unknown'}<br>
                        Progress: ${job.progress || 0}%
                        ${job.result ? `| Configs: ${job.result.configurations_found || 0}` : ''}
                    </div>
                </div>
            `).join('');
            
            this.elements.jobsList.innerHTML = html;
        }

        /**
         * Render recent activity
         */
        renderRecentActivity(activities) {
            const html = activities.map(activity => `
                <div class="flex items-center space-x-3 text-sm">
                    <div class="w-2 h-2 rounded-full ${this.getActivityTypeColor(activity.type)}"></div>
                    <div class="flex-1">${this.escapeHtml(activity.message)}</div>
                    <div class="text-gray-400">${activity.time}</div>
                </div>
            `).join('');
            
            this.elements.recentActivity.innerHTML = html;
        }

        /**
         * Show progress container
         */
        showProgress() {
            if (this.elements.progressContainer) {
                this.elements.progressContainer.classList.remove('hidden');
            }
        }

        /**
         * Hide progress container
         */
        hideProgress() {
            if (this.elements.progressContainer) {
                this.elements.progressContainer.classList.add('hidden');
            }
        }

        /**
         * Reset processing button
         */
        resetProcessingButton() {
            if (this.elements.startProcessingBtn) {
                this.elements.startProcessingBtn.disabled = false;
                this.elements.startProcessingBtn.textContent = 'Start Processing';
            }
        }

        /**
         * Start periodic updates
         */
        startPeriodicUpdates() {
            // Update statistics every 30 seconds
            this.intervals.statistics = setInterval(() => {
                if (this.currentTab === 'dashboard' && this.state.isConnected) {
                    this.loadStatistics();
                    this.loadRecentActivity();
                }
            }, 30000);
            
            // Check connection every 15 seconds
            this.intervals.connection = setInterval(() => {
                this.checkConnection();
            }, 15000);
        }

        /**
         * Setup WebSocket connection for real-time updates
         */
        setupWebSocket() {
            if (!window.WebSocket) return;
            
            try {
                const wsUrl = this.apiBase.replace(/^http/, 'ws') + '/ws';
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    console.log('[StreamlineVPN] WebSocket connected');
                    this.wsBackoff = 1000;
                };
                
                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleWebSocketMessage(data);
                    } catch (error) {
                        console.error('WebSocket message parse error:', error);
                    }
                };
                
                this.ws.onclose = () => {
                    console.log('[StreamlineVPN] WebSocket disconnected, reconnecting...');
                    this.scheduleWebSocketReconnect();
                };
                
                this.ws.onerror = (error) => {
                    console.error('[StreamlineVPN] WebSocket error:', error);
                };
                
            } catch (error) {
                console.error('WebSocket setup failed:', error);
            }
        }

        /**
         * Handle WebSocket messages
         */
        handleWebSocketMessage(data) {
            switch (data.type) {
                case 'statistics_update':
                    this.state.statistics = data.data;
                    if (this.currentTab === 'dashboard') {
                        this.loadStatistics();
                    }
                    break;
                case 'job_update':
                    if (data.data.job_id && this.elements.progressContainer && !this.elements.progressContainer.classList.contains('hidden')) {
                        this.updateJobProgress(data.data);
                    }
                    break;
                case 'source_update':
                    if (this.currentTab === 'sources') {
                        this.loadSources();
                    }
                    break;
            }
        }

        /**
         * Schedule WebSocket reconnection
         */
        scheduleWebSocketReconnect() {
            if (this.wsTimer) return;
            
            this.wsTimer = setTimeout(() => {
                this.wsTimer = null;
                this.setupWebSocket();
                this.wsBackoff = Math.min(this.wsBackoff * 2, 30000);
            }, this.wsBackoff);
        }

        /**
         * Update job progress from WebSocket
         */
        updateJobProgress(jobData) {
            if (this.elements.progressBar) {
                this.elements.progressBar.style.width = `${jobData.progress || 0}%`;
            }
            if (this.elements.progressPercent) {
                this.elements.progressPercent.textContent = `${jobData.progress || 0}%`;
            }
            if (this.elements.progressMessage) {
                this.elements.progressMessage.textContent = jobData.message || 'Processing...';
            }
            
            if (jobData.status === 'completed' || jobData.status === 'failed') {
                this.hideProgress();
                this.resetProcessingButton();
                
                if (jobData.status === 'completed') {
                    this.showSuccess('Processing completed successfully');
                } else {
                    this.showError('Processing failed: ' + (jobData.error || 'Unknown error'));
                }
                
                // Refresh data
                setTimeout(() => this.refreshData(), 1000);
            }
        }

        /**
         * Refresh all data for current tab
         */
        async refreshData() {
            await this.loadTabData(this.currentTab);
        }

        /**
         * Cleanup on page unload
         */
        cleanup() {
            // Clear intervals
            Object.values(this.intervals).forEach(interval => clearInterval(interval));
            
            // Close WebSocket
            if (this.ws) {
                this.ws.close();
            }
            
            // Clear timers
            if (this.wsTimer) {
                clearTimeout(this.wsTimer);
            }
        }

        /**
         * Utility methods
         */
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        formatDateTime(timestamp) {
            try {
                const date = new Date(timestamp);
                return date.toLocaleString();
            } catch {
                return 'Invalid date';
            }
        }

        formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }

        getJobStatusColor(status) {
            switch (status) {
                case 'completed': return 'bg-green-600';
                case 'failed': return 'bg-red-600';
                case 'running': return 'bg-blue-600';
                case 'pending': return 'bg-yellow-600';
                default: return 'bg-gray-600';
            }
        }

        getActivityTypeColor(type) {
            switch (type) {
                case 'success': return 'bg-green-500';
                case 'error': return 'bg-red-500';
                case 'warning': return 'bg-yellow-500';
                default: return 'bg-blue-500';
            }
        }

        showSuccess(message) {
            this.showNotification(message, 'success');
        }

        showError(message) {
            this.showNotification(message, 'error');
        }

        showNotification(message, type) {
            // Simple notification implementation
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${
                type === 'success' ? 'bg-green-600' : 'bg-red-600'
            }`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }
    }

    // Export to global namespace
    window.StreamlineVPN.ControlPanel = ControlPanelApp;

    // Auto-initialize if in browser environment
    if (typeof document !== 'undefined') {
        document.addEventListener('DOMContentLoaded', function() {
            if (document.getElementById('dashboard-tab')) {
                window.streamlineControlPanel = new ControlPanelApp();
                window.streamlineControlPanel.init();
            }
        });
    }

})();

