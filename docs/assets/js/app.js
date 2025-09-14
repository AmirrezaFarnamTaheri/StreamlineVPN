// Application configuration
const APP_CONFIG = {
    API_BASE: window.__API_BASE__ || 'http://localhost:8080',
    UPDATE_INTERVALS: {
        STATISTICS: 30000,
        JOBS: 10000,
        SOURCES: 60000
    },
    RETRY: {
        MAX_ATTEMPTS: 3,
        DELAY: 1000
    }
};

// Utility functions
const utils = {
    formatDate: (dateString) => {
        if (!dateString) return 'Never';
        try {
            return new Date(dateString).toLocaleString();
        } catch {
            return 'Invalid Date';
        }
    },

    formatNumber: (num) => {
        if (typeof num !== 'number') return '0';
        return num.toLocaleString();
    },

    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    makeRequest: async (url, options = {}) => {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            ...options
        };

        try {
            const response = await fetch(`${APP_CONFIG.API_BASE}${url}`, defaultOptions);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Request failed for ${url}:`, error);
            throw error;
        }
    }
};

// Statistics management
const statistics = {
    cache: null,
    lastUpdate: null,

    async load() {
        try {
            this.cache = await utils.makeRequest('/api/statistics');
            this.lastUpdate = new Date();
            this.render();
            return this.cache;
        } catch (error) {
            console.error('Failed to load statistics:', error);
            this.renderError();
            throw error;
        }
    },

    render() {
        if (!this.cache) return;

        const stats = this.cache;
        const elements = {
            totalConfigs: document.getElementById('stat-total-configs'),
            activeSources: document.getElementById('stat-active-sources'),
            successRate: document.getElementById('stat-success-rate'),
            lastUpdate: document.getElementById('stat-last-update')
        };

        if (elements.totalConfigs) {
            elements.totalConfigs.textContent = utils.formatNumber(stats.total_configurations || 0);
        }
        if (elements.activeSources) {
            elements.activeSources.textContent = utils.formatNumber(stats.active_sources || 0);
        }
        if (elements.successRate) {
            const rate = stats.success_rate || 0;
            elements.successRate.textContent = `${(rate * 100).toFixed(1)}%`;
        }
        if (elements.lastUpdate) {
            elements.lastUpdate.textContent = utils.formatDate(stats.last_update);
        }
    },

    renderError() {
        const errorMessage = 'Failed to load statistics';
        ['stat-total-configs', 'stat-active-sources', 'stat-success-rate', 'stat-last-update']
            .forEach(id => {
                const element = document.getElementById(id);
                if (element) element.textContent = 'Error';
            });
    }
};

// Job management
const jobs = {
    cache: [],

    async load() {
        try {
            const response = await utils.makeRequest('/api/jobs');
            this.cache = response.jobs || [];
            this.render();
            return this.cache;
        } catch (error) {
            console.error('Failed to load jobs:', error);
            this.renderError();
            throw error;
        }
    },

    render() {
        const container = document.getElementById('jobs-container');
        if (!container) return;

        if (this.cache.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-400 py-8">No jobs found</div>';
            return;
        }

        container.innerHTML = this.cache.map(job => `
            <div class="job-card glass p-4 rounded-lg border-l-4 ${this.getStatusColor(job.status)}">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="font-semibold text-lg">${job.type || 'Unknown'}</h3>
                    <span class="status-badge ${job.status.toLowerCase()} px-3 py-1 rounded-full text-sm font-medium">
                        ${job.status}
                    </span>
                </div>
                <div class="text-sm text-gray-300 space-y-1">
                    <div>Created: ${utils.formatDate(job.created_at)}</div>
                    ${job.completed_at ? `<div>Completed: ${utils.formatDate(job.completed_at)}</div>` : ''}
                    ${job.error ? `<div class="text-red-400">Error: ${job.error}</div>` : ''}
                </div>
            </div>
        `).join('');
    },

    getStatusColor(status) {
        const colors = {
            'completed': 'border-green-500',
            'running': 'border-blue-500',
            'failed': 'border-red-500',
            'pending': 'border-yellow-500'
        };
        return colors[status.toLowerCase()] || 'border-gray-500';
    },

    renderError() {
        const container = document.getElementById('jobs-container');
        if (container) {
            container.innerHTML = '<div class="text-center text-red-400 py-8">Failed to load jobs</div>';
        }
    }
};

// Application initialization
const app = {
    initialized: false,
    intervals: {},

    async init() {
        if (this.initialized) return;

        try {
            // Load initial data
            await Promise.allSettled([
                statistics.load(),
                jobs.load()
            ]);

            // Setup event listeners
            this.setupEventListeners();

            // Start periodic updates
            this.startPeriodicUpdates();

            this.initialized = true;
        } catch (error) {
            console.error('App initialization failed:', error);
        }
    },

    setupEventListeners() {
        // Manual refresh
        const refreshBtn = document.getElementById('refresh-all');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', utils.debounce(async () => {
                await this.refreshAll();
            }, 1000));
        }

        // Process trigger
        const processBtn = document.getElementById('trigger-process');
        if (processBtn) {
            processBtn.addEventListener('click', utils.debounce(async () => {
                await this.triggerProcess();
            }, 2000));
        }
    },

    startPeriodicUpdates() {
        // Statistics updates
        this.intervals.statistics = setInterval(() => {
            statistics.load().catch(console.error);
        }, APP_CONFIG.UPDATE_INTERVALS.STATISTICS);

        // Jobs updates
        this.intervals.jobs = setInterval(() => {
            jobs.load().catch(console.error);
        }, APP_CONFIG.UPDATE_INTERVALS.JOBS);
    },

    async refreshAll() {
        try {
            await Promise.all([
                statistics.load(),
                jobs.load()
            ]);
            this.showNotification('Data refreshed successfully', 'success');
        } catch (error) {
            this.showNotification('Refresh failed', 'error');
        }
    },

    async triggerProcess() {
        try {
            await utils.makeRequest('/api/v1/pipeline/run', { method: 'POST' });
            this.showNotification('Process started successfully', 'success');

            // Refresh jobs after a short delay
            setTimeout(() => jobs.load().catch(console.error), 2000);
        } catch (error) {
            this.showNotification('Failed to start process', 'error');
        }
    },

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
            background: ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6'};
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },

    destroy() {
        // Clear intervals
        Object.values(this.intervals).forEach(clearInterval);
        this.intervals = {};
        this.initialized = false;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => app.init());
} else {
    app.init();
}

// Export for global access
window.StreamlineApp = app;
