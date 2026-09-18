
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const url = args[0] instanceof Request ? args[0].url : (typeof args[0] === 'string' ? args[0] : '');
    const response = await originalFetch.apply(this, args);
    
    if (url && url.includes('search-stream-dt')) {
        const clone = response.clone();
        window.__streamContentType = clone.headers.get('content-type') || 'none';
        clone.text().then(text => {
            window.__streamData = text;
        }).catch(err => {
            window.__streamData = "Error: " + err;
        });
    }
    return response;
};
