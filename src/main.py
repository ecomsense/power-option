from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import random

from constants import O_SETG, logging
from symbols import dump, Symbols
from utils import dict_from_yml
from api import Helper



"""
# Exact data from your original main.py
STRIKE_DATA = [
    {"ce_strike": 26100, "pe_strike": 26100, "prev_ce": 145.00, "prev_pe": 3.25},
    {"ce_strike": 26150, "pe_strike": 26050, "prev_ce": 110.85, "prev_pe": 3.70},
    {"ce_strike": 26200, "pe_strike": 26000, "prev_ce": 81.60, "prev_pe": 4.40},
    {"ce_strike": 26250, "pe_strike": 25950, "prev_ce": 56.95, "prev_pe": 5.05},
    {"ce_strike": 26300, "pe_strike": 25900, "prev_ce": 37.85, "prev_pe": 5.90},
    {"ce_strike": 26350, "pe_strike": 25850, "prev_ce": 23.80, "prev_pe": 7.50},
    {"ce_strike": 26400, "pe_strike": 25800, "prev_ce": 14.55, "prev_pe": 10.30},
    {"ce_strike": 26450, "pe_strike": 25750, "prev_ce": 8.95, "prev_pe": 13.95},
    {"ce_strike": 26500, "pe_strike": 25700, "prev_ce": 5.75, "prev_pe": 19.85},
    {"ce_strike": 26550, "pe_strike": 25650, "prev_ce": 3.80, "prev_pe": 28.00},
    {"ce_strike": 26600, "pe_strike": 25600, "prev_ce": 2.85, "prev_pe": 39.65},
]


async def mock_market_feed(websocket: WebSocket):
    try:
        while True:
            updates = []
            for item in STRIKE_DATA:
                curr_ce = round(item["prev_ce"] * (1 + random.uniform(-0.05, 0.05)), 2)
                curr_pe = round(item["prev_pe"] * (1 + random.uniform(-0.05, 0.05)), 2)
                ce_diff = round(curr_ce - item["prev_ce"], 2)
                pe_diff = round(curr_pe - item["prev_pe"], 2)
                total_diff = round(ce_diff + pe_diff, 2)

                updates.append(
                    {
                        "total_diff": total_diff,
                        "ce_diff_pct": f"{round((ce_diff / item['prev_ce']) * 100, 2)}%",
                        "ce_diff": ce_diff,
                        "curr_ce": curr_ce,
                        "prev_ce": item["prev_ce"],
                        "ce_strike": item["ce_strike"],
                        "pe_strike": item["pe_strike"],
                        "prev_pe": item["prev_pe"],
                        "curr_pe": curr_pe,
                        "pe_diff": pe_diff,
                        "pe_diff_pct": f"{round((pe_diff / item['prev_pe']) * 100, 2)}%",
                        "total_diff_pct": f"{round((total_diff / (item['prev_ce'] + item['prev_pe'])) * 100, 2)}%",
                    }
                )
            # SENDING BOTH KEYS TO FRONTEND
            await websocket.send_json(
                {"type": "UPDATE", "diff_rows": updates, "hedge_rows": updates}
            )
            await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"Feed error: {e}")
"""

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def subscribe(websocket: WebSocket):


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    feed_task = asyncio.create_task(mock_market_feed(websocket))
    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Command received: {data}")
    except WebSocketDisconnect:
        feed_task.cancel()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        dump()
        app.state.symbol_settings = dict_from_yml("name", O_SETG["base"])
        app.state.api = Helper.api()
        logging.info("Login Successful - HAPPY TRADING")
        yield
    except Exception as e:
        logging.error(f"Startup login Error {e}")
        yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
