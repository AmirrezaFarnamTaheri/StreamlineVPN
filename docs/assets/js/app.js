/**
 * StreamlineVPN Main Application
 * ==============================
 *
 * Core JavaScript application for StreamlineVPN web interface.
 * Handles real-time updates, API interactions, and user interface management.
 */

// Global application state
window.StreamlineVPNApp = {
    // Application state
    state: {
        connected: false,
        websocket: null,
        statistics: {},
        sources: [],
        jobs: [],
        logs: [],
        settings: {
            autoRefresh: true,
            refreshInterval: 30000,
            logLevel: 'info',
            theme: 'dark'
        }
    },

    // Initialize the application
    async init() {
        console.log('🚀 Initializing StreamlineVPN Application...');

        try {
            // Check API connectivity
            await this.checkApiConnectivity();

            // Load initial data
            await this.loadInitialData();

            // Setup WebSocket connection
            await this.setupWebSocket();

            // Setup event listeners
            this.setupEventListeners();

            // Setup periodic updates
            this.setupPeriodicUpdates();

            // Initialize UI components
            this.initializeUI();

            console.log('✅ StreamlineVPN Application initialized successfully');
            this.updateConnectionStatus('connected', 'Connected to API');

        } catch (error) {
            console.error('❌ Failed to initialize application:', error);
            this.updateConnectionStatus('error', 'Failed to connect to API');
            this.showNotification('Failed to initialize application', 'error');
        }
    },

    // Check if API is accessible
    async checkApiConnectivity() {
        try {
            const response = await API.get('/health');
            console.log('API Health Check:', response);
            return response;
        } catch (error) {
            console.error('API connectivity check failed:', error);
            throw new Error('API is not accessible');
        }
    },

    // Load initial application data
    async loadInitialData() {
        console.log('📊 Loading initial application data...');

        const dataLoaders = [
            this.loadStatistics(),
            this.loadSources(),
            this.loadRecentJobs(),
            this.loadSystemLogs()
        ];

        // Load data with timeout and error handling
        const results = await Promise.allSettled(dataLoaders.map(loader =>
            this.withTimeout(loader, 10000)
        ));

        results.forEach((result, index) => {
            const loaderNames = ['statistics', 'sources', 'jobs', 'logs'];
            if (result.status === 'rejected') {
                console.warn(`Failed to load ${loaderNames[index]}:`, result.reason);
            }
        });
    },

    // Setup WebSocket connection for real-time updates
    async setupWebSocket() {
        if (!window.APIWebSocket) {
            console.warn('WebSocket API not available, skipping real-time updates');
            return;
        }

        try {
            this.state.websocket = await APIWebSocket.connect('/ws', {
                onMessage: this.handleWebSocketMessage.bind(this),
                onError: (error) => {
                    console.error('WebSocket error:', error);
                    this.updateConnectionStatus('warning', 'Real-time updates unavailable');
                },
                onClose: () => {
                    console.log('WebSocket connection closed');
                    this.state.connected = false;
                    this.updateConnectionStatus('warning', 'Real-time updates disconnected');
                }
            });

            console.log('🔗 WebSocket connected for real-time updates');

        } catch (error) {
            console.warn('WebSocket connection failed, falling back to polling:', error);
            this.setupPollingFallback();
        }
    },

    // Handle incoming WebSocket messages
    handleWebSocketMessage(data) {
        console.log('📨 WebSocket message received:', data);

        switch (data.type) {
            case 'statistics_update':
                this.handleStatisticsUpdate(data.payload);
                break;
            case 'job_update':
                this.handleJobUpdate(data.payload);
                break;
            case 'source_update':
                this.handleSourceUpdate(data.payload);
                break;
            case 'log_entry':
                this.handleLogEntry(data.payload);
                break;
            case 'system_alert':
                this.handleSystemAlert(data.payload);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    },

    // Setup event listeners for user interactions
    setupEventListeners() {
        console.log('🎯 Setting up event listeners...');

        // Global click handler for action buttons
        document.addEventListener('click', this.handleGlobalClick.bind(this));

        // Form submission handlers
        document.addEventListener('submit', this.handleFormSubmit.bind(this));

        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));

        // Page visibility change (pause/resume updates when tab is not active)
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));

        // Browser online/offline status
        window.addEventListener('online', () => {
            console.log('Browser came online');
            this.handleConnectivityChange(true);
        });

        window.addEventListener('offline', () => {
            console.log('Browser went offline');
            this.handleConnectivityChange(false);
        });
    },

    // Handle global click events (event delegation)
    async handleGlobalClick(event) {
        const target = event.target.closest('[data-action]');
        if (!target) return;

        const action = target.dataset.action;
        const loading = target.classList.contains('loading');

        if (loading) return; // Prevent double-clicks during loading

        try {
            this.setButtonLoading(target, true);
            await this.executeAction(action, target);
        } catch (error) {
            console.error(`Action ${action} failed:`, error);
            this.showNotification(`Failed to execute ${action}`, 'error');
        } finally {
            this.setButtonLoading(target, false);
        }
    },

    // Execute specific actions
    async executeAction(action, element) {
        console.log(`🔧 Executing action: ${action}`);

        switch (action) {
            case 'process':
                return await this.processAllConfigurations();
            case 'export':
                return await this.exportConfigurations();
            case 'clear-cache':
                return await this.clearCache();
            case 'validate':
                return await this.validateConfiguration();
            case 'refresh':
                return await this.refreshAllData();
            case 'add-source':
                return this.showAddSourceModal();
            case 'edit-source':
                return this.editSource(element.dataset.sourceId);
            case 'delete-source':
                return this.deleteSource(element.dataset.sourceId);
            case 'toggle-source':
                return this.toggleSource(element.dataset.sourceId);
            default:
                console.warn(`Unknown action: ${action}`);
        }
    },

    // Load and display statistics
    async loadStatistics() {
        try {
            const stats = await API.get('/api/v1/statistics');
            this.state.statistics = stats;
            this.updateStatisticsDisplay(stats);
            return stats;
        } catch (error) {
            console.error('Failed to load statistics:', error);
            this.showErrorPlaceholder('statistics-section');
            throw error;
        }
    },

    // Update statistics display
    updateStatisticsDisplay(stats) {
        const elements = {
            'total-sources': stats.total_sources || 0,
            'total-configs': stats.total_configurations || stats.total_configs || 0,
            'success-rate': `${Math.round((stats.success_rate || 0) * 100)}%`,
            'cache-hit-rate': `${Math.round((stats.cache_hit_rate || 0) * 100)}%`,
            'last-updated': this.formatTimestamp(stats.last_updated),
            'avg-response-time': stats.average_response_time ? `${stats.average_response_time}ms` : '-'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                element.classList.add('animate-fade-in-up');
            }
        });

        // Update progress bars
        this.updateProgressBars(stats);
    },

    // Update progress bars with animation
    updateProgressBars(stats) {
        const progressBars = [
            { id: 'sources-progress', value: Math.min(((stats.total_sources || 0) / 100) * 100, 100) },
            { id: 'configs-progress', value: Math.min(((stats.total_configurations || 0) / 1000) * 100, 100) },
            { id: 'success-progress', value: (stats.success_rate || 0) * 100 },
            { id: 'cache-progress', value: (stats.cache_hit_rate || 0) * 100 }
        ];

        progressBars.forEach(({ id, value }) => {
            const element = document.getElementById(id);
            if (element) {
                // Animate progress bar
                element.style.width = '0%';
                setTimeout(() => {
                    element.style.width = `${value}%`;
                }, 100);
            }
        });
    },

    // Load sources data
    async loadSources() {
        try {
            const sources = await API.get('/api/v1/sources');
            this.state.sources = Array.isArray(sources) ? sources : sources.sources || [];
            this.updateSourcesDisplay(this.state.sources);
            return this.state.sources;
        } catch (error) {
            console.error('Failed to load sources:', error);
            this.showErrorPlaceholder('sources-list');
            throw error;
        }
    },

    // Update sources display
    updateSourcesDisplay(sources) {
        const container = document.getElementById('sources-list');
        if (!container) return;

        // Clear loading placeholder
        container.innerHTML = '';

        if (!sources || sources.length === 0) {
            container.innerHTML = `
                <div class="card text-center py-8">
                    <div class="text-4xl mb-4 opacity-50">📡</div>
                    <h3 class="text-lg font-semibold mb-2">No Sources Configured</h3>
                    <p class="text-muted mb-4">Add your first VPN source to get started.</p>
                    <button class="btn btn-primary" data-action="add-source">Add Source</button>
                </div>
            `;
            return;
        }

        sources.forEach(source => {
            const sourceCard = this.createSourceCard(source);
            container.appendChild(sourceCard);
        });
    },

    // Create individual source card
    createSourceCard(source) {
        const card = document.createElement('div');
        card.className = 'card hover-lift';
        card.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center mb-2">
                        <div class="status-indicator ${source.status === 'active' ? 'status-online' : 'status-offline'} mr-2"></div>
                        <h3 class="font-semibold">${source.name || 'Unnamed Source'}</h3>
                        <span class="quality-badge ${this.getQualityBadgeClass(source.quality)} ml-2">${source.quality || 'Unknown'}</span>
                    </div>
                    <p class="text-sm text-muted mb-2">${source.url}</p>
                    <div class="flex items-center space-x-4 text-xs text-secondary">
                        <span>Tier: ${source.tier || 'N/A'}</span>
                        <span>Weight: ${source.weight || 'N/A'}</span>
                        <span>Configs: ${source.config_count || 0}</span>
                        <span>Last Check: ${this.formatTimestamp(source.last_check)}</span>
                    </div>
                </div>
                <div class="flex items-center space-x-2 ml-4">
                    <button class="btn btn-outline btn-sm" data-action="toggle-source" data-source-id="${source.id}" title="${source.enabled ? 'Disable' : 'Enable'} Source">
                        ${source.enabled ?
                            '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>' :
                            '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/><path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/></svg>'
                        }
                    </button>
                    <button class="btn btn-outline btn-sm" data-action="edit-source" data-source-id="${source.id}" title="Edit Source">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                    </button>
                    <button class="btn btn-danger btn-sm" data-action="delete-source" data-source-id="${source.id}" title="Delete Source">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        return card;
    },

    // Load recent jobs
    async loadRecentJobs() {
        try {
            const jobs = await API.get('/api/v1/jobs/recent');
            this.state.jobs = Array.isArray(jobs) ? jobs : jobs.jobs || [];
            this.updateJobsDisplay(this.state.jobs);
            return this.state.jobs;
        } catch (error) {
            console.error('Failed to load recent jobs:', error);
            this.showErrorPlaceholder('jobs-list');
            throw error;
        }
    },

    // Update jobs display
    updateJobsDisplay(jobs) {
        const container = document.getElementById('jobs-list');
        if (!container) return;

        container.innerHTML = '';

        if (!jobs || jobs.length === 0) {
            container.innerHTML = `
                <div class="card text-center py-6">
                    <div class="text-2xl mb-2 opacity-50">📋</div>
                    <p class="text-muted">No recent jobs</p>
                </div>
            `;
            return;
        }

        jobs.slice(0, 10).forEach(job => { // Show only last 10 jobs
            const jobCard = this.createJobCard(job);
            container.appendChild(jobCard);
        });
    },

    // Create individual job card
    createJobCard(job) {
        const card = document.createElement('div');
        card.className = 'card';
        
        const statusIcon = this.getJobStatusIcon(job.status);
        const statusClass = this.getJobStatusClass(job.status);

        card.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <div class="${statusIcon} mr-3"></div>
                    <div>
                        <h4 class="font-semibold">${job.type || 'Unknown Job'}</h4>
                        <p class="text-sm text-muted">${job.description || 'No description'}</p>
                    </div>
                </div>
                <div class="text-right">
                    <span class="inline-block px-2 py-1 rounded text-xs font-medium ${statusClass}">
                        ${job.status || 'Unknown'}
                    </span>
                    <div class="text-xs text-muted mt-1">
                        ${this.formatTimestamp(job.created_at)}
                    </div>
                    ${job.progress !== undefined ? `
                        <div class="mt-2">
                            <div class="progress-bar h-2">
                                <div class="progress-fill bar-blue" style="width: ${job.progress}%"></div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        return card;
    },

    // Load system logs
    async loadSystemLogs() {
        try {
            const logs = await API.get('/api/v1/logs/recent');
            this.state.logs = Array.isArray(logs) ? logs : logs.logs || [];
            this.updateLogsDisplay(this.state.logs);
            return this.state.logs;
        } catch (error) {
            console.error('Failed to load system logs:', error);
            throw error;
        }
    },

    // Update logs display
    updateLogsDisplay(logs) {
        const container = document.getElementById('logs-content');
        if (!container) return;

        container.innerHTML = '';

        if (!logs || logs.length === 0) {
            container.innerHTML = '<div class="text-muted">No logs available</div>';
            return;
        }

        logs.slice(0, 100).forEach(log => { // Show only last 100 logs
            const logEntry = this.createLogEntry(log);
            container.appendChild(logEntry);
        });

        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
    },

    // Create individual log entry
    createLogEntry(log) {
        const entry = document.createElement('div');
        entry.className = `mb-1 ${this.getLogLevelClass(log.level)}`;
        
        const timestamp = this.formatTimestamp(log.timestamp, true);
        entry.innerHTML = `
            <span class="text-gray-500">[${timestamp}]</span>
            <span class="font-medium">[${log.level.toUpperCase()}]</span>
            <span>${log.message}</span>
        `;

        return entry;
    },

    // Process all configurations
    async processAllConfigurations() {
        console.log('🔄 Starting configuration processing...');
        
        try {
            // Show processing modal
            this.showProcessingModal();

            const response = await API.post('/api/v1/pipeline/run', {
                output_dir: 'output',
                formats: ['json', 'clash', 'singbox'],
                force_refresh: true
            });

            if (response.success) {
                this.showNotification('Configuration processing completed successfully', 'success');
                await this.refreshAllData(); // Refresh all data after processing
            } else {
                throw new Error(response.message || 'Processing failed');
            }

            return response;

        } catch (error) {
            console.error('Processing failed:', error);
            throw error;
        } finally {
            this.hideProcessingModal();
        }
    },

    // Export configurations
    async exportConfigurations() {
        try {
            const formats = await this.showExportModal();
            if (!formats) return; // User cancelled

            this.showNotification('Preparing export...', 'info');

            for (const format of formats) {
                try {
                    await API.download(`/api/v1/export/configurations.${format}`, `streamline-configs.${format}`);
                } catch (error) {
                    console.error(`Failed to export ${format}:`, error);
                    this.showNotification(`Failed to export ${format} format`, 'error');
                }
            }

            this.showNotification('Export completed', 'success');

        } catch (error) {
            console.error('Export failed:', error);
            throw error;
        }
    },

    // Clear all caches
    async clearCache() {
        try {
            const confirmed = await this.showConfirmDialog(
                'Clear Cache',
                'Are you sure you want to clear all cached data? This will temporarily slow down the next processing cycle.',
                'Clear Cache',
                'danger'
            );

            if (!confirmed) return;

            await API.post('/api/v1/cache/clear');
            this.showNotification('Cache cleared successfully', 'success');
            
            // Refresh statistics to show updated cache status
            await this.loadStatistics();

        } catch (error) {
            console.error('Failed to clear cache:', error);
            throw error;
        }
    },

    // Validate configuration
    async validateConfiguration() {
        try {
            this.showNotification('Validating configuration...', 'info');
            
            const response = await API.post('/api/v1/validate');
            
            if (response.valid) {
                this.showNotification(`Configuration is valid. Found ${response.total_configs} configurations from ${response.total_sources} sources.`, 'success');
            } else {
                this.showNotification(`Configuration validation failed: ${response.errors.join(', ')}`, 'warning');
            }

            return response;

        } catch (error) {
            console.error('Validation failed:', error);
            throw error;
        }
    },

    // Refresh all application data
    async refreshAllData() {
        try {
            this.showNotification('Refreshing data...', 'info');
            await this.loadInitialData();
            this.showNotification('Data refreshed successfully', 'success');
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showNotification('Failed to refresh some data', 'warning');
        }
    },

    // Setup periodic updates
    setupPeriodicUpdates() {
        if (this.state.settings.autoRefresh) {
            this.periodicUpdateInterval = setInterval(() => {
                if (!document.hidden && this.state.connected) {
                    this.loadStatistics().catch(console.error);
                }
            }, this.state.settings.refreshInterval);
        }
    },

    // Start real-time updates
    startRealTimeUpdates() {
        console.log('🔄 Starting real-time updates...');
        this.setupPeriodicUpdates();
    },

    // Stop real-time updates
    stopRealTimeUpdates() {
        if (this.periodicUpdateInterval) {
            clearInterval(this.periodicUpdateInterval);
            this.periodicUpdateInterval = null;
        }
    },

    // Handle connectivity changes
    handleConnectivityChange(isOnline) {
        if (isOnline) {
            this.updateConnectionStatus('connected', 'Back online');
            this.startRealTimeUpdates();
        } else {
            this.updateConnectionStatus('error', 'Connection lost');
            this.stopRealTimeUpdates();
        }
    },

    // Update connection status indicator
    updateConnectionStatus(status, message) {
        const indicator = document.getElementById('connection-status');
        if (!indicator) return;

        const statusIndicator = indicator.querySelector('.status-indicator');
        const statusText = indicator.querySelector('span');

        if (statusIndicator) {
            statusIndicator.className = `status-indicator status-${status === 'connected' ? 'online' : status === 'error' ? 'offline' : 'warning'}`;
        }

        if (statusText) {
            statusText.textContent = message || status;
        }

        this.state.connected = status === 'connected';
    },

    // Utility function to add timeout to promises
    withTimeout(promise, timeoutMs) {
        return Promise.race([
            promise,
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Operation timed out')), timeoutMs)
            )
        ]);
    },

    // Format timestamp for display
    formatTimestamp(timestamp, includeSeconds = false) {
        if (!timestamp) return '-';

        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;

            const options = {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            };

            if (includeSeconds) {
                options.hour = '2-digit';
                options.minute = '2-digit';
                options.second = '2-digit';
            }

            return date.toLocaleDateString('en-US', options);
        } catch (error) {
            return 'Invalid date';
        }
    },

    // Get quality badge CSS class
    getQualityBadgeClass(quality) {
        switch (quality?.toLowerCase()) {
            case 'excellent': return 'quality-excellent';
            case 'good': return 'quality-good';
            case 'fair': return 'quality-fair';
            case 'poor': return 'quality-poor';
            default: return 'quality-fair';
        }
    },

    // Get job status icon
    getJobStatusIcon(status) {
        switch (status?.toLowerCase()) {
            case 'completed': return 'status-indicator status-online';
            case 'running': case 'processing': return 'status-indicator status-loading';
            case 'failed': case 'error': return 'status-indicator status-offline';
            case 'cancelled': return 'status-indicator status-warning';
            default: return 'status-indicator status-warning';
        }
    },

    // Get job status CSS class
    getJobStatusClass(status) {
        switch (status?.toLowerCase()) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'running': case 'processing': return 'bg-blue-100 text-blue-800';
            case 'failed': case 'error': return 'bg-red-100 text-red-800';
            case 'cancelled': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    },

    // Get log level CSS class
    getLogLevelClass(level) {
        switch (level?.toLowerCase()) {
            case 'error': return 'text-red-400';
            case 'warning': case 'warn': return 'text-yellow-400';
            case 'info': return 'text-blue-400';
            case 'debug': return 'text-gray-400';
            default: return 'text-gray-300';
        }
    },

    // Set button loading state
    setButtonLoading(button, loading) {
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
            const originalText = button.textContent;
            button.dataset.originalText = originalText;
            button.innerHTML = '<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mx-auto"></div>';
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
                delete button.dataset.originalText;
            }
        }
    },

    // Show notification (enhanced toast system)
    showNotification(message, type = 'info', duration = 5000) {
        if (typeof showToast === 'function') {
            showToast(message, type, duration);
        } else {
            // Fallback console notification
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    },

    // Show error placeholder
    showErrorPlaceholder(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="card text-center py-8 border-red-500 border-opacity-50">
                <div class="text-4xl mb-4 opacity-50">⚠️</div>
                <h3 class="text-lg font-semibold mb-2 text-red-400">Failed to Load Data</h3>
                <p class="text-muted mb-4">There was an error loading this section.</p>
                <button class="btn btn-outline" data-action="refresh">Try Again</button>
            </div>
        `;
    },

    // Initialize UI components
    initializeUI() {
        // Initialize any UI components that need setup
        this.initializeTabs();
        this.initializeModals();
        this.initializeFilters();
    },

    // Initialize tabs
    initializeTabs() {
        const tabs = document.querySelectorAll('[data-tab]');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
    },

    // Switch to specific tab
    switchTab(tabName) {
        // Hide all tab contents
        document.querySelectorAll('[data-tab-content]').forEach(content => {
            content.style.display = 'none';
        });

        // Show selected tab content
        const selectedContent = document.querySelector(`[data-tab-content="${tabName}"]`);
        if (selectedContent) {
            selectedContent.style.display = 'block';
        }

        // Update tab active states
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    },

    // Initialize modals
    initializeModals() {
        // Modal close handlers
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeModal(e.target);
            }
        });

        // ESC key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal-overlay:not(.hidden)');
                if (openModal) {
                    this.closeModal(openModal);
                }
            }
        });
    },

    // Close modal
    closeModal(modal) {
        modal.classList.add('hidden');
    },

    // Initialize filters
    initializeFilters() {
        const filters = document.querySelectorAll('[data-filter]');
        filters.forEach(filter => {
            filter.addEventListener('change', (e) => {
                const filterType = e.target.dataset.filter;
                const filterValue = e.target.value;
                this.applyFilter(filterType, filterValue);
            });
        });
    },

    // Apply filter to data
    applyFilter(type, value) {
        switch (type) {
            case 'source':
                this.filterSources(value);
                break;
            case 'log-level':
                this.filterLogs(value);
                break;
            default:
                console.warn(`Unknown filter type: ${type}`);
        }
    },

    // Filter sources display
    filterSources(tier) {
        const sourceCards = document.querySelectorAll('#sources-list .card');

        sourceCards.forEach(card => {
            if (tier === 'all') {
                card.style.display = 'block';
            } else {
                // This is a simplified filter - in a real app, you'd check the source tier
                card.style.display = 'block';
            }
        });
    },

    // Filter logs display
    filterLogs(level) {
        const logEntries = document.querySelectorAll('#logs-content > div');

        logEntries.forEach(entry => {
            if (level === 'all') {
                entry.style.display = 'block';
            } else {
                const entryLevel = entry.textContent.toLowerCase();
                entry.style.display = entryLevel.includes(level) ? 'block' : 'none';
            }
        });
    }
};

// Auto-initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        StreamlineVPNApp.init().catch(console.error);
    });
} else {
    // DOM is already loaded
    StreamlineVPNApp.init().catch(console.error);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamlineVPNApp;
}

console.log('📱 StreamlineVPN Main Application loaded');
