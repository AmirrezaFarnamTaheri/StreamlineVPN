class StreamlineVPNApp {
    constructor() {
        this.isInitialized = false;
        this.config = {
            updateInterval: 30000,
            retryAttempts: 3,
            retryDelay: 1000
        };
        this.init();
    }

    async init() {
        try {
            await this.loadInitialData();
            this.setupEventListeners();
            this.startPeriodicUpdates();
            this.isInitialized = true;
        } catch (error) {
            console.error('Failed to initialize StreamlineVPN App:', error);
            this.showError('Failed to initialize application');
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadStatistics(),
            this.loadSources(),
            this.loadJobs()
        ]);
    }

    async loadStatistics() {
        try {
            const stats = await API.get('/api/statistics');
            this.updateStatisticsDisplay(stats);
        } catch (error) {
            console.error('Failed to load statistics:', error);
            this.showError('Failed to load statistics');
        }
    }

    async loadSources() {
        try {
            const sources = await API.get('/api/v1/sources');
            this.updateSourcesDisplay(sources);
        } catch (error) {
            console.error('Failed to load sources:', error);
        }
    }

    async loadJobs() {
        try {
            const jobs = await API.get('/api/jobs');
            this.updateJobsDisplay(jobs);
        } catch (error) {
            console.error('Failed to load jobs:', error);
        }
    }

    updateStatisticsDisplay(stats) {
        const elements = {
            totalConfigs: document.getElementById('total-configs'),
            activeSources: document.getElementById('active-sources'),
            lastUpdate: document.getElementById('last-update'),
            qualityScore: document.getElementById('quality-score')
        };

        if (elements.totalConfigs) elements.totalConfigs.textContent = stats.total_configurations || 0;
        if (elements.activeSources) elements.activeSources.textContent = stats.active_sources || 0;
        if (elements.lastUpdate) elements.lastUpdate.textContent = stats.last_update || 'Never';
        if (elements.qualityScore) elements.qualityScore.textContent = stats.quality_score || 'N/A';
    }

    updateSourcesDisplay(sources) {
        const container = document.getElementById('sources-list');
        if (!container) return;

        container.innerHTML = sources.sources.map(source => `
            <div class="source-item glass p-4 rounded-lg">
                <div class="flex justify-between items-center">
                    <span class="font-medium">${source.name || source}</span>
                    <span class="quality-badge bg-green-500 text-white px-2 py-1 rounded text-sm">
                        Active
                    </span>
                </div>
            </div>
        `).join('');
    }

    updateJobsDisplay(jobs) {
        const container = document.getElementById('jobs-list');
        if (!container) return;

        container.innerHTML = jobs.jobs.map(job => `
            <div class="job-item glass p-4 rounded-lg">
                <div class="flex justify-between items-center">
                    <div>
                        <div class="font-medium">${job.type}</div>
                        <div class="text-sm text-gray-400">${job.created_at}</div>
                    </div>
                    <span class="status-badge ${job.status.toLowerCase()} px-2 py-1 rounded text-sm">
                        ${job.status}
                    </span>
                </div>
            </div>
        `).join('');
    }

    setupEventListeners() {
        // Process button
        const processBtn = document.getElementById('process-btn');
        if (processBtn) {
            processBtn.addEventListener('click', () => this.runProcess());
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.forceRefresh());
        }

        // Export buttons
        document.querySelectorAll('[data-export]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.dataset.export;
                this.exportConfigurations(format);
            });
        });
    }

    async runProcess() {
        try {
            this.showProcessing();
            const result = await API.post('/api/v1/pipeline/run', {});
            this.showSuccess('Processing completed successfully');
            await this.loadInitialData();
        } catch (error) {
            console.error('Process failed:', error);
            this.showError('Processing failed');
        } finally {
            this.hideProcessing();
        }
    }

    async forceRefresh() {
        try {
            await API.post('/api/refresh');
            await this.loadInitialData();
            this.showSuccess('Data refreshed successfully');
        } catch (error) {
            console.error('Refresh failed:', error);
            this.showError('Refresh failed');
        }
    }

    async exportConfigurations(format) {
        try {
            const response = await API.get(`/api/export/${format}`);
            if (format === 'download') {
                // Handle file download
                const blob = new Blob([JSON.stringify(response)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `vpn_configs_${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                URL.revokeObjectURL(url);
            }
            this.showSuccess(`Export to ${format} completed`);
        } catch (error) {
            console.error('Export failed:', error);
            this.showError('Export failed');
        }
    }

    startPeriodicUpdates() {
        setInterval(() => {
            if (this.isInitialized) {
                this.loadStatistics();
            }
        }, this.config.updateInterval);
    }

    showProcessing() {
        const processBtn = document.getElementById('process-btn');
        if (processBtn) {
            processBtn.disabled = true;
            processBtn.textContent = 'Processing...';
        }
    }

    hideProcessing() {
        const processBtn = document.getElementById('process-btn');
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.textContent = 'Run Process';
        }
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50`;
        toast.style.cssText = `
            background: ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6'};
            color: white;
            animation: slideInRight 0.3s ease-out;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof API !== 'undefined') {
        window.streamlineApp = new StreamlineVPNApp();
    } else {
        console.error('API object not found. Make sure api-base.js is loaded first.');
    }
});
