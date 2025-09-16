/**
 * StreamlineVPN Main Application
 */
(function() {
    'use strict';

    class StreamlineVPNApp {
        constructor() {
            this.isInitialized = false;
        }

        async init() {
            if (this.isInitialized) return;
            console.log('Initializing StreamlineVPN App...');
            this.isInitialized = true;
        }
    }

    window.StreamlineVPNApp = new StreamlineVPNApp();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.StreamlineVPNApp.init();
        });
    } else {
        window.StreamlineVPNApp.init();
    }
})();
