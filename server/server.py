import sys
import os
import asyncio
import json
import subprocess
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from scraper import scrape
from logger import add_ws_callback, remove_ws_callback

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path.home() / ".scrapiky_browsers")

def install_browser():
    try:
        from playwright._impl._driver import compute_driver_executable, get_driver_env
        driver_executable = compute_driver_executable()
        env = get_driver_env()
        
        if isinstance(driver_executable, tuple):
            cmd = list(driver_executable) + ["install", "chromium"]
        else:
            cmd = [str(driver_executable), "install", "chromium"]
            
        print("[System] Checking/Installing Chromium browser. This may take a minute on first run...")
        subprocess.check_call(cmd, env=env, stdout=subprocess.DEVNULL)
        print("[System] Chromium browser is ready.")
    except Exception as e:
        print(f"[ERROR] Failed to install browser: {e}")

install_browser()

app = FastAPI(title="Scrapiky API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/scrape")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    def log_callback(msg: str):
        # Fire-and-forget sending of log msg
        try:
            asyncio.create_task(websocket.send_json({"type": "log", "data": msg}))
        except Exception:
            pass

    add_ws_callback(log_callback)
    try:
        data = await websocket.receive_text()
        req = json.loads(data)
        
        keyword = req.get("keyword", "")
        max_results = req.get("max_results", 10)
        filters = {
            "FILTER_NO_PHONE": req.get("filter_no_phone", False),
            "FILTER_HAS_WEBSITE": req.get("filter_has_website", False),
            "FILTER_NO_REVIEW": req.get("filter_no_review", False),
            "FILTER_LOW_RATING": req.get("filter_low_rating", False),
        }
        
        if not keyword:
            await websocket.send_json({"type": "error", "data": "Keyword is required"})
            return

        await websocket.send_json({"type": "status", "data": "Scraping started..."})
        
        records, csv_path, json_path = await scrape(
            keyword=keyword,
            max_results=max_results,
            headless=True,
            output_dir=Path("output"),
            filters=filters
        )
        
        import dataclasses
        records_dict = [dataclasses.asdict(r) for r in records]
        await websocket.send_json({
            "type": "result",
            "data": records_dict
        })
        
        await websocket.send_json({
            "type": "status",
            "data": f"Scraping completed. Found {len(records)} records."
        })
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
    finally:
        remove_ws_callback(log_callback)

if getattr(sys, 'frozen', False):
    base_dir = Path(sys._MEIPASS)
else:
    base_dir = Path(__file__).parent.parent

dist_dir = base_dir / "pages" / "dist"

if dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        path = dist_dir / full_path
        if path.exists() and path.is_file():
            return FileResponse(str(path))
        return FileResponse(str(dist_dir / "index.html"))

if __name__ == "__main__":
    import uvicorn
    import threading
    import webbrowser
    import time
    
    def open_browser():
        time.sleep(3)
        print("[System] Opening browser at http://localhost:8000 ...")
        webbrowser.open("http://localhost:8000")
        
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
