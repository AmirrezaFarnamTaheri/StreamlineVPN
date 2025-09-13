// Complete api-base.js implementation
window.API = {
    baseURL: window.__API_BASE__ || 'http://localhost:8080',
    
    url: function(endpoint) {
        const base = this.baseURL.replace(/\/$/, '');
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
        return base + cleanEndpoint;
    },
    
    request: async function(endpoint, options = {}) {
        const url = this.url(endpoint);
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers
            }
        };
        const requestOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, requestOptions);
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            throw error;
        }
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
            body: JSON.stringify(data)
        });
    },
    
    put: function(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    delete: function(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Auto-configure API base URL from environment
if (typeof window !== 'undefined') {
    // Set from environment variable or current host
    window.__API_BASE__ = window.__API_BASE__ ||
        (location.protocol + '//' + location.hostname + ':8080');
}
