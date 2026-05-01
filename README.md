# 🗺️ Google Maps Harvester

A Python script based on **Playwright** that automatically scrapes business data from Google Maps — featuring stealth mode, auto-scroll lazy-loading, CSV/JSON export, and optional AI analysis via Gemini.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🕵️ Anti-Detection | Uses `playwright-stealth` to hide bot signals (navigator, WebGL, canvas fingerprint). |
| 🖱️ Human Emulation | Random delays, mouse movements, and gradual scrolling. |
| 🔄 URL-First Strategy | Collects all place URLs first to ensure stability and avoid stale elements. |
| 📦 Data Extraction | Name, Rating, Review Count, Category, Address, Website, Phone. |
| 📁 Automatic Export | Saves to CSV (UTF-8 BOM for Excel) and JSON formats per session. |
| 🤖 Gemini Analysis | Optional AI analysis for business suitability (e.g., Work From Cafe). |
| 🛡️ Error Handling | Layered try-except blocks, navigation fallbacks, and item timeouts. |

---

## 🚀 Installation

```bash
# 1. Create virtual environment
python3 -m venv .venv

# 2. Install dependencies using the venv's pip
.venv/bin/pip install -r requirements.txt

# 3. Install Chromium browser for Playwright
.venv/bin/playwright install chromium

# 4. (Optional) Setup environment variables
cp .env.example .env
```

Edit `.env` and fill in the `GEMINI_API_KEY` if you wish to enable AI analysis.

---

## 🎮 Usage

```bash
# Activate venv first
source .venv/bin/activate

# Basic example – scrape 20 results (browser window visible)
./run.sh --keyword "Cafe in Jakarta" --max 20

# Scrape 50 results in headless mode (no browser window)
./run.sh --keyword "Coworking Bandung" --max 50 --headless

# Enable Gemini AI analysis
./run.sh --keyword "Cafe in Jakarta" --max 30 --gemini
```

### CLI Options

| Flag | Default | Description |
|---|---|---|
| `--keyword` / `-k` | *(required)* | Search keyword for Google Maps. |
| `--max` / `-m` | `20` | Maximum number of results to fetch. |
| `--headless` | `False` | Run browser without a visible window. |
| `--gemini` | `False` | Enable WFC analysis via Gemini AI. |
| `--output` / `-o` | `./output` | Output directory for CSV/JSON files. |

---

## 📂 Output Structure

```
output/
└── Cafe_in_Jakarta_20260501_102300.csv
└── Cafe_in_Jakarta_20260501_102300.json
```

### Data Columns

```
name | rating | review_count | category | address | website | phone | google_maps_url | wfc_analysis
```

---

## ⚠️ Disclaimer

This script is for research and personal business analysis purposes only. Always comply with [Google Maps Terms of Service](https://maps.google.com/help/terms_maps/).
