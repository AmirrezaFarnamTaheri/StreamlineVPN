/* API Base URL Bootstrapper */
(function() {
    'use strict';
    
    // Don't override if already set
    if (window.__API_BASE__ && window.__API_BASE__.startsWith('http')) {
        console.log('API base already set:', window.__API_BASE__);
        return;
    }
    // URL override (?api=https://host:port)
    try {
        const params = new URLSearchParams(window.location.search);
        const override = params.get('api');
        if (override && /^https?:\/\//.test(override)) {
            window.__API_BASE__ = override.replace(/\/$/, '');
            localStorage.setItem('API_BASE_OVERRIDE', window.__API_BASE__);
            console.log('API base from query override:', window.__API_BASE__);
            return;
        }
    } catch (e) {}

    // LocalStorage persisted override
    try {
        const saved = localStorage.getItem('API_BASE_OVERRIDE');
        if (saved && /^https?:\/\//.test(saved)) {
            window.__API_BASE__ = saved;
            console.log('API base from localStorage:', window.__API_BASE__);
            return;
        }
    } catch (e) {}

    // Check for environment override
    const envBase = window.API_BASE_URL || window.VUE_APP_API_URL;
    if (envBase) {
        window.__API_BASE__ = envBase;
        console.log('API base from env:', window.__API_BASE__);
        return;
    }
    
    // Auto-detect based on hostname - FIXED to prevent GitHub Pages issues
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;

    // Force localhost for GitHub Pages and other static hosts
    let apiBase;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        // Local development
        apiBase = `${protocol}//${hostname}:8080`;
    } else if (hostname.includes('github.io') || hostname.includes('gitlab.io') || hostname.includes('netlify') || hostname.includes('vercel')) {
        // Static hosting - always use localhost API
        console.warn('Static hosting detected, defaulting to localhost API');
        apiBase = 'http://localhost:8080';
    } else if (hostname.includes('localhost') || hostname.includes('127.0.0.1')) {
        // Docker or WSL
        apiBase = `${protocol}//${hostname.split(':')[0]}:8080`;
    } else {
        // Production - check if API exists on same host, otherwise localhost
        apiBase = `${protocol}//${hostname}:8080`;
    }
    
    // Probe health on both default and current host, choose the first that answers
    const candidates = Array.from(new Set([
        apiBase,
        `${protocol}//${hostname}`,
        `${protocol}//${hostname}:8080`
    ]));
    
    function pickFirstHealthy(index) {
        if (index >= candidates.length) {
            window.__API_BASE__ = apiBase;
            console.warn('Falling back to default API base:', apiBase);
            return;
        }
        const base = candidates[index];
        fetch(`${base}/health`, { method: 'GET' })
            .then(r => { if (r.ok) { window.__API_BASE__ = base; console.log('API base selected:', base);} else { throw new Error(); } })
            .catch(() => pickFirstHealthy(index + 1));
    }
    pickFirstHealthy(0);
})();
