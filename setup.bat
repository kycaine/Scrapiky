@echo off
echo ============================================================
echo Checking prerequisites for Scrapiky...
echo ============================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python is not installed or not in PATH.
    echo Attempting to install Python automatically...
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] Auto-installation failed.
        echo Please download and install Python from: https://www.python.org/downloads/
        echo IMPORTANT: Make sure to check the box "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    echo ============================================================
    echo [SUCCESS] Python has been installed!
    echo IMPORTANT: Please CLOSE this window and double-click setup.bat again so the new PATH changes take effect.
    echo ============================================================
    pause
    exit /b 0
)

:: Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Node.js is not installed or not in PATH.
    echo Attempting to install Node.js automatically...
    winget install -e --id OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] Auto-installation failed.
        echo Please download and install Node.js from: https://nodejs.org/
        pause
        exit /b 1
    )
    echo ============================================================
    echo [SUCCESS] Node.js has been installed!
    echo IMPORTANT: Please CLOSE this window and double-click setup.bat again so the new PATH changes take effect.
    echo ============================================================
    pause
    exit /b 0
)

echo All prerequisites found! Starting setup...
echo.
python setup.py

pause
