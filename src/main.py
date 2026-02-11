import asyncio
import random
from contextlib import asynccontextmanager

import uvicorn
from api import Helper
from constants import D_SYMBOL, logging
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from symbols import (
    dump_basename_from_exchange,
    find_base_expiries,
    find_call_and_put_from_dropdown,
    find_strike_from_base_expiry,
)
from wsocket import Wsocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        for kwargs in D_SYMBOL.values():
            # filter the json further by base nme
            dump_basename_from_exchange(kwargs["name"], kwargs["exchange"])

        # app state of subscribed tokens
        SUBSCRIBED = {"left": [], "right": []}
        # we need to accepts arguments from the dependant dropdown
        df_ce, df_pe = find_call_and_put_from_dropdown(
            base_expiry="BANKNIFTY (2026-02-24)",
            ce_start=60600,
            pe_start=60600,
            num_of_strikes=15,
        )
        SUBSCRIBED["left"] = df_ce["instrument_token"].to_list()
        SUBSCRIBED["left"].extend(df_pe["instrument_token"].to_list())
        SUBSCRIBED["right"] = SUBSCRIBED["left"]

        app.state.ws = Wsocket(Helper.api(), SUBSCRIBED["left"])
        app.state.SUBSCRIBED = SUBSCRIBED
        ticks = {}
        while not any(ticks):
            ticks = app.state.ws.ltp()
            __import__("time").sleep(5)
        else:
            print(ticks)
            logging.info("Login Successful - HAPPY TRADING")
            yield
    except Exception as e:
        logging.error(f"Startup login Error {e}")
        yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def get(request: Request):
    symbols = find_base_expiries()
    return templates.TemplateResponse(
        "index.html", {"request": request, "symbols": symbols}
    )


@app.get("/get-strikes/{base_expiry}")
async def get_strikes(base_expiry: str):
    """strike prices dependant drop down
    Returns a dictionary: {"ce": [list of strikes], "pe": [list of strikes]}
    """
    try:
        # This function should return the dict you described
        strikes_dict = find_strike_from_base_expiry(base_expiry)
        return strikes_dict
    except Exception as e:
        logging.error(f"Error fetching strikes: {e}")
        return {"ce": [], "pe": []}


async def unsub_and_sub(side, base_expiry, ce_start, pe_start, num_of_strikes):
    df_ce, df_pe = find_call_and_put_from_dropdown(
        base_expiry=base_expiry,
        ce_start=ce_start,
        pe_start=pe_start,
        num_of_strikes=num_of_strikes,
    )
    lst = df_ce["instrument_token"].to_list()
    lst.extend(df_pe["instrument_token"].to_list())

    stale_list = app.state.SUBSCRIBED[side]
    other_list = app.state.SUBSCRIBED["left" if side == "right" else "left"]
    unsubscribe = list(set(stale_list) - set(other_list))
    app.state.ws.unsubscribe(unsubscribe)

    app.state.ws.subscribe(lst)
    app.state.SUBSCRIBED[side] = lst


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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
