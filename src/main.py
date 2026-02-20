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
    find_base_expiries,
    find_call_and_put_from_dropdown,
    find_strike_from_base_expiry,
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
        app.state.METADATA[t] = {
            "strike": row["strike"],
            "type": "CE",
            "prev": Helper.history(t),
        }

    for _, row in df_pe.iterrows():
        t = row["instrument_token"]
        new_tokens.append(t)
        app.state.METADATA[t] = {
            "strike": row["strike"],
            "type": "PE",
            "prev": Helper.history(t),
        }
    return new_tokens


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # 1. Initialize symbols
        for kwargs in D_SYMBOL.values():
            dump_basename_from_exchange(kwargs["name"], kwargs["exchange"])

        # 2. Setup Global State Registry
        # METADATA stores: {token: {"strike": 26100, "type": "CE", "prev": 145.0}}
        app.state.SUBSCRIBED = {"main": [], "hedge": []}

        app.state.METADATA = {}
        kwargs = dict(
            base_expiry="BANKNIFTY (2026-02-24)",
            ce_start=60600,
            pe_start=60600,
            num_of_strikes=10,
        )

        new_tokens = update_metadata(kwargs)
        app.state.SUBSCRIBED["main"] = new_tokens
        app.state.SUBSCRIBED["hedge"] = new_tokens

        # 4. Initialize WebSocket Manager
        # We assign it to app.state.ws so the broadcaster can find it
        app.state.ws = Wsocket(Helper.api(), new_tokens)

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
            base_expiry=payload.get("base_expiry"),
            ce_start=int(payload.get("ce_start"), 0),
            pe_start=int(payload.get("pe_start"), 0),
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

        return {"status": "success", "side": side}
    except Exception as e:
        logging.error(f"Subscription Error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/")
async def get(request: Request):
    symbols = find_base_expiries()
    return templates.TemplateResponse(
        "index.html", {"request": request, "symbols": symbols}
    )


@app.get("/get-strikes/{base_expiry}")
async def get_strikes(base_expiry: str):
    try:
        return find_strike_from_base_expiry(base_expiry)
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

            payload = {
                "type": "UPDATE",
                "diff_rows": assemble_table_rows("main", ticks),
                "hedge_rows": assemble_table_rows("hedge", ticks),
            }

            await websocket.send_json(payload)
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
                "ce_diff_pct": f"{round((ce_diff / ce_m['prev']) * 100, 2)}%"
                if ce_m["prev"]
                else "0%",
                "pe_diff_pct": f"{round((pe_diff / pe_m['prev']) * 100, 2)}%"
                if pe_m["prev"]
                else "0%",
                "total_diff_pct": f"{round((total_diff / (ce_m['prev'] + pe_m['prev'])) * 100, 2)}%"
                if (ce_m["prev"] + pe_m["prev"])
                else "0%",
            }
        )
    return rows


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
