/**
 * StreamlineVPN Main JavaScript
 * =============================
 * 
 * Enhanced JavaScript functionality for the StreamlineVPN web interface.
 */

// Global state management
const StreamlineVPN = {
    // Configuration
    config: {
        apiBase: (() => {
            const hostname = window.location.hostname;
            const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
            return isLocalhost ? `http://${hostname}:8080` : `${window.location.protocol}//${window.location.host}`;
        })(),
        updateInterval: 5000,
        maxRetries: 3,
        retryDelay: 1000
    },
    
    // State
    state: {
        configurations: [],
        sources: [],
        statistics: {},
        currentTab: 'dashboard',
        processingJobId: null,
        isProcessing: false,
        connectionStatus: 'disconnected'
    },
    
    // UI elements cache
    elements: {},
    
    // Initialize the application
    init() {
        this.cacheElements();
        this.setupEventListeners();
        this.loadInitialData();
        this.startPolling();
        console.log('StreamlineVPN initialized');
    },
    
    // Cache DOM elements for better performance
    cacheElements() {
        this.elements = {
            totalConfigs: document.getElementById('totalConfigs'),
            successfulSources: document.getElementById('successfulSources'),
            successRate: document.getElementById('successRate'),
            avgQuality: document.getElementById('avgQuality'),
            configList: document.getElementById('configList'),
            sourceList: document.getElementById('sourceList'),
            terminalOutput: document.getElementById('terminalOutput'),
            processingStatus: document.getElementById('processingStatus'),
            processingProgress: document.getElementById('processingProgress'),
            progressBar: document.getElementById('progressBar')
        };
    },
    
    // Setup event listeners
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.getAttribute('onclick')?.match(/switchTab\('([^']+)'\)/)?.[1];
                if (tabName) {
                    this.switchTab(tabName);
                }
            });
        });
        
        // Terminal input
        const terminalInput = document.getElementById('terminalInput');
        if (terminalInput) {
            terminalInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.executeCommand();
                }
            });
        }
        
        // Process button
        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.addEventListener('click', () => {
                this.startProcessing();
            });
        }
        
        // Add source button
        const addSourceBtn = document.querySelector('button[onclick="addSource()"]');
        if (addSourceBtn) {
            addSourceBtn.addEventListener('click', () => {
                this.addSource();
            });
        }
    },
    
    // Load initial data
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadStatistics(),
                this.loadConfigurations(),
                this.loadSources()
            ]);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.addTerminalLine('Failed to load initial data', 'error');
        }
    },
    
    // Start polling for updates
    startPolling() {
        setInterval(() => {
            if (this.state.currentTab === 'dashboard') {
                this.loadStatistics();
            }
        }, this.config.updateInterval);
    },
    
    // Switch tabs
    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Show selected tab
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) {
            targetTab.classList.add('active');
        }
        
        // Update button styles
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('bg-white', 'bg-opacity-20');
        });
        
        const activeBtn = document.querySelector(`.tab-btn[onclick*="switchTab('${tabName}'"]`);
        if (activeBtn) {
            activeBtn.classList.add('bg-white', 'bg-opacity-20');
        }
        
        this.state.currentTab = tabName;
        
        // Load tab-specific data
        if (tabName === 'configurations') {
            this.loadConfigurations();
        } else if (tabName === 'sources') {
            this.loadSources();
        }
    },
    
    // Load statistics
    async loadStatistics() {
        try {
            const response = await this.makeRequest('/api/v1/statistics');
            this.state.statistics = response;
            this.updateStatisticsDisplay(response);
        } catch (error) {
            console.error('Failed to load statistics:', error);
            // Try fallback endpoints
            try {
                const fallbackResponse = await this.makeRequest('/statistics');
                this.state.statistics = fallbackResponse;
                this.updateStatisticsDisplay(fallbackResponse);
            } catch (fallbackError) {
                console.warn('Fallback also failed:', fallbackError);
                this.updateStatisticsDisplay(this.getMockStatistics());
            }
        }
    },
    
    // Update statistics display
    updateStatisticsDisplay(stats) {
        if (this.elements.totalConfigs) {
            this.elements.totalConfigs.textContent = stats.total_configs || 0;
        }
        if (this.elements.successfulSources) {
            this.elements.successfulSources.textContent = stats.successful_sources || 0;
        }
        if (this.elements.successRate) {
            this.elements.successRate.textContent = `${Math.round((stats.success_rate || 0) * 100)}%`;
        }
        if (this.elements.avgQuality) {
            this.elements.avgQuality.textContent = (stats.avg_quality || 0).toFixed(2);
        }
    },
    
    // Load configurations
    async loadConfigurations() {
        try {
            const response = await this.makeRequest('/api/v1/configurations?limit=1000');
            this.state.configurations = response.configurations || [];
            this.renderConfigurations();
        } catch (error) {
            console.error('Failed to load configurations:', error);
            this.state.configurations = [];
            this.renderConfigurations();
        }
    },
    
    // Render configurations
    renderConfigurations() {
        if (!this.elements.configList) return;
        
        const configs = this.state.configurations;
        
        if (!configs || configs.length === 0) {
            this.elements.configList.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                    <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                    </svg>
                    <p class="text-lg mb-2">No configurations available</p>
                    <p class="text-sm">Start processing to load configurations</p>
                </div>
            `;
            return;
        }
        
        // Group configurations by protocol
        const groupedConfigs = configs.reduce((acc, config) => {
            const protocol = config.protocol || 'unknown';
            if (!acc[protocol]) acc[protocol] = [];
            acc[protocol].push(config);
            return acc;
        }, {});
        
        let html = '';
        
        Object.entries(groupedConfigs).forEach(([protocol, protocolConfigs]) => {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-white mb-3 flex items-center">
                        <span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                        ${protocol.toUpperCase()} (${protocolConfigs.length})
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            `;
            
            protocolConfigs.forEach(config => {
                const quality = config.quality_score || config.quality || 0;
                const qualityClass = this.getQualityClass(quality);
                const qualityPercent = Math.round(quality * 100);
                
                html += `
                    <div class="config-card glass-morphism rounded-lg p-4 hover-lift cursor-pointer" 
                         onclick="StreamlineVPN.showConfigDetails('${config.id || config.server}')">
                        <div class="flex justify-between items-start mb-3">
                            <div class="flex-1">
                                <h4 class="font-bold text-white text-sm mb-1">
                                    ${config.server || config.host || 'Unknown Server'}
                                </h4>
                                <div class="flex items-center space-x-2 text-xs text-gray-400">
                                    <span>Port: ${config.port || 'N/A'}</span>
                                    <span>•</span>
                                    <span>${config.location || 'Unknown'}</span>
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="quality-badge quality-${qualityClass} text-xs px-2 py-1 rounded">
                                    ${qualityPercent}%
                                </span>
                            </div>
                        </div>
                        
                        <div class="grid grid-cols-2 gap-2 text-xs text-gray-400">
                            <div>
                                <span class="text-gray-500">Network:</span> ${config.network || 'tcp'}
                            </div>
                            <div>
                                <span class="text-gray-500">TLS:</span> ${config.tls ? 'Yes' : 'No'}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        this.elements.configList.innerHTML = html;
    },
    
    // Load sources
    async loadSources() {
        try {
            const response = await this.makeRequest('/api/v1/sources');
            this.state.sources = response.sources || [];
            this.renderSources();
        } catch (error) {
            console.error('Failed to load sources:', error);
            this.state.sources = [];
            this.renderSources();
        }
    },
    
    // Render sources
    renderSources() {
        if (!this.elements.sourceList) return;
        
        const sources = this.state.sources;
        
        if (!sources || sources.length === 0) {
            this.elements.sourceList.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                    <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                    </svg>
                    <p class="text-lg mb-2">No sources found</p>
                    <p class="text-sm">Add a new source above to get started</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        sources.forEach(source => {
            html += `
                <div class="glass-morphism rounded-lg p-4">
                    <div class="flex justify-between items-center">
                        <div class="text-white">
                            <div class="font-semibold">${source.url}</div>
                            <div class="text-sm opacity-75">Configs: ${source.configs || 0}</div>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="status-indicator status-${source.status === 'active' ? 'running' : 'failed'}"></span>
                            <span class="text-white">${source.status}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        this.elements.sourceList.innerHTML = html;
    },
    
    // Start processing
    async startProcessing() {
        if (this.state.isProcessing) {
            this.addTerminalLine('Processing already in progress', 'warning');
            return;
        }
        
        this.state.isProcessing = true;
        this.updateProcessingUI(true);
        
        try {
            const configPath = document.getElementById('configPath')?.value || 'config/sources.yaml';
            const selectedFormats = Array.from(document.querySelectorAll('.output-format:checked'))
                .map(cb => cb.value.toLowerCase());
            
            if (selectedFormats.length === 0) {
                this.addTerminalLine('Please select at least one output format', 'warning');
                return;
            }
            
            this.addTerminalLine(`Starting processing with config: ${configPath}`, 'info');
            this.addTerminalLine(`Output formats: ${selectedFormats.join(', ')}`, 'info');
            
            const response = await this.makeRequest('/api/v1/pipeline/run', {
                method: 'POST',
                body: JSON.stringify({
                    config_path: configPath,
                    output_dir: 'output',
                    formats: selectedFormats
                })
            });
            
            if (response.status === 'success') {
                this.state.processingJobId = response.job_id;
                this.addTerminalLine(`Job started successfully! ID: ${response.job_id}`, 'success');
                this.monitorJobProgress(response.job_id);
            } else {
                throw new Error(response.message || 'Processing failed');
            }
        } catch (error) {
            console.error('Processing error:', error);
            this.addTerminalLine(`Processing failed: ${error.message}`, 'error');
            this.showNotification('Processing failed. Please check the terminal for details.', 'error');
        } finally {
            this.state.isProcessing = false;
            this.updateProcessingUI(false);
        }
    },
    
    // Monitor job progress
    async monitorJobProgress(jobId) {
        const maxAttempts = 120; // ~10 minutes
        let attempts = 0;
        
        const checkProgress = async () => {
            try {
                const response = await this.makeRequest(`/api/v1/pipeline/status/${jobId}`);
                const progress = response.progress || 0;
                const message = response.message || response.status || '';
                
                this.updateProgressDisplay(progress, message);
                
                if (response.status === 'completed') {
                    this.addTerminalLine('Processing completed successfully!', 'success');
                    this.showNotification('Processing completed!', 'success');
                    this.loadStatistics();
                    this.loadConfigurations();
                    return;
                } else if (response.status === 'failed') {
                    const errorMsg = response.error || 'Unknown error';
                    this.addTerminalLine(`Processing failed: ${errorMsg}`, 'error');
                    this.showNotification('Processing failed', 'error');
                    return;
                } else if (attempts >= maxAttempts) {
                    this.addTerminalLine('Processing timeout - job may still be running', 'warning');
                    this.showNotification('Processing timeout', 'warning');
                    return;
                }
                
                attempts++;
                setTimeout(checkProgress, 5000);
            } catch (error) {
                if (attempts % 3 === 0) {
                    this.addTerminalLine(`Progress check error: ${error.message}`, 'warning');
                }
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkProgress, 5000);
                }
            }
        };
        
        checkProgress();
    },
    
    // Update processing UI
    updateProcessingUI(isProcessing) {
        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.disabled = isProcessing;
            if (isProcessing) {
                processBtn.innerHTML = `
                    <svg class="animate-spin h-5 w-5 mr-2 inline" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                `;
            } else {
                processBtn.innerHTML = 'Start Processing';
            }
        }
        
        if (this.elements.processingStatus) {
            if (isProcessing) {
                this.elements.processingStatus.classList.remove('hidden');
            } else {
                this.elements.processingStatus.classList.add('hidden');
            }
        }
    },
    
    // Update progress display
    updateProgressDisplay(progress, message) {
        if (this.elements.processingProgress) {
            this.elements.processingProgress.textContent = `${Math.max(0, Math.min(100, progress))}%`;
        }
        if (this.elements.progressBar) {
            this.elements.progressBar.style.width = `${Math.max(0, Math.min(100, progress))}%`;
        }
        if (message) {
            this.addTerminalLine(message, 'info');
        }
    },
    
    // Add terminal line
    addTerminalLine(text, type = 'info') {
        if (!this.elements.terminalOutput) return;
        
        const line = document.createElement('div');
        line.className = `terminal-line terminal-${type}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
        this.elements.terminalOutput.appendChild(line);
        this.elements.terminalOutput.scrollTop = this.elements.terminalOutput.scrollHeight;
    },
    
    // Execute terminal command
    executeCommand() {
        const input = document.getElementById('terminalInput');
        if (!input) return;
        
        const command = input.value.trim();
        if (!command) return;
        
        this.addTerminalLine(`> ${command}`, 'info');
        
        // Process command
        const parts = command.split(' ');
        const cmd = parts[0].toLowerCase();
        
        switch (cmd) {
            case 'help':
                this.addTerminalLine('Available commands: help, status, process, clear, test', 'success');
                break;
            case 'status':
                this.loadStatistics();
                this.addTerminalLine('Statistics updated', 'success');
                break;
            case 'process':
                this.startProcessing();
                break;
            case 'clear':
                if (this.elements.terminalOutput) {
                    this.elements.terminalOutput.innerHTML = `
                        <div class="terminal-line terminal-success">StreamlineVPN Terminal v2.0</div>
                        <div class="terminal-line">Terminal cleared</div>
                    `;
                }
                break;
            case 'test':
                this.testConnection();
                break;
            default:
                this.addTerminalLine(`Unknown command: ${cmd}. Type 'help' for available commands.`, 'error');
        }
        
        input.value = '';
    },
    
    // Test connection
    async testConnection() {
        this.addTerminalLine('Testing API connection...', 'info');
        try {
            const response = await this.makeRequest('/health');
            this.addTerminalLine(`Connection successful! API Version: ${response.version || '2.0.0'}`, 'success');
            this.showNotification('API connection successful!', 'success');
        } catch (error) {
            this.addTerminalLine(`Connection failed: ${error.message}`, 'error');
            this.showNotification('API connection failed!', 'error');
        }
    },
    
    // Add source
    async addSource() {
        const input = document.getElementById('newSourceUrl');
        if (!input) return;
        
        const url = input.value.trim();
        if (!url) return;
        
        try {
            const response = await this.makeRequest('/api/v1/sources/add', {
                method: 'POST',
                body: JSON.stringify({ url })
            });
            
            this.addTerminalLine(response.message || 'Source added', 'success');
            input.value = '';
            this.loadSources();
        } catch (error) {
            this.addTerminalLine(`Add source error: ${error.message}`, 'error');
        }
    },
    
    // Show configuration details
    showConfigDetails(configId) {
        const config = this.state.configurations.find(c => c.id === configId || c.server === configId);
        if (!config) return;
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };
        
        modal.innerHTML = `
            <div class="glass-morphism rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-auto">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="text-xl font-bold text-white">Configuration Details</h2>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-white">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="text-gray-400">Protocol:</span>
                            <span class="text-white ml-2">${config.protocol}</span>
                        </div>
                        <div>
                            <span class="text-gray-400">Server:</span>
                            <span class="text-white ml-2">${config.server || config.host}</span>
                        </div>
                        <div>
                            <span class="text-gray-400">Port:</span>
                            <span class="text-white ml-2">${config.port}</span>
                        </div>
                        <div>
                            <span class="text-gray-400">Quality:</span>
                            <span class="text-white ml-2">${Math.round((config.quality_score || 0) * 100)}%</span>
                        </div>
                    </div>
                    
                    <div class="pt-4 border-t border-gray-700">
                        <h3 class="text-sm font-semibold text-gray-400 mb-2">Raw Configuration</h3>
                        <pre class="bg-black bg-opacity-50 rounded p-3 text-xs text-green-400 overflow-x-auto">
${JSON.stringify(config, null, 2)}
                        </pre>
                    </div>
                    
                    <div class="flex justify-end space-x-3 pt-4">
                        <button onclick="StreamlineVPN.copyToClipboard('${JSON.stringify(config).replace(/'/g, "\\'")}')" 
                                class="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded text-white text-sm transition">
                            Copy JSON
                        </button>
                        <button onclick="StreamlineVPN.exportConfig('${configId}')" 
                                class="px-4 py-2 bg-green-500 hover:bg-green-600 rounded text-white text-sm transition">
                            Export
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    },
    
    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard!', 'success');
        } catch (error) {
            this.showNotification('Failed to copy', 'error');
        }
    },
    
    // Export configuration
    exportConfig(configId) {
        const config = this.state.configurations.find(c => c.id === configId || c.server === configId);
        if (!config) return;
        
        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vpn-config-${config.protocol}-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showNotification('Configuration exported!', 'success');
    },
    
    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-4 rounded-lg text-white z-50 ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' :
            'bg-blue-500'
        } slide-in`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },
    
    // Get quality class
    getQualityClass(score) {
        if (score >= 0.9) return 'excellent';
        if (score >= 0.7) return 'good';
        if (score >= 0.5) return 'fair';
        return 'poor';
    },
    
    // Get mock statistics for fallback
    getMockStatistics() {
        return {
            total_configs: 1250,
            successful_sources: 15,
            success_rate: 0.92,
            avg_quality: 0.78
        };
    },
    
    // Make HTTP request with retry logic
    async makeRequest(endpoint, options = {}) {
        const url = `${this.config.apiBase}${endpoint}`;
        const requestOptions = {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            ...options
        };
        
        let lastError;
        for (let attempt = 1; attempt <= this.config.maxRetries; attempt++) {
            try {
                const response = await fetch(url, requestOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                } else {
                    return await response.text();
                }
            } catch (error) {
                lastError = error;
                if (attempt < this.config.maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, this.config.retryDelay * attempt));
                }
            }
        }
        
        throw lastError;
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    StreamlineVPN.init();
});

// Export for global access
window.StreamlineVPN = StreamlineVPN;
