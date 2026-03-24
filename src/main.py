import asyncio
from contextlib import asynccontextmanager

import uvicorn

# Assuming these are your existing local modules
from api import Helper
from constants import D_SYMBOL, logging
from fastapi import Body, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from symbols import (
    dump_basename_from_exchange,
    find_base,
    # find_base_expiries,
    find_expiry_from_base,
    find_strike_from_base_expiry,
    find_call_and_put_from_dropdown,
)
from wsocket import Wsocket


def update_metadata(kwargs):
    # 3. Initial Default Subscription (e.g., BANKNIFTY)
    df_ce, df_pe = find_call_and_put_from_dropdown(**kwargs)

    # Populate initial metadata and tokens
    # df also contains tradingsymbol, expiry
    new_tokens = []
    for _, row in df_ce.iterrows():
        t = row["instrument_token"]
        new_tokens.append(t)
        hist = Helper.history(t)
        if hist > 0:
            app.state.METADATA[t] = {
                "strike": row["strike"],
                "type": "CE",
                "prev": hist,
            }

    for _, row in df_pe.iterrows():
        t = row["instrument_token"]
        new_tokens.append(t)
        hist = Helper.history(t)
        if hist > 0:
            app.state.METADATA[t] = {
                "strike": row["strike"],
                "type": "PE",
                "prev": hist,
            }
    return new_tokens


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.sleep(10)
        # 1. Initialize symbols
        for kwargs in D_SYMBOL.values():
            dump_basename_from_exchange(kwargs["name"], kwargs["exchange"])

        # 2. Setup Global State Registry
        # METADATA stores: {token: {"strike": 26100, "type": "CE", "prev": 145.0}}
        app.state.SUBSCRIBED = {"main": [], "hedge": []}

        app.state.METADATA = {}

        app.state.checkbox = {"main": 1, "hedge": 1}

        # 4. Initialize WebSocket Manager
        # We assign it to app.state.ws so the broadcaster can find it
        index_tokens = [256265, 265, 260105]  # NIFTY, SENSEX, BANKNIFTY
        app.state.ws = Wsocket(Helper.api(), index_tokens)

        # Wait for first ticks to ensure app.state.ws.ltp() isn't empty
        while not any(app.state.ws.ltp()):
            await asyncio.sleep(1)

        logging.info("Login Successful - HAPPY TRADING")
        yield
    except Exception as e:
        logging.error(f"Startup Error: {e}")
        yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.post("/update-subscription")
async def update_subscription(payload: dict = Body(...)):
    try:
        side = payload.get("side")
        kwargs = dict(
            basename=payload.get("basename"),
            expiry=payload.get("expiry"),
            ce_start=int(payload.get("ce_start")),
            pe_start=int(payload.get("pe_start")),
            num_of_strikes=int(payload.get("num_of_strikes")),
        )
        new_tokens = update_metadata(kwargs)
        # Handle Subscriptions
        stale_list = app.state.SUBSCRIBED[side]
        other_side = "hedge" if side == "main" else "main"
        other_list = app.state.SUBSCRIBED[other_side]

        # Only unsubscribe if the other side isn't using the token
        unsubscribe = list(set(stale_list) - set(other_list))

        if unsubscribe:
            app.state.ws.unsubscribe(unsubscribe)  #

        # 4. Subscribe to new tokens
        app.state.ws.subscribe(new_tokens)  #

        # 5. Update global state for next comparison
        app.state.SUBSCRIBED[side] = new_tokens

        # 6 set checkbox state
        app.state.checkbox[side] = 1

        return {"status": "success", "side": side}
    except Exception as e:
        logging.error(f"Subscription Error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/")
async def get(request: Request):
    symbols = find_base()
    return templates.TemplateResponse(
        "index.html", {"request": request, "symbols": symbols}
    )


@app.get("/get-expiries/{basename}")
async def get_expiries(basename: str):
    try:
        return find_expiry_from_base(basename)
    except Exception as e:
        logging.error(f"Error fetching strikes: {e}")
        return []


