/**
 * API Base Configuration for StreamlineVPN Frontend
 * Dynamically configures API endpoints based on environment
 */

(function() {
    'use strict';

    // Default API base URL - can be overridden by server-side injection
    let apiBase = 'http://localhost:8080';
    
    // Check if server injected API base (from environment variable API_BASE_URL)
    if (typeof window !== 'undefined' && window.location) {
        // Try to detect if we're in a production environment
        const isProduction = window.location.protocol === 'https:' || 
                            window.location.hostname !== 'localhost';
        
        if (isProduction) {
            // In production, assume API is on same host with different port or path
            apiBase = `${window.location.protocol}//${window.location.hostname}:8080`;
        }
    }
    
    // Allow server-side override (injected by backend)
    if (typeof window !== 'undefined' && window.__API_BASE_OVERRIDE__) {
        apiBase = window.__API_BASE_OVERRIDE__;
    }
    
    // Make API base available globally
    if (typeof window !== 'undefined') {
        window.__API_BASE__ = apiBase;
        
        // Emit event for components that need to react to API base changes
        window.dispatchEvent(new CustomEvent('api-base-loaded', {
            detail: { apiBase: apiBase }
        }));
    }
    
    // For Node.js environments (if needed)
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { apiBase };
    }
})();

/**
 * API Client Helper Functions
 */
window.StreamlineVPN = window.StreamlineVPN || {};

window.StreamlineVPN.API = {
    /**
     * Get the current API base URL
     */
    getBase: function() {
        return window.__API_BASE__ || 'http://localhost:8080';
    },
    
    /**
     * Build a full API URL
     */
    url: function(endpoint) {
        const base = this.getBase();
        // Ensure endpoint starts with /
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
        return base + cleanEndpoint;
    },
    
    /**
     * Make an API request with proper error handling
     */
    request: async function(endpoint, options = {}) {
        const url = this.url(endpoint);
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };
        
        const requestOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }
            
            // Try to parse as JSON, fallback to text
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            // console.error(`API request failed for ${endpoint}:`, error);
            throw error;
        }
    },
    
    /**
     * GET request helper
     */
    get: function(endpoint, params = {}) {
        const url = new URL(this.url(endpoint));
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return this.request(url.pathname + url.search, { method: 'GET' });
    },
    
    /**
     * POST request helper
     */
    post: function(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * Health check helper
     */
    healthCheck: async function() {
        try {
            const response = await this.get('/health');
            return { success: true, data: response };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
};

/**
 * Connection status monitoring
 */
window.StreamlineVPN.ConnectionMonitor = {
    isConnected: false,
    lastCheck: null,
    checkInterval: 30000, // 30 seconds
    intervalId: null,
    
    start: function() {
        this.check();
        this.intervalId = setInterval(() => this.check(), this.checkInterval);
    },
    
    stop: function() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    },
    
    check: async function() {
        const health = await window.StreamlineVPN.API.healthCheck();
        const wasConnected = this.isConnected;
        this.isConnected = health.success;
        this.lastCheck = new Date();
        
        // Emit connection status change events
        if (wasConnected !== this.isConnected) {
            window.dispatchEvent(new CustomEvent('api-connection-changed', {
                detail: { 
                    connected: this.isConnected, 
                    health: health.success ? health.data : null,
                    error: health.error 
                }
            }));
        }
        
        return this.isConnected;
    }
};

