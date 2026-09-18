import json
from engine.spiders.base_uc import UCSpider

def run():
    print("Dumping Storage...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.get("https://www.goindigo.in/")
        import time
        time.sleep(10)
        
        storage = driver.execute_script("""
            let ls = {};
            for (let i = 0; i < localStorage.length; i++) {
                let key = localStorage.key(i);
                ls[key] = localStorage.getItem(key);
            }
            let ss = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                let key = sessionStorage.key(i);
                ss[key] = sessionStorage.getItem(key);
            }
            return {localStorage: ls, sessionStorage: ss, cookie: document.cookie};
        """)
        
        with open("indigo_full_storage.json", "w", encoding="utf-8") as f:
            json.dump(storage, f, indent=2)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