@app.get("/get-strikes/{basename}/{expiry}")
async def get_strikes(basename: str, expiry: str):
    try:
        return find_strike_from_base_expiry(basename, expiry)
    except Exception as e:
        logging.error(f"Error fetching strikes: {e}")
        return {"CE": [], "PE": []}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Broadcaster handles all table updates dynamically
    feed_task = asyncio.create_task(market_broadcaster(websocket))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        feed_task.cancel()


async def market_broadcaster(websocket: WebSocket):
    """
    Look up tokens from SUBSCRIBED, find their LTP from app.state.ws,
    and send paired row data to the UI.
    """
    try:
        while True:
            # Safely get current LTP cache
            ticks = app.state.ws.ltp() if hasattr(app.state, "ws") else {}

            if ticks:
                payload = {
                    "type": "UPDATE",
                    "diff_rows": assemble_table_rows("main", ticks),
                    "hedge_rows": assemble_table_rows("hedge", ticks),
                    "main_fresh": app.state.checkbox["main"],
                    "hedge_fresh": app.state.checkbox["hedge"],
                }

                await websocket.send_json(payload)
                app.state.checkbox["main"] = 0
                app.state.checkbox["hedge"] = 0
            await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"Broadcaster Error: {e}")


def assemble_table_rows(side, ticks):
    """
    Pairs CE and PE tokens correctly.
    Assumes the tokens list is: [CE1, CE2... PE1, PE2...]
    """
    rows = []
    tokens = app.state.SUBSCRIBED.get(side, [])

    if not tokens:
        return rows

    if not ticks:
        print(f"DEBUG: Have {len(tokens)} tokens for {side} but 0 ticks received yet.")

    # Calculate the midpoint (half are CE, half are PE)
    half = len(tokens) // 2

    for i in range(half):
        ce_t = tokens[i]  # CE token
        pe_t = tokens[i + half]  # Corresponding PE token

        ce_m = app.state.METADATA.get(ce_t)
        pe_m = app.state.METADATA.get(pe_t)

        if not ce_m or not pe_m:
            continue

        # 1. Fetch live LTP from the ws.ltp() dictionary
        # Fallback to metadata 'prev' if the token hasn't ticked yet
        c_ce = ticks.get(ce_t, ce_m["prev"])
        c_pe = ticks.get(pe_t, pe_m["prev"])

        # 2. Calculate Diffs
        ce_diff = round(c_ce - ce_m["prev"], 2)
        pe_diff = round(c_pe - pe_m["prev"], 2)
        total_diff = round(ce_diff + pe_diff, 2)

        # 3. Build row for the frontend renderDashboard()
        rows.append(
            {
                "ce_strike": ce_m["strike"],
                "pe_strike": pe_m["strike"],
                "curr_ce": c_ce,
                "curr_pe": c_pe,
                "prev_ce": ce_m["prev"],
                "prev_pe": pe_m["prev"],
                "ce_diff": ce_diff,
                "pe_diff": pe_diff,
                "total_diff": total_diff,
                "ce_diff_pct": round((ce_diff / ce_m["prev"]) * 100, 2)
                if ce_m["prev"]
                else 0,
                "pe_diff_pct": round((pe_diff / pe_m["prev"]) * 100, 2)
                if pe_m["prev"]
                else 0,
                "total_diff_pct": round(
                    (total_diff / (ce_m["prev"] + pe_m["prev"])) * 100, 2
                )
                if (ce_m["prev"] + pe_m["prev"])
                else 0,
            }
        )
    return rows


if __name__ == "__main__":
    try:
        # reload=False is better for production/stable testing to avoid double-triggers
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        # This catch happens when you press Ctrl+C
        logging.info("Power-Option Server stopped by user (Ctrl+C).")
    except Exception as e:
        # Use an f-string or comma to properly log the error object
        logging.error(f"Error in main: {e}")
    finally:
        logging.info("Cleaning up resources... Shutdown complete.")
