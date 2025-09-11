(function(){
    'use strict';

    async function buildErrorMessage(actionLabel, response, url){
        try{
            const status = response && typeof response.status === 'number' ? response.status : 'N/A';
            const statusText = response && response.statusText ? response.statusText : '';
            let bodyPreview = '';
            if(response && response.text){
                const raw = await response.text();
                bodyPreview = raw ? (raw.slice(0,200) + (raw.length>200?'…':'')) : '';
            }
            return `${actionLabel} failed\nURL: ${url}\nStatus: ${status} ${statusText}` + (bodyPreview?`\nResponse preview: ${bodyPreview}`:'');
        }catch(_){
            return `${actionLabel} failed\nURL: ${url}`;
        }
    }

    async function requestJSON(action, url, options){
        const resp = await fetch(url, options);
        if(!resp.ok){
            throw new Error(await buildErrorMessage(action, resp, url));
        }
        const ct = resp.headers.get('content-type') || '';
        if(!ct.includes('application/json')){
            throw new Error(`${action} returned non-JSON content for ${url}`);
        }
        return await resp.json();
    }

    // Expose globally
    window.__ERR__ = { buildErrorMessage, requestJSON };
})();


