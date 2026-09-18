import json
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo Token Creation POST...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.get("https://www.goindigo.in/")
        import time
        time.sleep(10)
        
        js_script = """
        var done = arguments[0];
        fetch('https://api-prod-session-skyplus6e.goindigo.in/v1/token/create', {
            method: 'POST',
            headers: {
                'user_key': '654a6a3cc4998e498e5c0c8ead072915',
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*'
            },
            body: JSON.stringify({})
        })
        .then(res => res.json())
        .then(data => done({"status": 200, "data": data}))
        .catch(e => done({"error": e.toString()}));
        """
        
        response = driver.execute_async_script(js_script)
        print("Token response:", json.dumps(response, indent=2))
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
