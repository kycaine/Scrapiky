import os
from pathlib import Path
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path.home() / ".scrapiky_browsers")

try:
    from playwright._impl._driver import compute_driver_executable, get_driver_env
    import subprocess
    driver_executable = compute_driver_executable()
    env = get_driver_env()
    print("Driver:", driver_executable)
    print("Running install...")
    
    if isinstance(driver_executable, tuple):
        cmd = list(driver_executable) + ["install", "chromium"]
    else:
        cmd = [str(driver_executable), "install", "chromium"]
        
    subprocess.check_call(cmd, env=env)
    print("Success")
except Exception as e:
    print("Error:", e)
