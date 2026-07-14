@echo off
echo ============================================================
echo Checking prerequisites for Scrapiky...
echo ============================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please download and install Python from: https://www.python.org/downloads/
    echo IMPORTANT: Make sure to check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not added to PATH.
    echo Please download and install Node.js from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo All prerequisites found! Starting setup...
echo.
python setup.py

pause
