import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from constants import D_SYMBOL, yml_to_obj
from symbols import (
    dump_basename_from_exchange,
    find_call_and_put_from_dropdown,
    find_expiry_from_base,
    find_strike_from_base_expiry,
)
from state import _logic_state, get_logic_state
from webhook import send_to_webhook_async

logger = __import__('logging').getLogger(__name__)


def load_template(name: str) -> str:
    template_path = Path(__file__).parent.parent / "templates" / f"{name}.html"
    return template_path.read_text()


class OrderRequest(BaseModel):
    orders: List[str]
    quantity: int
    order_code: str
    tag: str


class SubscriptionRequest(BaseModel):
    side: str
    basename: str
    expiry: str
    ce_start: int
    pe_start: int
    num_of_strikes: int


class SettingsPayload(BaseModel):
    webhook_url: str
    tag: str = "poweroption"
    timeout: int = 30
    log_level: int = 20
    log_show: bool = True


def _get_symbols() -> Dict[str, Any]:
    return D_SYMBOL


def _validate_broker() -> bool:
    from api import Helper
    return Helper.api() is not None


def _initialize_symbols():
    for kwargs in D_SYMBOL.values():
        dump_basename_from_exchange(kwargs["name"], kwargs["exchange"])


def _update_metadata(side: str, kwargs: dict, app_data: dict) -> List[int]:
    df_ce, df_pe = find_call_and_put_from_dropdown(**kwargs)

    expiry_str = kwargs.get("expiry", "")
    expiry_formatted = ""
    if expiry_str:
        try:
            dt = datetime.strptime(expiry_str, "%Y-%m-%d")
            expiry_formatted = dt.strftime("%y%m%d")
        except:
            expiry_formatted = expiry_str.replace("-", "")[:6]

    basename = kwargs.get("basename")

    new_tokens = []
    metadata = app_data.get("metadata", {})
    symbol_lookup = app_data.get("symbol_lookup", {})

    for _, row in df_ce.iterrows():
        t = row["instrument_token"]
        new_tokens.append(t)
        from api import Helper
        hist = Helper.history(t)
        if hist > 0:
            strike = row.get("strike", 0)
            symbol = f"{basename}{expiry_formatted}{strike:05d}CE"
            metadata[t] = {
                "strike": strike,
                "type": "CE",
                "prev": hist,
                "symbol": symbol,
            }
            symbol_lookup[(strike, "CE")] = symbol

    for _, row in df_pe.iterrows():
        t = row["instrument_token"]
        new_tokens.append(t)
        from api import Helper
        hist = Helper.history(t)
        if hist > 0:
            strike = row.get("strike", 0)
            symbol = f"{basename}{expiry_formatted}{strike:05d}PE"
            metadata[t] = {
                "strike": strike,
                "type": "PE",
                "prev": hist,
                "symbol": symbol,
            }
            symbol_lookup[(strike, "PE")] = symbol

    app_data["metadata"] = metadata
    app_data["symbol_lookup"] = symbol_lookup
    return new_tokens


def on_start(startup_data: dict, app_data: dict):
    logger.info(f"[LIFECYCLE] Starting logic for account: {startup_data.get('account_id', 'UNKNOWN')}")

    app_data["subscribed"] = {"main": [], "hedge": []}
    app_data["metadata"] = {}
    app_data["symbol_lookup"] = {}
    app_data["checkbox"] = {"main": 1, "hedge": 1}

    _initialize_symbols()

    from api import Helper
    from wsocket import Wsocket

    broker_api = Helper.api()
    if broker_api is not None:
        app_data["ws"] = Wsocket(broker_api, [256265, 265, 260105])
        logger.info("WebSocket connected successfully")
    else:
        app_data["ws"] = None
        logger.warning("Broker not authenticated - WebSocket disabled")


def on_stop(app_data: dict):
    logger.info(f"[LIFECYCLE] on_stop called")
    if app_data.get("ws"):
        app_data["ws"] = None


