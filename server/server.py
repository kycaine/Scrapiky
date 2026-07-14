import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from scraper import scrape
from logger import add_ws_callback, remove_ws_callback

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
