#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
#  run.sh  –  Google Maps Harvester Launcher
#  Automatically uses the pre-configured virtual environment.
#  Usage: ./run.sh --keyword "Cafe in Jakarta" --max 20
# ─────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment not found."
    echo "  Please run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/playwright install chromium"
    exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/scraper.py" "$@"
