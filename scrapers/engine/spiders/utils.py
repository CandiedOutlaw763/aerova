import threading
import psutil

def safe_quit(driver, timeout=10):
    """
    Safely quit undetected_chromedriver on Windows.
    If driver.quit() hangs, forcefully kill the entire process tree.
    """
    def _quit():
        try:
            driver.quit()
        except Exception:
            pass

    t = threading.Thread(target=_quit, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        # quit() is hung — kill the process tree directly
        try:
            # uc.Chrome exposes the service process
            if hasattr(driver, 'service') and hasattr(driver.service, 'process') and driver.service.process:
                pid = driver.service.process.pid
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                parent.kill()
        except Exception:
            pass

def setup_cdp_limits(driver):
    """
    Raises CDP's buffer limits so Chrome holds onto response bodies longer,
    giving the scraper more slack against garbage collection.
    """
    try:
        driver.execute_cdp_cmd("Network.enable", {
            "maxTotalBufferSize": 100_000_000,
            "maxResourceBufferSize": 50_000_000
        })
    except Exception as e:
        print(f"Warning: Could not set CDP limits: {e}")
