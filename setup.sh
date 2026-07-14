#!/bin/bash

echo "============================================================"
echo "Checking prerequisites for Scrapiky..."
echo "============================================================"

# Check for Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python is not installed."
    echo "Please download and install Python from: https://www.python.org/downloads/"
    echo "Or use your package manager (e.g., sudo apt install python3, brew install python)"
    exit 1
fi

# Check for Node.js
if ! command -v node &>/dev/null; then
    echo "[ERROR] Node.js is not installed."
    echo "Please download and install Node.js from: https://nodejs.org/"
    echo "Or use your package manager (e.g., sudo apt install nodejs, brew install node)"
    exit 1
fi

echo "All prerequisites found! Starting setup..."
echo ""
$PYTHON_CMD setup.py
