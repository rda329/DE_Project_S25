import psutil
import platform

import platform
import psutil
import os

def kill_chrome():
    os_name = platform.system()
    chrome_names = {
        'Windows': 'chrome.exe',
        'Darwin': 'Google Chrome',  # macOS
        'Linux': 'chrome'  # or 'google-chrome' depending on the distro
    }
    
    target_name = chrome_names.get(os_name)
    if not target_name:
        print(f"Unsupported OS: {os_name}")
        return

    killed = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if target_name.lower() in proc.info['name'].lower():
                proc.kill()
                print(f"Closed process {proc.info['name']} with PID {proc.info['pid']}")
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Process may have ended or we don't have permissions

    if killed == 0:
        print("No Chrome processes found.")
    else:
        print(f"Killed {killed} Chrome processes.")