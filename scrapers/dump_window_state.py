import json
import time
from engine.spiders.base_uc import UCSpider

def run():
    print("Dumping Window State for IndiGo...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.get("https://www.goindigo.in/")
        time.sleep(10)
        
        # Dump any global variables that look like state
        state = driver.execute_script("""
            let state = {};
            for (let key in window) {
                if (key.toLowerCase().includes('state') || key.toLowerCase().includes('data') || key.toLowerCase().includes('config') || key.toLowerCase().includes('env') || key.toLowerCase().includes('auth')) {
                    try {
                        let val = window[key];
                        if (typeof val === 'object' && val !== null) {
                            state[key] = JSON.stringify(val).substring(0, 500);
                        } else if (typeof val === 'string') {
                            state[key] = val.substring(0, 500);
                        }
                    } catch(e) {}
                }
            }
            return state;
        """)
        
        with open("indigo_window_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            
        print("State dumped to indigo_window_state.json")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
