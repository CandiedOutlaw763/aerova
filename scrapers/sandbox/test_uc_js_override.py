import undetected_chromedriver as uc
import time
import json

init_script = """
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

// Also hook XHR just in case
const originalXHR = window.XMLHttpRequest;
window.XMLHttpRequest = function() {
    const xhr = new originalXHR();
    const originalOpen = xhr.open;
    xhr.open = function() {
        this.__url = arguments[1];
        return originalOpen.apply(this, arguments);
    };
    xhr.addEventListener('load', function() {
        if (this.__url && this.__url.includes('search-stream-dt')) {
            window.__streamContentType = this.getResponseHeader('content-type') || 'none';
            window.__streamData = this.responseText;
        }
    });
    return xhr;
};
"""

def run_uc_js_override():
    print("Launching UC with JS override...")
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(version_main=152, options=options)
    
    print("Injecting script on new document...")
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': init_script})
    
    print("Navigating to MakeMyTrip...")
    driver.get("https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E")
    
    print("Waiting 30 seconds for flights to load...")
    time.sleep(30)
    
    try:
        content_type = driver.execute_script("return window.__streamContentType;")
        stream_data = driver.execute_script("return window.__streamData;")
        
        print("\n--- INTERCEPTED DATA ---")
        print(f"Content-Type: {content_type}")
        
        if stream_data:
            print(f"Data length: {len(stream_data)} chars")
            print(f"Preview: {stream_data[:500]}")
            with open("mmt_intercepted_uc.txt", "w", encoding="utf-8") as f:
                f.write(stream_data)
            print("Successfully saved intercepted data to mmt_intercepted_uc.txt")
        else:
            print("No data captured. __streamData is empty or undefined.")
            
    except Exception as e:
        print("Error evaluating JS:", e)
        
    driver.quit()

if __name__ == "__main__":
    run_uc_js_override()
