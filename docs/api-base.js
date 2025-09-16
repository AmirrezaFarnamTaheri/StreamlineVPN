/**
 * StreamlineVPN API Base Library
 * Provides frontend-backend communication
 */
(function(global) {
    'use strict';

    const API = {
        config: { baseURL: '', timeout: 30000 },

        init: function() {
            if (typeof window !== 'undefined') {
                const protocol = window.location.protocol;
                const hostname = window.location.hostname;
                this.config.baseURL = `${protocol}//${hostname}:8080`;
            }
        },

        url: function(endpoint) {
            const base = this.config.baseURL;
            const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
            return base + '/' + cleanEndpoint;
        },

        request: async function(endpoint, options = {}) {
            const url = this.url(endpoint);
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }
            return response.json();
        },

        get: function(endpoint, params = {}) {
            const url = new URL(this.url(endpoint));
            Object.keys(params).forEach(key => {
                if (params[key] !== undefined && params[key] !== null) {
                    url.searchParams.append(key, params[key]);
                }
            });
            return this.request(url.pathname + url.search, { method: 'GET' });
        },

        post: function(endpoint, data = {}) {
            return this.request(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }
    };

    if (typeof window !== 'undefined') {
        window.API = API;
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => API.init());
        } else {
            API.init();
        }
    }

})(typeof window !== 'undefined' ? window : global);
