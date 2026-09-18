import time
from engine.spiders.base_uc import UCSpider

def run():
    print("Exploring SpiceJet...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.get("https://www.spicejet.com/")
        time.sleep(15)
        
        driver.save_screenshot("spicejet_home.png")
        
        # Try to find common input fields
        inputs = driver.execute_script("""
            let inps = document.querySelectorAll('input');
            let data = [];
            for(let i of inps) {
                let rect = i.getBoundingClientRect();
                if(rect.width > 0 && rect.height > 0) {
                    data.push({
                        id: i.id,
                        className: i.className,
                        placeholder: i.placeholder,
                        value: i.value,
                        type: i.type,
                        name: i.name
                    });
                }
            }
            return data;
        """)
        print("Visible Inputs found:", inputs)
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
