#!/bin/bash
echo "Starting Scrapiky..."
if command -v python3 &>/dev/null; then
    python3 run.py
else
    python run.py
fi
