/**
 * StreamlineVPN App.js
 * Legacy compatibility layer and additional functionality
 */

// API Configuration
const API_BASE = (() => {
    // Prefer value injected by the static server if present
    const injected = window.__API_BASE__;
    if (typeof injected === 'string' && injected.startsWith('http')) return injected;
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return `http://${hostname}:8080`;
    }
    return `${window.location.protocol}//${window.location.host}`;
})();

console.log('API Base:', API_BASE);

// Global state
let chart = null;
let currentTab = 'dashboard';
let jobPollingInterval = null;
let currentJobId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    initChart();
    loadStatistics();
    setupTabHandling();
    setupPeriodicUpdates();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('[StreamlineVPN] Initializing app.js compatibility layer');
    
    // Test API connectivity
    testApiConnection();
    
    // Setup global error handling
    window.addEventListener('error', (event) => {
        console.error('[StreamlineVPN] Global error:', event.error);
        showNotification('An error occurred. Check console for details.', 'error');
    });
    
    window.addEventListener('unhandledrejection', (event) => {
        console.error('[StreamlineVPN] Unhandled promise rejection:', event.reason);
        showNotification('A network error occurred. Please try again.', 'error');
    });
}

/**
 * Test API connection
 */
async function testApiConnection() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            console.log('[StreamlineVPN] API connection successful');
            updateConnectionIndicator(true);
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.warn('[StreamlineVPN] API connection failed:', error.message);
        updateConnectionIndicator(false);
    }
}

/**
 * Update connection indicator
 */
function updateConnectionIndicator(isConnected) {
    const indicators = document.querySelectorAll('[data-connection-status]');
    indicators.forEach(indicator => {
        indicator.setAttribute('data-connection-status', isConnected ? 'connected' : 'disconnected');
        const statusText = indicator.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
        }
    });
}

/**
 * Initialize Chart.js if canvas exists
 */
function initChart() {
    const ctx = document.getElementById('statisticsChart');
    if (!ctx) return;
    
    try {
        // Only initialize if Chart.js is available
        if (typeof Chart !== 'undefined') {
            chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Active Sources', 'Inactive Sources', 'Pending'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: [
                            '#10b981', // green
                            '#ef4444', // red
                            '#f59e0b'  // yellow
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#f8fafc',
                                usePointStyle: true,
                                padding: 20
                            }
                        }
                    },
                    animation: {
                        animateRotate: true,
                        duration: 1000
                    }
                }
            });
        } else {
            console.warn('[StreamlineVPN] Chart.js not available, skipping chart initialization');
        }
    } catch (error) {
        console.error('[StreamlineVPN] Failed to initialize chart:', error);
    }
}

/**
 * Setup tab handling
 */
function setupTabHandling() {
    const tablist = document.getElementById('tablist');
    if (!tablist) return;
    
    const tabContents = document.querySelectorAll('.tab-content');
    const tabs = tablist.querySelectorAll('.tab-btn');

    function switchTab(targetTab) {
        // Update tab contents
        tabContents.forEach(content => {
            const isTarget = content.id === `${targetTab}-tab`;
            content.classList.toggle('active', isTarget);
            content.toggleAttribute('hidden', !isTarget);
        });

        // Update tab buttons
        tabs.forEach(tab => {
            const isTarget = tab.dataset.tab === targetTab;
            tab.setAttribute('aria-selected', isTarget);
            tab.setAttribute('tabindex', isTarget ? '0' : '-1');
            
            // Update visual state
            if (isTarget) {
                tab.classList.add('text-white', 'border-indigo-400');
                tab.classList.remove('text-gray-400');
            } else {
                tab.classList.add('text-gray-400');
                tab.classList.remove('text-white', 'border-indigo-400');
            }
        });

        currentTab = targetTab;
        
        // Load data for specific tabs
        if (targetTab === 'configs') loadConfigurations();
        if (targetTab === 'sources') loadSources();
        if (targetTab === 'logs') loadRecentLogs();
    }

    // Tab click handlers
    tablist.addEventListener('click', (e) => {
        const tabButton = e.target.closest('.tab-btn');
        if (tabButton) {
            switchTab(tabButton.dataset.tab);
        }
    });

    // Keyboard navigation
    tablist.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
            e.preventDefault();
            const currentTabIndex = Array.from(tabs).indexOf(e.target);
            const nextTabIndex = e.key === 'ArrowRight'
                ? (currentTabIndex + 1) % tabs.length
                : (currentTabIndex - 1 + tabs.length) % tabs.length;
            
            tabs[nextTabIndex].focus();
            switchTab(tabs[nextTabIndex].dataset.tab);
        }
    });
}

