/**
 * StreamlineVPN Main Application
 * ===============================
 *
 * Main frontend application logic for the control panel and interactive features.
 */

(function() {
    'use strict';

    class StreamlineVPNApp {
        constructor() {
            this.isInitialized = false;
            this.statistics = {};
            this.websocket = null;
            this.updateInterval = null;

            // Bind methods
            this.init = this.init.bind(this);
            this.updateStatistics = this.updateStatistics.bind(this);
            this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
        }

        /**
         * Initialize the application
         */
        async init() {
            if (this.isInitialized) return;

            console.log('Initializing StreamlineVPN App...');

            try {
                // Wait for API to be available
                await this.waitForAPI();

                // Check API health
                const health = await API.healthCheck();
                this.updateHealthStatus(health.healthy);

                // Initialize UI components
                this.initializeUI();

                // Start periodic updates
                this.startPeriodicUpdates();

                // Connect WebSocket for real-time updates
                this.connectWebSocket();

                this.isInitialized = true;
                console.log('✅ StreamlineVPN App initialized successfully');

            } catch (error) {
                console.error('❌ Failed to initialize app:', error);
                this.showError('Failed to initialize application. Please check if the API server is running.');
            }
        }

        /**
         * Wait for API to be available
         */
        async waitForAPI(timeout = 10000) {
            const start = Date.now();

            while (Date.now() - start < timeout) {
                if (typeof API !== 'undefined') {
                    return;
                }
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            throw new Error('API not available');
        }

        /**
         * Initialize UI components
         */
        initializeUI() {
            // Initialize navigation
            this.initializeNavigation();

            // Initialize statistics cards
            this.initializeStatisticsCards();

            // Initialize action buttons
            this.initializeActionButtons();

            // Initialize forms
            this.initializeForms();

            // Initialize tooltips and interactive elements
            this.initializeInteractiveElements();
        }

        /**
         * Initialize navigation
         */
        initializeNavigation() {
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    // Handle internal navigation
                    if (link.getAttribute('href').startsWith('#')) {
                        e.preventDefault();
                        const target = document.querySelector(link.getAttribute('href'));
                        if (target) {
                            target.scrollIntoView({ behavior: 'smooth' });
                        }
                    }
                });
            });
        }

        /**
         * Initialize statistics cards
         */
        initializeStatisticsCards() {
            // Add loading state to stat cards
            const statCards = document.querySelectorAll('.stat-card');
            statCards.forEach(card => {
                const value = card.querySelector('.stat-value');
                if (value && !value.textContent.trim()) {
                    value.textContent = '...';
                    card.classList.add('loading');
                }
            });
        }

        /**
         * Initialize action buttons
         */
        initializeActionButtons() {
            // Refresh button
            const refreshBtn = document.getElementById('refresh-btn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this.handleRefresh());
            }

            // Run pipeline button
            const pipelineBtn = document.getElementById('pipeline-btn');
            if (pipelineBtn) {
                pipelineBtn.addEventListener('click', () => this.handleRunPipeline());
            }

            // Clear cache button
            const clearCacheBtn = document.getElementById('clear-cache-btn');
            if (clearCacheBtn) {
                clearCacheBtn.addEventListener('click', () => this.handleClearCache());
            }
        }

        /**
         * Initialize forms
         */
        initializeForms() {
            // Source addition form
            const addSourceForm = document.getElementById('add-source-form');
            if (addSourceForm) {
                addSourceForm.addEventListener('submit', (e) => this.handleAddSource(e));
            }

            // Configuration search
            const searchInput = document.getElementById('config-search');
            if (searchInput) {
                let searchTimeout;
                searchInput.addEventListener('input', (e) => {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        this.handleConfigSearch(e.target.value);
                    }, 300);
                });
            }
        }

        /**
         * Initialize interactive elements
         */
        initializeInteractiveElements() {
            // Tooltips
            const tooltips = document.querySelectorAll('[data-tooltip]');
            tooltips.forEach(element => {
                this.addTooltip(element);
            });

            // Collapsible sections
            const collapsibles = document.querySelectorAll('.collapsible-header');
            collapsibles.forEach(header => {
                header.addEventListener('click', () => {
                    const content = header.nextElementSibling;
                    const isExpanded = header.classList.contains('expanded');

                    header.classList.toggle('expanded');
                    if (content) {
                        content.style.maxHeight = isExpanded ? '0' : content.scrollHeight + 'px';
                    }
                });
            });
        }

        /**
         * Start periodic updates
         */
        startPeriodicUpdates() {
            this.updateStatistics();
            this.updateInterval = setInterval(() => {
                this.updateStatistics();
            }, 30000); // Update every 30 seconds
        }

        /**
         * Update statistics from API
         */
        async updateStatistics() {
            try {
                const stats = await API.get('/api/statistics');
                this.statistics = stats;
                this.renderStatistics(stats);
            } catch (error) {
                console.warn('Failed to update statistics:', error);
            }
        }

        /**
         * Render statistics in UI
         */
        renderStatistics(stats) {
            // Update stat cards
            this.updateStatCard('total-configs', stats.total_configurations || 0);
            this.updateStatCard('active-sources', stats.active_sources || 0);
            this.updateStatCard('last-update', stats.last_update ? this.formatTime(stats.last_update) : 'Never');
            this.updateStatCard('processing-time', stats.processing_time ? `${stats.processing_time}ms` : 'N/A');

            // Update health indicators
            this.updateHealthIndicator('cache-health', stats.cache_health);
            this.updateHealthIndicator('source-health', stats.source_health);

            // Remove loading states
            const loadingCards = document.querySelectorAll('.stat-card.loading');
            loadingCards.forEach(card => card.classList.remove('loading'));
        }

        /**
         * Update individual stat card
         */
        updateStatCard(cardId, value) {
            const card = document.getElementById(cardId);
            if (card) {
                const valueElement = card.querySelector('.stat-value');
                if (valueElement) {
                    valueElement.textContent = value;
                }
            }
        }

        /**
         * Update health indicator
         */
        updateHealthIndicator(indicatorId, isHealthy) {
            const indicator = document.getElementById(indicatorId);
            if (indicator) {
                indicator.className = `health-indicator ${isHealthy ? 'healthy' : 'unhealthy'}`;
            }
        }

        /**
         * Connect WebSocket for real-time updates
         */
        connectWebSocket() {
            try {
                this.websocket = API.connectWebSocket();

                this.websocket.addEventListener('message', this.handleWebSocketMessage);

                this.websocket.addEventListener('close', () => {
                    console.log('WebSocket disconnected, attempting to reconnect...');
                    setTimeout(() => this.connectWebSocket(), 5000);
                });

            } catch (error) {
                console.warn('WebSocket not available:', error);
            }
        }

        /**
         * Handle WebSocket messages
         */
        handleWebSocketMessage(event) {
            try {
                const data = JSON.parse(event.data);

                switch (data.type) {
                    case 'statistics_update':
                        this.renderStatistics(data.data);
                        break;
                    case 'pipeline_status':
                        this.updatePipelineStatus(data.status);
                        break;
                    case 'notification':
                        this.showNotification(data.message, data.level);
                        break;
                    default:
                        console.log('Unhandled WebSocket message:', data);
                }
            } catch (error) {
                console.warn('Failed to parse WebSocket message:', error);
            }
        }

        /**
         * Event Handlers
         */
        async handleRefresh() {
            this.showNotification('Refreshing data...', 'info');

            try {
                await API.post('/api/refresh');
                await this.updateStatistics();
                this.showNotification('Data refreshed successfully', 'success');
            } catch (error) {
                this.showError('Failed to refresh data: ' + error.message);
            }
        }

        async handleRunPipeline() {
            this.showNotification('Starting pipeline...', 'info');

            try {
                const result = await API.post('/api/v1/pipeline/run');
                this.showNotification('Pipeline completed successfully', 'success');
                await this.updateStatistics();
            } catch (error) {
                this.showError('Pipeline failed: ' + error.message);
            }
        }

        async handleClearCache() {
            this.showNotification('Clearing cache...', 'info');

            try {
                await API.post('/api/v1/cache/clear');
                this.showNotification('Cache cleared successfully', 'success');
            } catch (error) {
                this.showError('Failed to clear cache: ' + error.message);
            }
        }

        async handleAddSource(event) {
            event.preventDefault();

            const form = event.target;
            const formData = new FormData(form);
            const url = formData.get('url');

            if (!url) {
                this.showError('Please enter a valid URL');
                return;
            }

            try {
                await API.post('/api/v1/sources', { url });
                this.showNotification('Source added successfully', 'success');
                form.reset();
                await this.updateStatistics();
            } catch (error) {
                this.showError('Failed to add source: ' + error.message);
            }
        }

        async handleConfigSearch(query) {
            if (!query.trim()) return;

            try {
                const results = await API.get('/api/v1/configurations', { search: query });
                this.renderSearchResults(results);
            } catch (error) {
                console.warn('Search failed:', error);
            }
        }

        /**
         * UI Helper Methods
         */
        updateHealthStatus(isHealthy) {
            const indicator = document.getElementById('api-health');
            if (indicator) {
                indicator.className = `health-indicator ${isHealthy ? 'healthy' : 'unhealthy'}`;
                indicator.title = isHealthy ? 'API is healthy' : 'API is unhealthy';
            }
        }

        updatePipelineStatus(status) {
            const indicator = document.getElementById('pipeline-status');
            if (indicator) {
                indicator.textContent = status;
                indicator.className = `status status-${status.toLowerCase()}`;
            }
        }

        showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;

            // Add to container
            let container = document.getElementById('notifications');
            if (!container) {
                container = document.createElement('div');
                container.id = 'notifications';
                container.className = 'notifications-container';
                document.body.appendChild(container);
            }

            container.appendChild(notification);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 5000);
        }

        showError(message) {
            this.showNotification(message, 'error');
            console.error(message);
        }

        addTooltip(element) {
            const tooltip = element.getAttribute('data-tooltip');
            if (!tooltip) return;

            element.addEventListener('mouseenter', (e) => {
                const tooltipElement = document.createElement('div');
                tooltipElement.className = 'tooltip';
                tooltipElement.textContent = tooltip;
                tooltipElement.style.position = 'absolute';
                tooltipElement.style.zIndex = '9999';

                document.body.appendChild(tooltipElement);

                const rect = element.getBoundingClientRect();
                tooltipElement.style.left = rect.left + 'px';
                tooltipElement.style.top = (rect.top - tooltipElement.offsetHeight - 5) + 'px';

                element._tooltip = tooltipElement;
            });

            element.addEventListener('mouseleave', () => {
                if (element._tooltip) {
                    document.body.removeChild(element._tooltip);
                    element._tooltip = null;
                }
            });
        }

        formatTime(timestamp) {
            return new Date(timestamp).toLocaleString();
        }

        /**
         * Cleanup
         */
        destroy() {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
            }

            if (this.websocket) {
                this.websocket.close();
            }

            this.isInitialized = false;
        }
    }

    // Create global app instance
    window.StreamlineVPNApp = new StreamlineVPNApp();

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.StreamlineVPNApp.init();
        });
    } else {
        window.StreamlineVPNApp.init();
    }

})();
