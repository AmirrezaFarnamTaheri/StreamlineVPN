/* Lightweight API base bootstrapper */
(function () {
  try {
    if (typeof window === 'undefined') return;

    // If already set, keep it
    if (typeof window.__API_BASE__ === 'string' && window.__API_BASE__.startsWith('http')) {
      console.debug('API base preset:', window.__API_BASE__);
      return;
    }

    // Allow an injected global override (e.g., from server-side)
    var injected = window.API_BASE_URL;
    if (typeof injected === 'string' && injected.startsWith('http')) {
      window.__API_BASE__ = injected;
      console.debug('API base (injected):', window.__API_BASE__);
      return;
    }

    var host = window.location.hostname;
    var proto = window.location.protocol;
    var isLocal = host === 'localhost' || host === '127.0.0.1';
    window.__API_BASE__ = isLocal ? proto + '//' + host + ':8080' : proto + '//' + host;
    console.debug('API base (computed):', window.__API_BASE__);
  } catch (e) {
    // Silent fail – frontend will fallback internally
  }
})();

