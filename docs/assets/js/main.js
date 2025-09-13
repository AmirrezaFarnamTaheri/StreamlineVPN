/**
 * StreamlineVPN Frontend Main JavaScript - FIXED
 * ===============================================
 *
 * Improved error handling, consistent API communication, and better UX.
 */

class StreamlineVPNDashboard {
    constructor() {
        this.apiBase = this.getApiBase();
        this.state = {
            configurations: [],
            sources: [],
            statistics: {},
            loading: false,
            error: null
        };
        
        this.elements = {};
        this.retryAttempts = 3;
        this.retryDelay = 1000;
        
        this.init();
    }

    /**
     * Get API base URL with proper fallbacks
     */
    getApiBase() {
        // Check for dynamically injected API base
        if (window.__API_BASE__) {
            return window.__API_BASE__;
        }

        // Check for environment variable or use default
        return 'http://localhost:8080';
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        this.bindElements();
        this.setupEventListeners();
        await this.loadInitialData();
        
        // Set up periodic refresh
        setInterval(() => {
            if (!this.state.loading) {
                this.refreshData();
            }
        }, 30000); // Refresh every 30 seconds
    }

    /**
     * Bind DOM elements
     */
    bindElements() {
        this.elements = {
            configList: document.getElementById('config-list'),
            sourceList: document.getElementById('source-list'),
            statisticsPanel: document.getElementById('statistics-panel'),
            refreshButton: document.getElementById('refresh-button'),
            processButton: document.getElementById('process-button'),
            errorAlert: document.getElementById('error-alert'),
            loadingIndicator: document.getElementById('loading-indicator')
        };
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        if (this.elements.refreshButton) {
            this.elements.refreshButton.addEventListener('click', () => {
                this.refreshData();
            });
        }

        if (this.elements.processButton) {
            this.elements.processButton.addEventListener('click', () => {
                this.runPipeline();
            });
        }

        // Setup export buttons
        document.querySelectorAll('[data-export]').forEach(button => {
            button.addEventListener('click', (e) => {
                const format = e.target.dataset.export;
                this.exportConfigurations(format);
            });
        });
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        this.setLoading(true);
        
        try {
            await Promise.all([
                this.loadConfigurations(),
                this.loadSources(),
                this.loadStatistics()
            ]);
            
            this.clearError();
        } catch (error) {
            this.showError('Failed to load initial data', error);
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Refresh all data
     */
    async refreshData() {
        try {
            await this.loadInitialData();
        } catch (error) {
            console.error('Failed to refresh data:', error);
        }
    }

    /**
     * Make API request with retry logic
     */
    async makeRequest(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                const response = await fetch(url, {
                    ...options,
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                return data;

            } catch (error) {
                console.warn(`API request attempt ${attempt} failed:`, error);

                if (attempt === this.retryAttempts) {
                    throw new Error(`Failed after ${this.retryAttempts} attempts: ${error.message}`);
                }

                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
            }
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
            throw error;
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
        configs.forEach((config, index) => {
            const protocol = config.protocol || 'unknown';
            const server = config.server || 'unknown';
            const port = config.port || 'N/A';
            const quality = this.calculateQualityScore(config);

            html += `
                <div class="config-item dark-glass rounded-lg p-4 mb-2 hover:bg-opacity-20 transition-all duration-200">
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="flex items-center space-x-3">
                                <span class="protocol-badge badge-${protocol}">${protocol.toUpperCase()}</span>
                                <div class="font-medium text-white">${server}:${port}</div>
                            </div>
                            ${config.name ? `<div class="text-xs text-gray-400 mt-1">${config.name}</div>` : ''}
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-medium ${quality >= 70 ? 'text-green-400' : quality >= 40 ? 'text-yellow-400' : 'text-red-400'}">${quality}%</div>
                            <div class="text-xs text-gray-400">Quality</div>
                        </div>
                        <div class="ml-4">
                            <button class="copy-btn text-blue-400 hover:text-blue-300" onclick="copyToClipboard('${this.escapeHtml(config.url || '')}')">
                                Copy
                            </button>
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
            throw error;
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
            const status = source.status || 'unknown';
            const configs = source.configs || 0;
            const latency = source.avg_response_time || 0;

            html += `
                <div class="config-item dark-glass rounded-lg p-4 mb-2">
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="font-medium text-white truncate">${this.escapeHtml(source.url)}</div>
                            <div class="text-sm text-gray-400 mt-1">
                                Configs: ${configs} |
                                Success: ${successRate}% |
                                Latency: ${latency}ms
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="status-indicator status-${status === 'active' ? 'success' : 'error'}"></span>
                            <span class="text-xs text-gray-400">${status}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        this.elements.sourceList.innerHTML = html;
    }

    /**
     * Load statistics
     */
    async loadStatistics() {
        if (!this.elements.statisticsPanel) return;
        
        try {
            const response = await this.makeRequest('/api/v1/statistics');
            this.state.statistics = response || {};
            this.renderStatistics();
            
        } catch (error) {
            console.error('Failed to load statistics:', error);
            throw error;
        }
    }

    /**
     * Render statistics
     */
    renderStatistics() {
        if (!this.elements.statisticsPanel) return;
        
        const stats = this.state.statistics;
        const totalConfigs = stats.total_configs || 0;
        const successRate = Math.round((stats.success_rate || 0) * 100);
        const totalSources = stats.total_sources || 0;
        
        this.elements.statisticsPanel.innerHTML = `
            <div class="grid grid-cols-3 gap-4">
                <div class="stat-card">
                    <div class="stat-value">${totalConfigs}</div>
                    <div class="stat-label">Configurations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${successRate}%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${totalSources}</div>
                    <div class="stat-label">Sources</div>
                </div>
            </div>
        `;
    }

    /**
     * Run pipeline
     */
    async runPipeline() {
        if (this.state.loading) return;
        
        this.setLoading(true);
        
        try {
            const response = await this.makeRequest('/api/v1/pipeline/run', {
                method: 'POST',
                body: JSON.stringify({
                    config_path: 'config/sources.yaml',
                    output_dir: 'output',
                    formats: ['json', 'clash']
                })
            });
            
            this.showSuccess(`Pipeline started successfully. Job ID: ${response.job_id}`);

            // Refresh data after a delay
            setTimeout(() => {
                this.refreshData();
            }, 2000);

        } catch (error) {
            this.showError('Failed to start pipeline', error);
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Export configurations
     */
    async exportConfigurations(format) {
        try {
            const response = await this.makeRequest(`/api/export/${format}`);

            if (format === 'download') {
                // Trigger download
                const blob = new Blob([JSON.stringify(response, null, 2)], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `streamline_vpn_configs_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                this.showSuccess('Configurations exported successfully');
            } else {
                console.log('Export response:', response);
            }

        } catch (error) {
            this.showError('Failed to export configurations', error);
        }
    }

    /**
     * Calculate quality score for a configuration
     */
    calculateQualityScore(config) {
        let score = 50; // Base score
        
        // Protocol bonus
        const protocolBonus = {
            'vless': 25,
            'vmess': 20,
            'trojan': 20,
            'shadowsocks': 15,
            'shadowsocksr': 10
        };
        score += protocolBonus[config.protocol] || 0;
        
        // Other factors
        if (config.tls) score += 10;
        if (config.port && config.port !== 80 && config.port !== 8080) score += 5;
        if (config.network === 'ws') score += 5;
        
        return Math.min(100, Math.max(0, score));
    }

    /**
     * Utility methods
     */
    setLoading(loading) {
        this.state.loading = loading;
        
        if (this.elements.loadingIndicator) {
            this.elements.loadingIndicator.style.display = loading ? 'block' : 'none';
        }

        // Disable buttons during loading
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.disabled = loading;
        });
    }

    showError(message, error = null) {
        console.error(message, error);

        if (this.elements.errorAlert) {
            this.elements.errorAlert.innerHTML = `
                <div class="alert alert-error">
                    <div class="font-medium">${message}</div>
                    ${error ? `<div class="text-sm mt-1">${error.message}</div>` : ''}
                </div>
            `;
            this.elements.errorAlert.style.display = 'block';
        }
    }

    showSuccess(message) {
        if (this.elements.errorAlert) {
            this.elements.errorAlert.innerHTML = `
                <div class="alert alert-success">
                    <div class="font-medium">${message}</div>
                </div>
            `;
            this.elements.errorAlert.style.display = 'block';

            // Auto-hide success messages
            setTimeout(() => {
                this.clearError();
            }, 5000);
        }
    }

    clearError() {
        if (this.elements.errorAlert) {
            this.elements.errorAlert.style.display = 'none';
        }
    }

    getLoadingHTML() {
        return `
            <div class="flex items-center justify-center p-8">
                <div class="loading-spinner"></div>
                <span class="ml-3 text-gray-400">Loading...</span>
            </div>
        `;
    }

    getErrorHTML(message) {
        return `
            <div class="flex items-center justify-center p-8 text-red-400">
                <div class="text-center">
                    <div class="mb-2">⚠️</div>
                    <div>${message}</div>
                </div>
            </div>
        `;
    }

    getEmptyHTML(message) {
        return `
            <div class="flex items-center justify-center p-8 text-gray-400">
                <div class="text-center">
                    <div class="mb-2">📭</div>
                    <div>${message}</div>
                </div>
            </div>
        `;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

/**
 * Global utility functions
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy:', err);
            showToast('Failed to copy to clipboard', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('Copied to clipboard!');
        } catch (err) {
            console.error('Failed to copy:', err);
            showToast('Failed to copy to clipboard', 'error');
        }
        document.body.removeChild(textArea);
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);

    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

/**
 * Initialize dashboard when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    window.streamlineVPN = new StreamlineVPNDashboard();
});

/**
 * Export for module systems
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamlineVPNDashboard;
}
