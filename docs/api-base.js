/* API Base URL Bootstrapper */
(function() {
    'use strict';
    
    // Don't override if already set
    if (window.__API_BASE__ && window.__API_BASE__.startsWith('http')) {
        console.log('API base already set:', window.__API_BASE__);
        return;
    }
    
    // Check for environment override
    const envBase = window.API_BASE_URL || window.VUE_APP_API_URL;
    if (envBase) {
        window.__API_BASE__ = envBase;
        console.log('API base from env:', window.__API_BASE__);
        return;
    }
    
    // Auto-detect based on hostname
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // Default API port is 8080
    let apiBase;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        // Local development
        apiBase = `${protocol}//${hostname}:8080`;
    } else if (hostname.includes('localhost') || hostname.includes('127.0.0.1')) {
        // Docker or WSL
        apiBase = `${protocol}//${hostname.split(':')[0]}:8080`;
    } else {
        // Production - assume same host
        apiBase = `${protocol}//${hostname}`;
    }
    
    window.__API_BASE__ = apiBase;
    console.log('API base auto-detected:', window.__API_BASE__);
})();
