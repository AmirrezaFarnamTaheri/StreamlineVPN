/**
 * StreamlineVPN API Base Library (Advanced)
 * Provides a robust frontend-backend communication client with retries,
 * timeout handling, file upload, and WebSocket helper.
 */
(function (global) {
  'use strict';

  const API = {
    // Configuration
    config: {
      baseURL: '', // Determined in init()
      timeout: 30000,
      retries: 3,
      retryDelay: 1000,
    },

    // Initialize and determine baseURL
    init: function () {
      if (typeof window !== 'undefined') {
        if (window.__API_BASE__) {
          this.config.baseURL = window.__API_BASE__;
        } else {
          const protocol = window.location.protocol;
          const hostname = window.location.hostname;
          if (hostname === 'localhost' || hostname === '127.0.0.1') {
            this.config.baseURL = `${protocol}//${hostname}:8080`;
          } else {
            // Same origin in non-local environments
            this.config.baseURL = `${protocol}//${window.location.host}`;
          }
        }
      } else if (global && global.__API_BASE__) {
        this.config.baseURL = global.__API_BASE__;
      }
      // Expose resolved base for other scripts and smoke checks
      try {
        if (typeof window !== 'undefined') {
          window.__API_BASE__ = window.__API_BASE__ || this.config.baseURL;
        }
      } catch {}
      try {
        console.log('StreamlineVPN API initialized:', this.config.baseURL);
      } catch {}
    },

    // Build clean URL
    url: function (endpoint) {
      const base = (this.config.baseURL || '').replace(/\/$/, '');
      const cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
      return base + cleanEndpoint;
    },

    // Generate unique request id
    generateRequestId: function () {
      return (
        Date.now().toString(36) + Math.random().toString(36).substr(2)
      );
    },

    // Delay helper
    delay: function (ms) {
      return new Promise((resolve) => setTimeout(resolve, ms));
    },

    // Core request with retries and timeout
    request: async function (endpoint, options = {}) {
      const url = this.url(endpoint);
      const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      };
      headers['X-Request-ID'] = this.generateRequestId();

      const requestOptions = { ...options, headers };

      let lastError;
      for (let attempt = 1; attempt <= this.config.retries; attempt++) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(
            () => controller.abort(),
            this.config.timeout
          );

          const response = await fetch(url, {
            ...requestOptions,
            signal: controller.signal,
          });

          clearTimeout(timeoutId);

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const ct = response.headers.get('content-type') || '';
          if (ct.includes('application/json')) {
            return await response.json();
          }
          return await response.text();
        } catch (error) {
          lastError = error;
          if (attempt < this.config.retries) {
            try {
              console.warn(
                `API request attempt ${attempt} failed, retrying...`,
                error && error.message ? error.message : error
              );
            } catch {}
            await this.delay(this.config.retryDelay * attempt);
          }
        }
      }
      try {
        console.error(
          `API request failed after ${this.config.retries} attempts:`,
          lastError
        );
      } catch {}
      throw lastError;
    },

    // HTTP helpers
    get: function (endpoint, params = {}) {
      const u = new URL(this.url(endpoint));
      Object.keys(params).forEach((k) => {
        if (params[k] !== undefined && params[k] !== null) {
          u.searchParams.append(k, params[k]);
        }
      });
      return this.request(u.pathname + u.search, { method: 'GET' });
    },

    post: function (endpoint, data = {}) {
      return this.request(endpoint, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    put: function (endpoint, data = {}) {
      return this.request(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    },

    delete: function (endpoint) {
      return this.request(endpoint, { method: 'DELETE' });
    },

    // File upload with progress callback
    upload: function (endpoint, file, onProgress = null) {
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
              resolve(JSON.parse(xhr.responseText));
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

    // Health check
    healthCheck: async function () {
      try {
        const result = await this.get('/health');
        return { healthy: true, data: result };
      } catch (error) {
        return { healthy: false, error: error && error.message ? error.message : String(error) };
      }
    },

    // WebSocket connector
    connectWebSocket: function (endpoint = '/ws') {
      const wsUrl = this.url(endpoint).replace(/^http/, 'ws');
      const ws = new WebSocket(wsUrl);
      try {
        ws.addEventListener('open', () => console.log('WebSocket connected:', wsUrl));
        ws.addEventListener('error', (e) => console.error('WebSocket error:', e));
        ws.addEventListener('close', (ev) =>
          console.log('WebSocket closed:', ev.code, ev.reason)
        );
      } catch {}
      return ws;
    },
  };

  // Initialize and expose
  if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => API.init());
    } else {
      API.init();
    }
    window.API = API;
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
  }
  if (typeof define === 'function' && define.amd) {
    define(function () {
      return API;
    });
  }
})(typeof window !== 'undefined' ? window : global);
