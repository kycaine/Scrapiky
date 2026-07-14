#!/usr/bin/env python3
import subprocess
import sys
import os
import threading

def run_backend():
    print("[Backend] Starting FastAPI server...")
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server")
    
    if os.name == 'nt':
        python_exe = os.path.join(backend_dir, ".venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join(backend_dir, ".venv", "bin", "python")
        
    if not os.path.exists(python_exe):
        print(f"[Backend] ERROR: Virtual environment not found at {python_exe}")
        print("[Backend] Please run the setup instructions in README.md first.")
        return
        
    subprocess.run([python_exe, "-m", "uvicorn", "server:app", "--reload"], cwd=backend_dir)

def run_frontend():
    print("[Frontend] Starting React development server...")
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")
    
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    subprocess.run([npm_cmd, "run", "dev"], cwd=frontend_dir)

if __name__ == "__main__":
    print("========================================")
    print("      Starting Scrapiky Local Dev       ")
    print("========================================")
    
    t1 = threading.Thread(target=run_backend)
    t2 = threading.Thread(target=run_frontend)
    
    t1.start()
    t2.start()
    
    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print("\nShutting down Scrapiky servers...")
