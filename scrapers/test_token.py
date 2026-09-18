import json
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo Token Creation Headers...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.get("https://www.goindigo.in/")
        import time
        time.sleep(10)
        
        js_script = """
        var done = arguments[0];
        fetch('https://api-prod-session-skyplus6e.goindigo.in/v1/token/create', {
            method: 'GET',
            headers: {
                'user_key': '654a6a3cc4998e498e5c0c8ead072915',
                'Accept': 'application/json, text/plain, */*'
            }
        })
        .then(res => {
            let headers = {};
            for (let pair of res.headers.entries()) {
               headers[pair[0]] = pair[1];
            }
            res.text().then(text => {
                done({
                    status: res.status,
                    headers: headers,
                    text: text
                });
            });
        })
        .catch(e => done({"error": e.toString()}));
        """
        
        response = driver.execute_async_script(js_script)
        print("Token response:", json.dumps(response, indent=2))
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
