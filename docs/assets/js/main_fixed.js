/**
 * StreamlineVPN Frontend - Fixed and Enhanced
 * Complete integration with backend API
 */

class StreamlineVPNApp {
    constructor() {
        // Configuration
        this.apiBase = window.__API_BASE__ || 'http://localhost:8080';
        this.wsUrl = this.apiBase.replace('http', 'ws') + '/ws';
        
        // State management
        this.state = {
            connected: false,
            statistics: {},
            configurations: [],
            sources: [],
            jobs: {},
            loading: false,
            error: null
        };
        
        // WebSocket connection
        this.ws = null;
        
        // UI elements cache
        this.elements = {};
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing StreamlineVPN App...');
        
        // Cache DOM elements
        this.cacheElements();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check backend health
        await this.checkHealth();
        
        // Load initial data
        await this.loadInitialData();
        
        // Setup WebSocket connection
        this.setupWebSocket();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        console.log('Initialization complete');
    }
    
    /**
     * Cache DOM elements for performance
     */
    cacheElements() {
        this.elements = {
            // Status elements
            statusIndicator: document.getElementById('status-indicator'),
            statusText: document.getElementById('status-text'),
            
            // Statistics
            totalSources: document.getElementById('total-sources'),
            activeSources: document.getElementById('active-sources'),
            totalConfigs: document.getElementById('total-configs'),
            successRate: document.getElementById('success-rate'),
            lastUpdate: document.getElementById('last-update'),
            
            // Configuration list
            configList: document.getElementById('config-list'),
            configCount: document.getElementById('config-count'),
            
            // Source list
            sourceList: document.getElementById('source-list'),
            sourceCount: document.getElementById('source-count'),
            
            // Control buttons
            runPipelineBtn: document.getElementById('run-pipeline-btn'),
            refreshBtn: document.getElementById('refresh-btn'),
            exportBtn: document.getElementById('export-btn'),
            
            // Forms
            addSourceForm: document.getElementById('add-source-form'),
            sourceUrlInput: document.getElementById('source-url-input'),
            
            // Processing
            processingStatus: document.getElementById('processing-status'),
            processingProgress: document.getElementById('processing-progress'),
            
            // Notifications
            notificationContainer: document.getElementById('notification-container'),
            
            // Loading overlay
            loadingOverlay: document.getElementById('loading-overlay')
        };
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Run pipeline button
        if (this.elements.runPipelineBtn) {
            this.elements.runPipelineBtn.addEventListener('click', () => this.runPipeline());
        }
        
        // Refresh button
        if (this.elements.refreshBtn) {
            this.elements.refreshBtn.addEventListener('click', () => this.refresh());
        }
        
        // Export button
        if (this.elements.exportBtn) {
            this.elements.exportBtn.addEventListener('click', () => this.exportConfigurations());
        }
        
        // Add source form
        if (this.elements.addSourceForm) {
            this.elements.addSourceForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addSource();
            });
        }
        
        // Format checkboxes
        document.querySelectorAll('.format-checkbox').forEach(cb => {
            cb.addEventListener('change', () => this.updateSelectedFormats());
        });
        
        // Search functionality
        const searchInput = document.getElementById('config-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filterConfigurations(e.target.value));
        }
    }
    
    /**
     * Check backend health
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            const data = await response.json();
            
            this.state.connected = data.status === 'healthy';
            this.updateConnectionStatus(this.state.connected);
            
            return data;
        } catch (error) {
            console.error('Health check failed:', error);
            this.state.connected = false;
            this.updateConnectionStatus(false);
            this.showError('Failed to connect to backend API');
            return null;
        }
    }
    
    /**
     * Load initial data
     */
    async loadInitialData() {
        this.showLoading(true);
        
        try {
            // Load in parallel for better performance
            const [stats, configs, sources] = await Promise.all([
                this.loadStatistics(),
                this.loadConfigurations(),
                this.loadSources()
            ]);
            
            this.state.statistics = stats || {};
            this.state.configurations = configs || [];
            this.state.sources = sources || [];
            
            // Update UI
            this.updateStatisticsDisplay();
            this.updateConfigurationsDisplay();
            this.updateSourcesDisplay();
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load data from server');
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Setup WebSocket connection for real-time updates
     */
    setupWebSocket() {
        if (!this.wsUrl) return;
        
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.showNotification('Connected to real-time updates', 'success');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                // Reconnect after 5 seconds
                setTimeout(() => this.setupWebSocket(), 5000);
            };
            
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }
    
    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'statistics':
                this.state.statistics = message.data;
                this.updateStatisticsDisplay();
                break;
                
            case 'job_update':
                this.updateJobStatus(message.data);
                break;
                
            case 'configuration_update':
                this.handleConfigurationUpdate(message.data);
                break;
                
            default:
                console.log('Unknown WebSocket message type:', message.type);
        }
    }
    
    /**
     * Start periodic updates
     */
    startPeriodicUpdates() {
        // Update statistics every 30 seconds
        setInterval(() => this.loadStatistics(), 30000);
        
        // Check health every minute
        setInterval(() => this.checkHealth(), 60000);
    }
    
    /**
     * Load statistics from API
     */
    async loadStatistics() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/statistics`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.state.statistics = data;
            this.updateStatisticsDisplay();
            
            return data;
        } catch (error) {
            console.error('Failed to load statistics:', error);
            return null;
        }
    }
    
    /**
     * Load configurations from API
     */
    async loadConfigurations(limit = 100, offset = 0) {
        try {
            const response = await fetch(
                `${this.apiBase}/api/v1/configurations?limit=${limit}&offset=${offset}`
            );
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.state.configurations = data.configurations || [];
            this.updateConfigurationsDisplay();
            
            return data.configurations;
        } catch (error) {
            console.error('Failed to load configurations:', error);
            return [];
        }
    }
    
    /**
     * Load sources from API
     */
    async loadSources() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/sources`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.state.sources = data.sources || [];
            this.updateSourcesDisplay();
            
            return data.sources;
        } catch (error) {
            console.error('Failed to load sources:', error);
            return [];
        }
    }
    
    /**
     * Run the pipeline
     */
    async runPipeline() {
        const formats = this.getSelectedFormats();
        
        if (formats.length === 0) {
            this.showError('Please select at least one output format');
            return;
        }
        
        this.showLoading(true);
        this.updateProcessingStatus('Starting pipeline...', 0);
        
        try {
            const response = await fetch(`${this.apiBase}/api/v1/pipeline/run`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    output_dir: 'output',
                    formats: formats
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.showNotification(`Pipeline started: ${data.job_id}`, 'success');
            
            // Monitor job progress
            this.monitorJob(data.job_id);
            
        } catch (error) {
            console.error('Failed to run pipeline:', error);
            this.showError(`Failed to run pipeline: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Monitor job progress
     */
    async monitorJob(jobId) {
        const checkInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBase}/api/v1/pipeline/status/${jobId}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const job = await response.json();
                this.updateJobStatus(job);
                
                if (job.status === 'completed' || job.status === 'failed') {
                    clearInterval(checkInterval);
                    
                    if (job.status === 'completed') {
                        this.showNotification('Pipeline completed successfully!', 'success');
                        await this.refresh();
                    } else {
                        this.showError(`Pipeline failed: ${job.error || 'Unknown error'}`);
                    }
                    
                    this.updateProcessingStatus('', 0);
                }
            } catch (error) {
                console.error('Failed to check job status:', error);
                clearInterval(checkInterval);
            }
        }, 2000);
    }
    
    /**
     * Add a new source
     */
    async addSource() {
        const url = this.elements.sourceUrlInput?.value?.trim();
        
        if (!url) {
            this.showError('Please enter a valid URL');
            return;
        }
        
        this.showLoading(true);
        
        try {
            const response = await fetch(`${this.apiBase}/api/v1/sources`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.showNotification('Source added successfully!', 'success');
            
            // Clear input and reload sources
            if (this.elements.sourceUrlInput) {
                this.elements.sourceUrlInput.value = '';
            }
            await this.loadSources();
            
        } catch (error) {
            console.error('Failed to add source:', error);
            this.showError(`Failed to add source: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Export configurations
     */
    async exportConfigurations() {
        const format = document.getElementById('export-format')?.value || 'json';
        
        try {
            const response = await fetch(
                `${this.apiBase}/api/v1/configurations?limit=10000`
            );
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            const configurations = data.configurations || [];
            
            // Create download
            const blob = new Blob([JSON.stringify(configurations, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `vpn-configs-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('Configurations exported successfully!', 'success');
            
        } catch (error) {
            console.error('Failed to export configurations:', error);
            this.showError('Failed to export configurations');
        }
    }
    
    /**
     * Refresh all data
     */
    async refresh() {
        await this.loadInitialData();
        this.showNotification('Data refreshed', 'info');
    }
    
    /**
     * Get selected output formats
     */
    getSelectedFormats() {
        const formats = [];
        document.querySelectorAll('.format-checkbox:checked').forEach(cb => {
            formats.push(cb.value);
        });
        return formats;
    }
    
    /**
     * Filter configurations
     */
    filterConfigurations(searchTerm) {
        const filtered = this.state.configurations.filter(config => {
            const searchLower = searchTerm.toLowerCase();
            return (
                config.server?.toLowerCase().includes(searchLower) ||
                config.protocol?.toLowerCase().includes(searchLower) ||
                config.country?.toLowerCase().includes(searchLower)
            );
        });
        
        this.updateConfigurationsDisplay(filtered);
    }
    
    // ===== UI Update Methods =====
    
    /**
     * Update connection status display
     */
    updateConnectionStatus(connected) {
        if (this.elements.statusIndicator) {
            this.elements.statusIndicator.className = connected ? 'status-online' : 'status-offline';
        }
        
        if (this.elements.statusText) {
            this.elements.statusText.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }
    
    /**
     * Update statistics display
     */
    updateStatisticsDisplay() {
        const stats = this.state.statistics;
        
        if (this.elements.totalSources) {
            this.elements.totalSources.textContent = stats.total_sources || 0;
        }
        
        if (this.elements.activeSources) {
            this.elements.activeSources.textContent = stats.active_sources || 0;
        }
        
        if (this.elements.totalConfigs) {
            this.elements.totalConfigs.textContent = stats.total_configs || 0;
        }
        
        if (this.elements.successRate) {
            const rate = (stats.success_rate || 0) * 100;
            this.elements.successRate.textContent = `${rate.toFixed(1)}%`;
        }
        
        if (this.elements.lastUpdate) {
            const date = new Date(stats.last_update || Date.now());
            this.elements.lastUpdate.textContent = date.toLocaleString();
        }
    }
    
    /**
     * Update configurations display
     */
    updateConfigurationsDisplay(configs = null) {
        const configurations = configs || this.state.configurations;
        
        if (this.elements.configCount) {
            this.elements.configCount.textContent = configurations.length;
        }
        
        if (this.elements.configList) {
            if (configurations.length === 0) {
                this.elements.configList.innerHTML = `
                    <div class="empty-state">
                        <p>No configurations available</p>
                        <button onclick="app.runPipeline()" class="btn btn-primary">
                            Run Pipeline
                        </button>
                    </div>
                `;
                return;
            }
            
            const html = configurations.slice(0, 100).map(config => `
                <div class="config-item">
                    <div class="config-header">
                        <span class="protocol-badge ${config.protocol}">${config.protocol}</span>
                        <span class="server">${config.server}:${config.port}</span>
                    </div>
                    <div class="config-details">
                        ${config.country ? `<span class="country">📍 ${config.country}</span>` : ''}
                        ${config.security ? `<span class="security">🔒 ${config.security}</span>` : ''}
                    </div>
                </div>
            `).join('');
            
            this.elements.configList.innerHTML = html;
        }
    }
    
    /**
     * Update sources display
     */
    updateSourcesDisplay() {
        const sources = this.state.sources;
        
        if (this.elements.sourceCount) {
            this.elements.sourceCount.textContent = sources.length;
        }
        
        if (this.elements.sourceList) {
            if (sources.length === 0) {
                this.elements.sourceList.innerHTML = `
                    <div class="empty-state">
                        <p>No sources configured</p>
                    </div>
                `;
                return;
            }
            
            const html = sources.map(source => `
                <div class="source-item">
                    <div class="source-url">${source.url}</div>
                    <div class="source-status">
                        <span class="status-badge ${source.status}">${source.status}</span>
                        <span class="config-count">${source.configs} configs</span>
                    </div>
                </div>
            `).join('');
            
            this.elements.sourceList.innerHTML = html;
        }
    }
    
    /**
     * Update job status
     */
    updateJobStatus(job) {
        this.state.jobs[job.id] = job;
        
        if (job.status === 'running') {
            this.updateProcessingStatus(
                `Processing: ${job.type}`,
                job.progress || 0
            );
        }
    }
    
    /**
     * Update processing status
     */
    updateProcessingStatus(message, progress) {
        if (this.elements.processingStatus) {
            this.elements.processingStatus.textContent = message;
            this.elements.processingStatus.style.display = message ? 'block' : 'none';
        }
        
        if (this.elements.processingProgress) {
            this.elements.processingProgress.style.width = `${progress}%`;
            this.elements.processingProgress.textContent = `${progress}%`;
        }
    }
    
    // ===== Utility Methods =====
    
    /**
     * Show loading overlay
     */
    showLoading(show) {
        this.state.loading = show;
        
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        if (this.elements.notificationContainer) {
            this.elements.notificationContainer.appendChild(notification);
        } else {
            document.body.appendChild(notification);
        }
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
    
    /**
     * Show error message
     */
    showError(message) {
        this.state.error = message;
        this.showNotification(message, 'error');
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new StreamlineVPNApp();
});
