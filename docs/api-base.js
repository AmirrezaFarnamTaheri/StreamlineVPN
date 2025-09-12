// StreamlineVPN API Base Configuration
(function() {
    // Get API base from meta tag or environment
    const metaApiBase = document.querySelector('meta[name="api-base"]');
    const apiBase = metaApiBase ? metaApiBase.content : '';
    
    // Set global API base
    window.__API_BASE__ = apiBase || window.__API_BASE__ || 'http://localhost:8080';
    
    // Helper function for API requests
    window.makeApiRequest = async function(path, options = {}) {
        const url = `${window.__API_BASE__}${path}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, defaultOptions);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    };
    
    // Set and clear API base override functions
    window.setApiBaseOverride = function(url) {
        window.__API_BASE__ = url;
        localStorage.setItem('apiBaseOverride', url);
        window.dispatchEvent(new Event('api-base-changed'));
        location.reload();
    };
    
    window.clearApiBaseOverride = function() {
        localStorage.removeItem('apiBaseOverride');
        window.__API_BASE__ = apiBase || 'http://localhost:8080';
        window.dispatchEvent(new Event('api-base-cleared'));
        location.reload();
    };
    
    // Check for localStorage override
    const override = localStorage.getItem('apiBaseOverride');
    if (override) {
        window.__API_BASE__ = override;
    }
})();