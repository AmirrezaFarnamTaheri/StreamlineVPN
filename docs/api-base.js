/**
 * API Base Configuration
 * Automatically detects and configures the API base URL for the frontend
 */

(function() {
    'use strict';

    /**
     * Determine the API base URL based on environment and configuration
     */
    function getApiBaseUrl() {
        // 0) Developer override persisted in localStorage
        try {
            if (typeof localStorage !== 'undefined') {
                const saved = localStorage.getItem('API_BASE_OVERRIDE');
                if (saved && /^https?:\/\//i.test(saved)) {
                    return saved;
                }
            }
        } catch (e) {
            // ignore storage errors
        }

        // 1) Explicit injection wins
        if (typeof window.__API_BASE_URL__ !== 'undefined' && window.__API_BASE_URL__) {
            return window.__API_BASE_URL__;
        }

        // 2) Meta tag override
        const metaApiBase = document.querySelector('meta[name="api-base"]');
        if (metaApiBase && metaApiBase.getAttribute('content')) {
            return metaApiBase.getAttribute('content');
        }

        // 3) Prefer same-origin when served over HTTP(S)
        const { protocol, hostname, port } = window.location;
        if (protocol === 'http:' || protocol === 'https:') {
            const portSegment = port ? `:${port}` : '';
            const originBase = `${protocol}//${hostname}${portSegment}`;
            return originBase;
        }

        // 4) file:// or other schemes -> fall back to common dev port
        return 'http://localhost:8080';
    }

    /**
     * Initialize API configuration
     */
    function initializeApiConfig() {
        const apiBase = getApiBaseUrl();
        
        // Set global API base
        window.__API_BASE__ = apiBase;
        window.API_BASE = apiBase; // Legacy compatibility
        
        // Log configuration for debugging (dev only)
        if (['localhost', '127.0.0.1'].includes(window.location.hostname)) {
            console.log('[StreamlineVPN] API Base URL:', apiBase);
        }
        
        // Test API connectivity
        testApiConnectivity(apiBase);
    }

    /**
     * Test API connectivity with fallback
     */
    async function testApiConnectivity(apiBase) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`${apiBase}/health`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                console.log('[StreamlineVPN] API connectivity verified');
                document.body.setAttribute('data-api-status', 'connected');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.warn('[StreamlineVPN] API connectivity issue:', error.message);
            document.body.setAttribute('data-api-status', 'disconnected');
            
            // Show user-friendly notification
            showApiConnectionWarning();
        }
    }

    /**
     * Show API connection warning to users
     */
    function showApiConnectionWarning() {
        // Only show in development or if explicitly enabled
        if (window.location.hostname === 'localhost' || window.location.search.includes('debug=1')) {
            const warning = document.createElement('div');
            warning.id = 'api-warning';
            warning.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                background: #f59e0b;
                color: #1f2937;
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                z-index: 9999;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: opacity 0.3s ease;
            `;
            warning.innerHTML = `
                ⚠️ API Connection Issue
                <button onclick="this.parentElement.remove()" style="margin-left: 10px; background: none; border: none; font-weight: bold; cursor: pointer;">×</button>
            `;
            document.body.appendChild(warning);
            
            // Auto-hide after 10 seconds
            setTimeout(() => {
                if (warning.parentElement) {
                    warning.style.opacity = '0';
                    setTimeout(() => warning.remove(), 300);
                }
            }, 10000);
        }
    }

    /**
     * Utility function for making API requests
     */
    window.makeApiRequest = async function(endpoint, options = {}) {
        const url = `${window.__API_BASE__}${endpoint}`;
        
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
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error('[StreamlineVPN] API Request Failed:', error);
            throw error;
        }
    };

    /**
     * Open a WebSocket to the root /ws endpoint with optional client_id query parameter.
     * Prefer this single-endpoint approach over subpaths to avoid environment restrictions.
     */
    window.openWebSocket = function(clientId, path) {
        try {
            var httpBase = window.__API_BASE__ || (window.location.protocol + '//' + window.location.host);
            var wsBase = httpBase.replace(/^http/i, 'ws');
            var p = (typeof path === 'string' && path.trim()) ? path.trim() : '/ws';
            if (!p.startsWith('/ws')) p = '/ws';
            var url = wsBase + p + (clientId ? (p.indexOf('?') === -1 ? '?' : '&') + 'client_id=' + encodeURIComponent(clientId) : '');
            return new WebSocket(url);
        } catch (e) {
            console.error('[StreamlineVPN] openWebSocket error:', e);
            throw e;
        }
    };

    /**
     * Resolve a client_id from context or persist one.
     * Order: data-client-id on body -> localStorage CLIENT_ID -> generated and saved.
     */
    window.resolveClientId = function() {
        try {
            var cid = document.body && document.body.getAttribute('data-client-id');
            if (cid && cid.trim()) return cid.trim();
        } catch(_) {}
        try {
            var saved = localStorage.getItem('CLIENT_ID');
            if (saved && saved.trim()) return saved;
        } catch(_) {}
        // Generate simple client id
        var gen = 'client_' + Math.random().toString(36).slice(2, 10);
        try { localStorage.setItem('CLIENT_ID', gen); } catch(_) {}
        return gen;
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeApiConfig);
    } else {
        initializeApiConfig();
    }

    // Export for manual initialization if needed
    window.initializeStreamlineVPN = initializeApiConfig;

    // Developer helpers: set/clear persistent override and broadcast change
    window.setApiBaseOverride = function(url) {
        try {
            if (!/^https?:\/\//i.test(url)) throw new Error('Invalid URL');
            localStorage.setItem('API_BASE_OVERRIDE', url);
            window.__API_BASE_URL__ = url;
            // Re-init and reload to ensure all modules pick up the change
            initializeApiConfig();
            try { window.dispatchEvent(new CustomEvent('api-base-changed', { detail: { apiBase: url } })); } catch(_) {}
            location.reload();
        } catch (e) {
            alert('Invalid API base URL. Please include http(s) scheme.');
        }
    };

    window.clearApiBaseOverride = function() {
        try {
            localStorage.removeItem('API_BASE_OVERRIDE');
            delete window.__API_BASE_URL__;
            initializeApiConfig();
            try { window.dispatchEvent(new CustomEvent('api-base-cleared')); } catch(_) {}
            location.reload();
        } catch (e) {
            // best-effort
            location.reload();
        }
    };
})();

