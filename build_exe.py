import sys
import os
import subprocess
from pathlib import Path

def main():
    root_dir = Path(__file__).parent.absolute()
    server_dir = root_dir / "server"
    pages_dir = root_dir / "pages"
    
    # 1. Build React frontend
    print("========================================")
    print("1. Building React Frontend...")
    print("========================================")
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    subprocess.check_call([npm_cmd, "run", "build"], cwd=str(pages_dir))
    
    # 2. Install PyInstaller
    print("========================================")
    print("2. Ensuring PyInstaller is installed...")
    print("========================================")
    # Ensure we use the venv pip if possible
    venv_python = server_dir / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable
    
    subprocess.check_call([python_cmd, "-m", "pip", "install", "pyinstaller"], cwd=str(server_dir))
    
    # 3. Build EXE
    print("========================================")
    print("3. Building Standalone Executable...")
    print("========================================")
    sep = ";" if os.name == "nt" else ":"
    data_arg = f"../pages/dist{sep}pages/dist"
    
    cmd = [
        python_cmd, "-m", "PyInstaller",
        "--name", "Scrapiky",
        "--onefile",
        "--add-data", data_arg,
        "server.py"
    ]
    subprocess.check_call(cmd, cwd=str(server_dir))
    
    print("========================================")
    print(f"BUILD COMPLETE! 🎉")
    print(f"Your executable is located in: {server_dir / 'dist'}")
    print("========================================")

if __name__ == "__main__":
    main()
