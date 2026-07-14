#!/usr/bin/env python3
import os
import sys
import subprocess
import venv

def print_header(msg):
    print(f"\n{'='*60}\n>> {msg}\n{'='*60}")

def run_cmd(cmd, cwd=None, error_msg="Command failed"):
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd, cwd=cwd)
    except subprocess.CalledProcessError:
        print(f"\n[ERROR] {error_msg}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[ERROR] Command not found: {cmd[0]}")
        print("Please ensure it is installed and added to your system PATH.")
        sys.exit(1)

def setup_backend():
    print_header("Setting up Backend (Python FastAPI & Playwright)")
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server")
    venv_dir = os.path.join(backend_dir, ".venv")
    
    print("1. Creating Python Virtual Environment...")
    if not os.path.exists(venv_dir):
        venv.create(venv_dir, with_pip=True)
        print("Virtual environment created successfully.")
    else:
        print("Virtual environment already exists. Skipping.")
        
    if os.name == 'nt':
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        playwright_exe = os.path.join(venv_dir, "Scripts", "playwright.exe")
    else:
        python_exe = os.path.join(venv_dir, "bin", "python")
        pip_exe = os.path.join(venv_dir, "bin", "pip")
        playwright_exe = os.path.join(venv_dir, "bin", "playwright")
        
    print("\n2. Upgrading pip...")
    run_cmd([python_exe, "-m", "pip", "install", "--upgrade", "pip"], cwd=backend_dir)
    
    print("\n3. Installing Python dependencies...")
    run_cmd([pip_exe, "install", "-r", "requirements.txt"], cwd=backend_dir)
    
    print("\n4. Installing Playwright Chromium browser...")
    run_cmd([playwright_exe, "install", "chromium"], cwd=backend_dir)
    print("Backend setup complete!")

def setup_frontend():
    print_header("Setting up Frontend (React Node.js)")
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")
    
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    
    print("1. Installing NPM dependencies (this might take a minute)...")
    run_cmd([npm_cmd, "install"], cwd=frontend_dir, error_msg="Failed to install Node modules. Please ensure Node.js and NPM are installed on your computer.")
    print("Frontend setup complete!")

if __name__ == "__main__":
    print_header("Welcome to the Scrapiky Automated Setup Script!")
    print("This script will install all necessary dependencies for both the frontend and backend.")
    print("It works automatically on Windows, Mac, and Linux.")
    
    setup_backend()
    setup_frontend()
    
    print_header("ALL SET UP SUCCESSFULLY! 🎉")
    print("You can now start the application by running:")
    print("    python run.py")
    print("\nEnjoy using Scrapiky!")