async def start_logic():
    if _logic_state.is_running():
        return {"status": "already_running", "message": "Logic app is already running"}

    session_id = f"SES_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6].upper()}"
    logger.info(f"New broker session: {session_id}")

    _logic_state.startup_data = {
        "account_id": "ACC_" + str(uuid.uuid4())[:6].upper(),
        "session_id": session_id,
        "logged_in_at": datetime.now().isoformat(),
    }

    _logic_state.app_data = {
        "positions": {},
        "orders": [],
        "market_cache": {},
        "total_pnl": 0.0,
        "trade_count": 0,
        "last_update": None,
    }

    on_start(_logic_state.startup_data, _logic_state.app_data)

    _logic_state.running = True
    _logic_state.started_at = datetime.now()

    return {
        "status": "started",
        "message": "Logic app started",
        "session_id": session_id,
    }


async def stop_logic():
    if not _logic_state.is_running():
        return {"status": "already_stopped", "message": "Logic app is not running"}

    on_stop(_logic_state.app_data)

    _logic_state.running = False

    if _logic_state.app_data:
        _logic_state.app_data.clear()
        _logic_state.app_data = None

    _logic_state.started_at = None

    return {"status": "stopped", "message": "Logic app stopped gracefully"}


def get_status():
    app_data = _logic_state.app_data
    return {
        "running": _logic_state.is_running(),
        "started_at": _logic_state.started_at.isoformat() if _logic_state.started_at else None,
        "account_id": _logic_state.startup_data.get("account_id") if _logic_state.startup_data else None,
        "session_id": _logic_state.startup_data.get("session_id") if _logic_state.startup_data else None,
    }