/**
 * Setup periodic updates
 */
function setupPeriodicUpdates() {
    // Update statistics every 30 seconds
    setInterval(loadStatistics, 30000);
    
    // Update source status every 60 seconds
    setInterval(() => {
        if (currentTab === 'sources') {
            loadSources();
        }
    }, 60000);
}

/**
 * Load statistics
 */
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/statistics`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const stats = await response.json();
        updateStatisticsDisplay(stats);
        updateChart(stats);
        
    } catch (error) {
        console.error('Failed to load statistics:', error);
        showNotification('Failed to load statistics', 'error');
    }
}

/**
 * Update statistics display
 */
function updateStatisticsDisplay(stats) {
    const updates = {
        'totalSources': stats.total_sources || 0,
        'totalConfigs': stats.total_configurations || 0,
        'activeSources': stats.active_sources || 0,
        'validConfigs': stats.valid_configurations || 0
    };
    
    Object.entries(updates).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            // Animate number change
            animateNumber(element, parseInt(element.textContent) || 0, value);
        }
    });
    
    // Update last updated timestamp
    const lastUpdated = document.getElementById('lastUpdated');
    if (lastUpdated) {
        lastUpdated.textContent = formatRelativeTime(stats.last_updated);
    }
}

/**
 * Animate number changes
 */
function animateNumber(element, from, to) {
    const duration = 1000;
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.round(from + (to - from) * progress);
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

/**
 * Update chart with new data
 */
function updateChart(stats) {
    if (!chart) return;
    
    const active = stats.active_sources || 0;
    const total = stats.total_sources || 0;
    const inactive = total - active;
    const pending = stats.pending_sources || 0;
    
    chart.data.datasets[0].data = [active, inactive, pending];
    chart.update('none'); // No animation for updates
}

/**
 * Load configurations
 */
async function loadConfigurations() {
    const configsList = document.getElementById('configsList');
    if (!configsList) return;
    
    try {
        configsList.innerHTML = getLoadingSpinner();
        
        const response = await fetch(`${API_BASE}/api/v1/configurations?limit=20`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        const configs = data.configurations || [];
        
        if (configs.length === 0) {
            configsList.innerHTML = '<div class="text-gray-400 text-center py-8">No configurations available</div>';
            return;
        }
        
        const items = configs.map(config => `
            <div class="glass rounded-lg p-4 mb-3 hover:bg-white/10 transition-colors cursor-pointer"
                 onclick="showConfigDetails('${config.id || config.server}')">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="font-semibold text-white">${config.protocol.toUpperCase()}</div>
                        <div class="text-sm text-gray-300">${config.server}:${config.port}</div>
                        ${config.name ? `<div class="text-xs text-gray-400">${config.name}</div>` : ''}
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-medium ${getQualityColor(config.quality_score)}">
                            ${Math.round((config.quality_score || 0) * 100)}%
                        </div>
                        <div class="text-xs text-gray-400">Quality</div>
                    </div>
                </div>
                <div class="mt-2 text-xs text-gray-400">
                    Encryption: ${config.encryption || 'auto'} | 
                    TLS: ${config.tls ? 'Yes' : 'No'} |
                    ${config.network ? `Network: ${config.network}` : ''}
                </div>
            </div>
        `).join('');
        
        configsList.innerHTML = items;
        
    } catch (error) {
        configsList.innerHTML = '<div class="text-red-400 text-center py-8">Failed to load configurations</div>';
        console.error('Failed to load configurations:', error);
    }
}

/**
 * Get quality score color
 */
function getQualityColor(score) {
    const percentage = (score || 0) * 100;
    if (percentage >= 80) return 'text-green-400';
    if (percentage >= 60) return 'text-yellow-400';
    if (percentage >= 40) return 'text-orange-400';
    return 'text-red-400';
}

/**
 * Load sources
 */
async function loadSources() {
    const sourcesList = document.getElementById('sourcesList');
    if (!sourcesList) return;
    
    try {
        sourcesList.innerHTML = getLoadingSpinner();
        
        const response = await fetch(`${API_BASE}/api/v1/sources`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        const sources = data.sources || [];
        
        if (sources.length === 0) {
            sourcesList.innerHTML = '<div class="text-gray-400 text-center py-8">No sources configured</div>';
            return;
        }
        
        const items = sources.map(source => {
            const displayName = source.name || new URL(source.url).hostname;
            const configs = source.avg_config_count ?? 0;
            const successRate = Math.round((source.success_rate || 0) * 100);
            
            return `
                <div class="glass rounded-lg p-4 mb-3 hover:bg-white/10 transition-colors">
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="font-semibold text-white">${displayName}</div>
                            <div class="text-sm text-gray-300">
                                Configs: ${configs} | Success: ${successRate}% | 
                                Response: ${source.avg_response_time || 0}ms
                            </div>
                            <div class="text-xs text-gray-400 truncate">${source.url}</div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="status-dot ${source.status === 'active' ? 'status-active' : 'status-inactive'}"></span>
                            <span class="text-sm capitalize ${source.status === 'active' ? 'text-green-400' : 'text-red-400'}">
                                ${source.status || 'unknown'}
                            </span>
                        </div>
                    </div>
                    ${source.last_error ? `
                        <div class="mt-2 text-xs text-red-400">
                            Last Error: ${source.last_error}
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        sourcesList.innerHTML = items.join('');
        
    } catch (error) {
        sourcesList.innerHTML = '<div class="text-red-400 text-center py-8">Failed to load sources</div>';
        console.error('Failed to load sources:', error);
    }
}

/**
 * Load recent logs
 */
async function loadRecentLogs() {
    const logsContainer = document.getElementById('recentLogs');
    if (!logsContainer) return;
    
    try {
        // This is a placeholder - implement actual log fetching if backend supports it
        const logs = [
            { timestamp: new Date(), level: 'info', message: 'System initialized' },
            { timestamp: new Date(Date.now() - 30000), level: 'success', message: 'Source validation completed' },
            { timestamp: new Date(Date.now() - 60000), level: 'warning', message: 'High latency detected on source' },
            { timestamp: new Date(Date.now() - 120000), level: 'info', message: 'Configuration cache updated' }
        ];
        
        const logItems = logs.map(log => `
            <div class="flex items-start space-x-3 py-2">
                <div class="flex-shrink-0 w-2 h-2 rounded-full mt-2 ${getLogLevelColor(log.level)}"></div>
                <div class="flex-1 min-w-0">
                    <div class="text-sm text-gray-300">${log.message}</div>
                    <div class="text-xs text-gray-500">${formatRelativeTime(log.timestamp)}</div>
                </div>
            </div>
        `).join('');
        
        logsContainer.innerHTML = logItems;
        
    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

/**
 * Get log level color
 */
function getLogLevelColor(level) {
    const colors = {
        'info': 'bg-blue-400',
        'success': 'bg-green-400',
        'warning': 'bg-yellow-400',
        'error': 'bg-red-400'
    };
    return colors[level] || 'bg-gray-400';
}

/**
 * Start processing
 */
async function startProcessing() {
    const startBtn = document.getElementById('startProcessingBtn');
    if (!startBtn) return;
    
    const configPath = document.getElementById('configPath')?.value || 'config/sources.yaml';
    const formats = Array.from(document.querySelectorAll('.format-cb:checked')).map(cb => cb.value);
    
    if (formats.length === 0) {
        showNotification('Please select at least one output format', 'warning');
        return;
    }
    
    // Update UI
    startBtn.disabled = true;
    startBtn.innerHTML = '<span class="flex items-center justify-center"><div class="spinner mr-2"></div>Processing...</span>';
    
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.classList.remove('hidden');
        updateProgress(0, 'Starting...');
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/pipeline/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                config_path: configPath,
                output_dir: 'output',
                formats: formats
            })
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        
        const result = await response.json();
        currentJobId = result.job_id;
        
        showNotification('Pipeline started successfully!', 'success');
        
        // Start polling
        pollJobStatus(currentJobId);
        
    } catch (error) {
        console.error('Processing failed:', error);
        showNotification(`Pipeline failed: ${error.message}`, 'error');
        resetProcessingUI();
    }
}

/**
 * Poll job status
 */
function pollJobStatus(jobId) {
    if (jobPollingInterval) {
        clearInterval(jobPollingInterval);
    }
    
    jobPollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/pipeline/status/${jobId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const status = await response.json();
            updateProgress(status.progress * 100, status.status);
            
            if (status.status === 'completed') {
                clearInterval(jobPollingInterval);
                showNotification('Processing completed successfully!', 'success');
                resetProcessingUI();
                loadStatistics(); // Refresh stats
            } else if (status.status === 'failed') {
                clearInterval(jobPollingInterval);
                showNotification(`Processing failed: ${status.error || 'Unknown error'}`, 'error');
                resetProcessingUI();
            }
            
        } catch (error) {
            clearInterval(jobPollingInterval);
            console.error('Status polling failed:', error);
            resetProcessingUI();
        }
    }, 2000);
}

/**
 * Update progress
 */
function updateProgress(percent, message) {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressMessage = document.getElementById('progressMessage');
    
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    }
    
    if (progressPercent) {
        progressPercent.textContent = `${Math.round(percent)}%`;
    }
    
    if (progressMessage) {
        progressMessage.textContent = message;
    }
}

/**
 * Reset processing UI
 */
function resetProcessingUI() {
    const startBtn = document.getElementById('startProcessingBtn');
    if (startBtn) {
        startBtn.disabled = false;
        startBtn.innerHTML = 'Start Processing';
    }
    
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.classList.add('hidden');
    }
    
    currentJobId = null;
}

/**
 * Show configuration details
 */
function showConfigDetails(configId) {
    // This would open a modal with detailed configuration info
    console.log('Show config details for:', configId);
    showNotification('Configuration details feature coming soon!', 'info');
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 glass rounded-lg p-4 text-white transform translate-x-full transition-transform duration-300`;
    
    const colors = {
        'success': 'border-l-4 border-green-500',
        'error': 'border-l-4 border-red-500',
        'warning': 'border-l-4 border-yellow-500',
        'info': 'border-l-4 border-blue-500'
    };
    
    notification.classList.add(colors[type] || colors['info']);
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <span class="flex-1 mr-4">${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" 
                    class="text-xl hover:text-red-400 transition-colors">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Trigger slide-in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 10);
    
    // Auto-remove
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

/**
 * Get loading spinner HTML
 */
function getLoadingSpinner() {
    return `
        <div class="flex items-center justify-center py-12">
            <div class="spinner"></div>
            <span class="ml-3 text-gray-400">Loading...</span>
        </div>
    `;
}

/**
 * Format relative time
 */
function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (jobPollingInterval) {
        clearInterval(jobPollingInterval);
    }
});

// Export for compatibility
window.StreamlineVPN = {
    API_BASE,
    loadStatistics,
    loadConfigurations,
    loadSources,
    startProcessing,
    showNotification
};

