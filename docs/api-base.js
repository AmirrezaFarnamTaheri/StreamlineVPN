/**
 * StreamlineVPN API Base Library
 * ================================
 *
 * Provides a clean interface for frontend-backend communication.
 */

(function(global) {
    'use strict';

    const API = {
        // Configuration
        config: {
            baseURL: '',  // Will be determined dynamically
            timeout: 30000,
            retries: 3,
            retryDelay: 1000
        },

        /**
         * Initialize the API client
         */
        init: function() {
            // Determine base URL based on current location
            if (typeof window !== 'undefined') {
                const protocol = window.location.protocol;
                const hostname = window.location.hostname;

                // Use same host but different port for API in development
                if (hostname === 'localhost' || hostname === '127.0.0.1') {
                    this.config.baseURL = `${protocol}//${hostname}:8080`;
                } else {
                    // Production - assume same origin
                    this.config.baseURL = `${protocol}//${window.location.host}`;
                }
            }

            console.log('StreamlineVPN API initialized:', this.config.baseURL);
        },

        /**
         * Build complete URL for endpoint
         */
        url: function(endpoint) {
            const base = this.config.baseURL;
            const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
            return base + '/' + cleanEndpoint;
        },

        /**
         * Core request method with error handling and retries
         */
        request: async function(endpoint, options = {}) {
            const url = this.url(endpoint);
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                timeout: this.config.timeout
            };

            const requestOptions = { ...defaultOptions, ...options };

            // Add request ID for tracking
            requestOptions.headers['X-Request-ID'] = this.generateRequestId();

            let lastError;

            // Retry logic
            for (let attempt = 1; attempt <= this.config.retries; attempt++) {
                try {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

                    const response = await fetch(url, {
                        ...requestOptions,
                        signal: controller.signal
                    });

                    clearTimeout(timeoutId);

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

                    if (attempt < this.config.retries) {
                        console.warn(`API request attempt ${attempt} failed, retrying...`, error.message);
                        await this.delay(this.config.retryDelay * attempt);
                    }
                }
            }
            
            console.error(`API request failed after ${this.config.retries} attempts:`, lastError);
            throw lastError;
        },

        /**
         * GET request with query parameters
         */
        get: function(endpoint, params = {}) {
            const url = new URL(this.url(endpoint));

            // Add query parameters
            Object.keys(params).forEach(key => {
                if (params[key] !== undefined && params[key] !== null) {
                    url.searchParams.append(key, params[key]);
                }
            });

            return this.request(url.pathname + url.search, { method: 'GET' });
        },

        /**
         * POST request with JSON body
         */
        post: function(endpoint, data = {}) {
            return this.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        /**
         * PUT request with JSON body
         */
        put: function(endpoint, data = {}) {
            return this.request(endpoint, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },

        /**
         * DELETE request
         */
        delete: function(endpoint) {
            return this.request(endpoint, {
                method: 'DELETE'
            });
        },

        /**
         * Upload file with progress tracking
         */
        upload: function(endpoint, file, onProgress = null) {
            return new Promise((resolve, reject) => {
                const formData = new FormData();
                formData.append('file', file);

                const xhr = new XMLHttpRequest();

                if (onProgress) {
                    xhr.upload.addEventListener('progress', (e) => {
                        if (e.lengthComputable) {
                            onProgress(Math.round((e.loaded / e.total) * 100));
                        }
                    });
                }

                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            resolve(response);
                        } catch {
                            resolve(xhr.responseText);
                        }
                    } else {
                        reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
                    }
                });

                xhr.addEventListener('error', () => {
                    reject(new Error('Upload failed: Network error'));
                });

                xhr.open('POST', this.url(endpoint));
                xhr.setRequestHeader('X-Request-ID', this.generateRequestId());
                xhr.send(formData);
            });
        },

        /**
         * Utility methods
         */
        generateRequestId: function() {
            return Date.now().toString(36) + Math.random().toString(36).substr(2);
        },

        delay: function(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        },

        /**
         * Health check
         */
        healthCheck: async function() {
            try {
                const result = await this.get('/health');
                return { healthy: true, data: result };
            } catch (error) {
                return { healthy: false, error: error.message };
            }
        },

        /**
         * WebSocket connection helper
         */
        connectWebSocket: function(endpoint = '/ws') {
            const wsUrl = this.url(endpoint).replace(/^http/, 'ws');
            const ws = new WebSocket(wsUrl);

            ws.addEventListener('open', () => {
                console.log('WebSocket connected:', wsUrl);
            });

            ws.addEventListener('error', (error) => {
                console.error('WebSocket error:', error);
            });

            ws.addEventListener('close', (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
            });

            return ws;
        }
    };

    // Initialize API when loaded
    if (typeof window !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => API.init());
        } else {
            API.init();
        }

        // Make API globally available
        window.API = API;
    }

    // Export for Node.js/module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = API;
    }

    // AMD support
    if (typeof define === 'function' && define.amd) {
        define(function() {
            return API;
        });
    }

})(typeof window !== 'undefined' ? window : global);