def create_logic_router() -> APIRouter:
    router = APIRouter(tags=["logic"])

    @router.get("/status")
    async def status():
        return get_status()

    @router.post("/start")
    async def start():
        return await start_logic()

    @router.post("/stop")
    async def stop():
        return await stop_logic()

    @router.post("/order_place")
    async def place_order(payload: OrderRequest):
        from fastapi import FastAPI
        from fastapi import Request as FastAPIRequest

        app_data = _logic_state.app_data
        if not app_data:
            raise HTTPException(status_code=503, detail="Logic app not running")

        try:
            from constants import logging as app_logging

            parts = []
            for order_id in payload.orders:
                parts_id = order_id.split("-")
                if len(parts_id) >= 4:
                    option_type = parts_id[2].upper()
                    strike = int(parts_id[3])
                    symbol = app_data.get("symbol_lookup", {}).get((strike, option_type), "UNKNOWN")
                    stag = "MAIN" if payload.tag.lower() == "main" else "HEDGE"
                    parts.append(f"TYPE:{payload.order_code},SYMBOL:{symbol},STAG:{stag},QTY:{payload.quantity}")

            msg = ";".join(parts)

            await send_to_webhook_async(msg)
            logger.info(f"Entry: {msg}")

            return {"status": "success", "order_type": payload.order_code}
        except Exception as e:
            logger.error(f"Order Error: {e}")
            return {"status": "error", "message": str(e)}

    @router.post("/order_place_one")
    async def place_order_one(payload: dict):
        app_data = _logic_state.app_data
        if not app_data:
            raise HTTPException(status_code=503, detail="Logic app not running")

        try:
            from constants import logging as app_logging

            order_id = payload.get("trading_symbol")
            quantity = payload.get("quantity")
            order_type = payload.get("order_type")
            table_tag = payload.get("tag", "main")

            stag = "MAIN" if table_tag.lower() == "main" else "HEDGE"

            parts_id = order_id.split("-")
            if len(parts_id) >= 4:
                option_type = parts_id[2].upper()
                strike = int(parts_id[3])
                symbol = app_data.get("symbol_lookup", {}).get((strike, option_type), "UNKNOWN")
            else:
                symbol = "UNKNOWN"

            msg = f"TYPE:{order_type},SYMBOL:{symbol},STAG:{stag},QTY:{quantity}"
            await send_to_webhook_async(msg)
            logger.info(f"Entry One: {msg}")

            return {"status": "success", "order_type": order_type, "symbol": symbol}
        except Exception as e:
            logger.error(f"Order One Error: {e}")
            return {"status": "error", "message": str(e)}

    @router.post("/update-subscription")
    async def update_subscription(payload: SubscriptionRequest):
        app_data = _logic_state.app_data
        if not app_data:
            raise HTTPException(status_code=503, detail="Logic app not running")

        try:
            kwargs = dict(
                basename=payload.basename,
                expiry=payload.expiry,
                ce_start=payload.ce_start,
                pe_start=payload.pe_start,
                num_of_strikes=payload.num_of_strikes,
            )
            new_tokens = _update_metadata(payload.side, kwargs, app_data)

            ws = app_data.get("ws")
            if ws is None:
                return {"status": "error", "message": "Broker not authenticated"}

            stale_list = app_data.get("subscribed", {}).get(payload.side, [])
            other_side = "hedge" if payload.side == "main" else "main"
            other_list = app_data.get("subscribed", {}).get(other_side, [])
            unsubscribe = list(set(stale_list) - set(other_list))

            if unsubscribe:
                ws.unsubscribe(unsubscribe)

            ws.subscribe(new_tokens)
            app_data["subscribed"][payload.side] = new_tokens
            app_data["checkbox"][payload.side] = 1

            return {"status": "success", "side": payload.side}
        except Exception as e:
            logger.error(f"Subscription Error: {e}")
            return {"status": "error", "message": str(e)}

    @router.get("/symbols")
    async def get_symbols():
        return list(D_SYMBOL.keys())

    @router.get("/expiries/{basename}")
    async def get_expiries(basename: str):
        try:
            return find_expiry_from_base(basename)
        except Exception as e:
            logger.error(f"Error fetching expiries: {e}")
            return []

    @router.get("/strikes/{basename}/{expiry}")
    async def get_strikes(basename: str, expiry: str):
        try:
            return find_strike_from_base_expiry(basename, expiry)
        except Exception as e:
            logger.error(f"Error fetching strikes: {e}")
            return {"CE": [], "PE": []}

    @router.get("/settings")
    async def get_settings():
        try:
            import yaml
            with open("../data/settings.yml", "r") as f:
                settings = yaml.safe_load(f)
            return settings
        except Exception as e:
            logger.error(f"Error reading settings: {e}")
            return {"status": "error", "message": str(e)}

    @router.post("/settings")
    async def update_settings(payload: SettingsPayload):
        try:
            import yaml
            settings_path = "../data/settings.yml"

            new_settings = {
                "webhook_url": payload.webhook_url,
                "tag": payload.tag,
                "timeout": payload.timeout,
                "log": {
                    "show": payload.log_show,
                    "level": payload.log_level,
                }
            }

            with open(settings_path, "w") as f:
                yaml.dump(new_settings, f)

            logger.info("Settings saved")
            return {"status": "success", "message": "Settings saved"}
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return {"status": "error", "message": str(e)}

    @router.get("/trading-status")
    async def get_trading_status():
        from datetime import datetime, timedelta

        now = datetime.now()
        is_trading = _logic_state.is_running()

        market_start = now.replace(hour=9, minute=14, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=31, second=0, microsecond=0)

        if now.weekday() >= 5:
            days_until_monday = 7 - now.weekday()
            market_start += timedelta(days=days_until_monday)
            market_end += timedelta(days=days_until_monday)
        elif now < market_start:
            pass
        elif now >= market_end:
            market_start += timedelta(days=1)
            market_end += timedelta(days=1)
            while market_start.weekday() >= 5:
                market_start += timedelta(days=1)
                market_end += timedelta(days=1)

        next_open = market_start if now < market_start else market_start + timedelta(days=1)
        next_close = market_end if now < market_end else market_end + timedelta(days=1)

        if is_trading:
            target = next_close
            label = "Market closes in"
        else:
            target = next_open
            label = "Market opens in"

        remaining = target - now
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60

        return {
            "trading_active": is_trading,
            "countdown_label": label,
            "countdown_hours": hours,
            "countdown_minutes": minutes,
        }

    @router.post("/reset-all")
    async def reset_all():
        _logic_state.startup_data = None
        _logic_state.reset()
        logger.info("Session reset complete")
        return {"status": "reset_all_done"}

    return router
