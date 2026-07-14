# 🗺️ Scrapiky (Google Maps Harvester)

Scrapiky is a modern, elegant web application and scraper that automatically extracts business data from Google Maps. It features a full React frontend, a FastAPI WebSocket backend, anti-detection stealth scraping via Playwright, and real-time logging.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎨 **Elegant Interface** | Clean, modern UI built with React, Vite, and Tailwind-like styling. |
| 🕵️ **Anti-Detection** | Uses Playwright stealth techniques to bypass bot detection. |
| ⚡ **Real-time WebSockets** | Watch the scraping process live directly on your dashboard. |
| 🛡️ **Smart Filters** | Skip places without phones, websites, reviews, or low ratings (< 3.0). |
| 📦 **Instant CSV Export** | Download the harvested data neatly formatted in one click. |
| 🔐 **Firebase Auth** | Secure Google Login integration. |

---

## 📁 Project Structure

The project has been split into two independent parts to allow seamless deployment (e.g. Cloudflare Pages for Frontend, and a VPS for Backend).

- **`/pages`** : The React (Vite) frontend application.
- **`/server`** : The Python FastAPI backend and Playwright scraper logic.

---

## 🚀 Local Installation & Setup

We have created an automated setup script that works across all operating systems. Just ensure you have **Python 3.9+** and **Node.js** installed on your computer.

1. Open a terminal in the root folder of the project.
2. Run the setup script:
```bash
python setup.py
```
*This script will automatically create the virtual environment, install Python dependencies, install the Chromium browser for Playwright, and install all Node.js modules for the frontend.*

---

## 💻 How to Run (Cross-Platform)

We have provided a cross-platform Python launcher that will start both the Frontend and the Backend simultaneously!

From the root directory of the project, simply run:
```bash
python run.py
```
*(This script works automatically on Windows, macOS, and Linux).*

**Alternative (Manual Run):**
If you prefer running them separately:
- **Terminal 1 (Backend)**: `cd server && .venv/bin/uvicorn server:app --reload` (or `uvicorn server:app --reload` if venv is activated).
- **Terminal 2 (Frontend)**: `cd pages && npm run dev`

---

## 🌐 Deployment Guide

### Frontend (Cloudflare Pages)
1. Push this repository to GitHub.
2. Go to Cloudflare Pages and connect your repository.
3. Set the **Root directory** to `pages`.
4. Set the **Build command** to `npm run build`.
5. Set the **Build output directory** to `dist`.

### Backend (VPS / Render / DigitalOcean)
1. Host the `server` folder on any server that supports Python and can run headless Chrome (e.g., Ubuntu VPS).
2. Install Python, create a virtual environment, and install `requirements.txt` & `playwright`.
3. Run the server using `uvicorn server:app --host 0.0.0.0 --port 8000`.
4. Update the WebSocket URL inside `pages/src/App.jsx` to point to your new backend server IP/Domain.
