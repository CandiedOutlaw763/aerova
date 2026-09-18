import time
from selenium import webdriver

def run():
    print("Testing SpiceJet Search Button...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.spicejet.com/")
        time.sleep(10)
        
        button_info = driver.execute_script("""
            let els = document.querySelectorAll('*');
            let res = [];
            for(let el of els) {
                if(el.innerText && el.innerText.trim() === 'Search Flight') {
                    res.push({
                        tag: el.tagName,
                        className: el.className,
                        testId: el.getAttribute('data-testid')
                    });
                }
            }
            return res;
        """)
        print("Search Flight elements:", button_info)
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
