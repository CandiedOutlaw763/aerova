import time
from engine.spiders.base_uc import UCSpider

def run():
    print("Dumping form elements for AIX...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.get("https://www.airindiaexpress.com/")
        time.sleep(10)
        
        # Dump the entire flight search form wrapper
        form_html = driver.execute_script("""
            let form = document.querySelector('.flight-search-widget') || document.querySelector('.flight-search');
            if (form) return form.outerHTML;
            // Or try to find by some known inner text
            let els = document.querySelectorAll('div');
            for(let el of els) {
                if(el.innerText && el.innerText.includes('Flight Search') && el.innerText.includes('Manage Booking') && el.innerText.includes('Check-in')) {
                    // Try to find the closest wrapper
                    return el.parentElement.parentElement.outerHTML;
                }
            }
            return document.body.innerHTML;
        """)
        
        with open('aix_form_dump.html', 'w', encoding='utf-8') as f:
            f.write(form_html)
            
        print("Dumped to aix_form_dump.html")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
