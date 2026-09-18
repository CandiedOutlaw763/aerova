import subprocess
import sys
import os
import time
from show_db import show_results

def main():
    print("Starting Orchestrator for all 11 sites...")
    
    # Run orchestrator synchronously
    # We use -u to prevent buffering
    process = subprocess.Popen(
        [sys.executable, "-u", "engine/orchestrator.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd="c:/Users/siddh/OneDrive/Desktop/sih 2026/scrapers"
    )
    
    # Read output live so we don't block
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
        
    process.stdout.close()
    process.wait()
    
    print("\n\n--- SCRAPING COMPLETED ---")
    print("Now querying flights database...\n")
    
    show_results()

if __name__ == "__main__":
    main()
