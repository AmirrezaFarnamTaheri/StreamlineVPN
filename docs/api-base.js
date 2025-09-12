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
        // Check if API_BASE_URL is set by the server
        if (typeof window.__API_BASE_URL__ !== 'undefined' && window.__API_BASE_URL__) {
            return window.__API_BASE_URL__;
        }

        // Check for environment variable or meta tag
        const metaApiBase = document.querySelector('meta[name="api-base"]');
        if (metaApiBase && metaApiBase.getAttribute('content')) {
            return metaApiBase.getAttribute('content');
        }

        // Auto-detect based on current location
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        // Development environments
        if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.')) {
            return `${protocol}//${hostname}:8080`;
        }
        
        // Production environments
        if (hostname.includes('streamlinevpn') || hostname.includes('vpn-api')) {
            return `${protocol}//api.${hostname}`;
        }
        
        // Default fallback
        return `${protocol}//${hostname}:8080`;
    }

    /**
     * Initialize API configuration
     */
    function initializeApiConfig() {
        const apiBase = getApiBaseUrl();
        
        // Set global API base
        window.__API_BASE__ = apiBase;
        window.API_BASE = apiBase; // Legacy compatibility
        
        // Log configuration for debugging
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
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

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeApiConfig);
    } else {
        initializeApiConfig();
    }

    // Export for manual initialization if needed
    window.initializeStreamlineVPN = initializeApiConfig;
})();

