import asyncio
import gc
import logging
import os
import signal
import sys
from base64 import b64decode
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from constants import S_DATA, S_LOG, yml_to_obj
from logic_app import create_logic_router, start_logic, stop_logic
from state import _logic_state, get_logic_state
from webhook import send_to_webhook_async

log_dir = Path(__file__).parent.parent / "data"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "log.txt"

logger = logging.getLogger(__name__)

LOCK_FILE = Path(__file__).parent.parent / "data" / "app.pid"


def check_pid_lock() -> bool:
    if not LOCK_FILE.exists():
        return True
    try:
        old_pid = int(LOCK_FILE.read_text().strip())
        try:
            os.kill(old_pid, 0)
            logger.error(f"Another instance is running (PID: {old_pid}). Exiting.")
            return False
        except OSError:
            logger.info(f"Stale lock file found (PID: {old_pid}). Proceeding.")
            return True
    except (ValueError, IOError):
        return True


def acquire_pid_lock() -> None:
    LOCK_FILE.write_text(str(os.getpid()))
    logger.info(f"PID lock acquired: {os.getpid()}")


def release_pid_lock() -> None:
    if LOCK_FILE.exists():
        try:
            current_pid = int(LOCK_FILE.read_text().strip())
            if current_pid == os.getpid():
                LOCK_FILE.unlink()
                logger.info("PID lock released")
        except (ValueError, IOError):
            pass


def get_auth_credentials() -> Optional[tuple[str, str]]:
    auth = os.environ.get("HTTP_AUTH", "")
    if not auth:
        return None
    try:
        username, password = auth.split(":", 1)
        return (username, password)
    except ValueError:
        return None


def verify_basic_auth(request) -> bool:
    credentials = get_auth_credentials()
    if credentials is None:
        return True
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return False
    try:
        encoded = auth_header[6:]
        decoded = b64decode(encoded).decode("utf-8")
        provided_user, provided_pass = decoded.split(":", 1)
        return provided_user == credentials[0] and provided_pass == credentials[1]
    except Exception:
        return False


def load_page_template(name: str) -> str:
    templates_dir = Path(__file__).parent / "templates"
    template_path = templates_dir / f"{name}.html"
    return template_path.read_text()


class ScheduleConfig:
    def __init__(self):
        self.enabled = True
        self.start_hour = 13
        self.start_minute = 5
        self.end_hour = 15
        self.end_minute = 31
        self.trading_days = [0, 1, 2, 3, 4]
        self.trading_day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    def is_within_schedule(self) -> bool:
        if not self.enabled:
            return True
        if _logic_state.is_paused():
            return False
        now = datetime.now()
        if now.weekday() not in self.trading_days:
            return False
        current_minutes = now.hour * 60 + now.minute
        start_minutes = self.start_hour * 60 + self.start_minute
        end_minutes = self.end_hour * 60 + self.end_minute
        return start_minutes <= current_minutes < end_minutes

    def is_paused(self) -> bool:
        return _logic_state.is_paused()

    def pause_reason(self) -> str:
        if _logic_state.paused and _logic_state.pause_until:
            remaining = (_logic_state.pause_until - datetime.now()).total_seconds()
            if remaining > 0:
                return f"{_logic_state.pause_reason} ({int(remaining)}s)"
        return ""

    def can_start(self) -> bool:
        return self.is_within_schedule() and not _logic_state.is_running()

    def time_until_start(self) -> str:
        if not self.enabled or self.is_within_schedule():
            return "now"
        now = datetime.now()
        start_minutes = self.start_hour * 60 + self.start_minute
        current_minutes = now.hour * 60 + now.minute
        mins_until = start_minutes - current_minutes
        if mins_until < 0:
            mins_until += 1440
        hours = mins_until // 60
        mins = mins_until % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    def time_until_end(self) -> str:
        if not self.enabled or not self.is_within_schedule():
            return "outside"
        now = datetime.now()
        end_minutes = self.end_hour * 60 + self.end_minute
        current_minutes = now.hour * 60 + now.minute
        mins_until = end_minutes - current_minutes
        if mins_until <= 0:
            return "now"
        hours = mins_until // 60
        mins = mins_until % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"


schedule_config = ScheduleConfig()
scheduler = AsyncIOScheduler()


async def scheduled_start():
    if schedule_config.can_start():
        await start_logic()


async def scheduled_stop():
    if _logic_state.is_running() and not schedule_config.is_within_schedule():
        await stop_logic()


async def watchdog_check():
    if schedule_config.is_within_schedule() and not _logic_state.is_running():
        await start_logic()
    elif not schedule_config.is_within_schedule() and _logic_state.is_running():
        await stop_logic()


def get_memory_usage() -> dict:
    gc.collect()
    logic_size = sys.getsizeof(_logic_state)
    startup_size = sys.getsizeof(_logic_state.startup_data)
    app_size = sys.getsizeof(_logic_state.app_data)
    ws_size = sys.getsizeof(_logic_state.ws_client)
    return {
        "logic_state_bytes": logic_size,
        "startup_data_bytes": startup_size or 0,
        "app_data_bytes": app_size or 0,
        "ws_client_bytes": ws_size or 0,
        "total_bytes": (startup_size or 0) + (app_size or 0) + (ws_size or 0),
    }


async def trading_session_start(app: FastAPI):
    if _logic_state.is_running():
        logging.info("Trading session already running")
        return
    await start_logic()


async def trading_session_stop(app: FastAPI):
    if not _logic_state.is_running():
        return
    await stop_logic()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.logic = _logic_state

    from api import remove_token
    tokpath = S_DATA + "token.txt"
    if os.path.exists(tokpath):
        os.remove(tokpath)
        logger.info("Broker token invalidated on startup - forcing fresh login")

    global _is_lock_enabled
    if _is_lock_enabled:
        if not check_pid_lock():
            logger.error("Another instance is running. Exiting.")
            sys.exit(1)
        acquire_pid_lock()

    if schedule_config.enabled:
        scheduler.add_job(
            watchdog_check,
            trigger=IntervalTrigger(seconds=60),
            id="watchdog_check",
        )
        scheduler.start()

        scheduler.add_job(
            trading_session_start,
            trigger=CronTrigger(day_of_week="mon-fri", hour=13, minute=5),
            id="start_session",
            args=[app],
        )
        scheduler.add_job(
            trading_session_stop,
            trigger=CronTrigger(day_of_week="mon-fri", hour=15, minute=31),
            id="stop_session",
            args=[app],
        )

        from datetime import datetime
        now = datetime.now()
        if now.weekday() < 5:
            hour_min = now.hour * 60 + now.minute
            market_start = 13 * 60 + 5
            market_end = 15 * 60 + 31
            if market_start <= hour_min < market_end:
                await trading_session_start(app)

    logger.info(f"Server Started - Trading scheduled {schedule_config.start_hour:02d}:{schedule_config.start_minute:02d}-{schedule_config.end_hour:02d}:{schedule_config.end_minute:02d} Mon-Fri")
    yield

    if scheduler.running:
        scheduler.shutdown()
    await trading_session_stop(app)
    release_pid_lock()


app = FastAPI(
    title="Power Option",
    description="Real-time option trading terminal",
    version="1.0.0",
    lifespan=lifespan,
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory="templates")

_is_lock_enabled = os.environ.get("SKIP_PID_LOCK", "") != "1"


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not verify_basic_auth(request):
        return Response(
            content="Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Restricted"'},
        )
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if _logic_state.is_running() and schedule_config.is_within_schedule():
        from symbols import find_base
        symbols = find_base()
        return templates.TemplateResponse(request=request, name="index.html", context={"symbols": symbols})
    return HTMLResponse(load_page_template("sleeping"))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    from symbols import find_base
    symbols = find_base()
    return templates.TemplateResponse(request=request, name="index.html", context={"symbols": symbols})


@app.get("/sleeping", response_class=HTMLResponse)
async def sleeping_page():
    return HTMLResponse(load_page_template("sleeping"))


@app.get("/api/memory")
async def memory_info():
    memory = get_memory_usage()
    return {
        "running": _logic_state.running,
        "has_startup_data": _logic_state.startup_data is not None,
        "has_app_data": _logic_state.app_data is not None,
        "has_ws_client": _logic_state.ws_client is not None,
        "schedule_enabled": schedule_config.enabled,
        "within_schedule": schedule_config.is_within_schedule(),
        "time_until_end": schedule_config.time_until_end(),
        **memory,
    }


@app.get("/api/schedule")
async def schedule_info():
    return {
        "enabled": schedule_config.enabled,
        "start_time": f"{schedule_config.start_hour:02d}:{schedule_config.start_minute:02d}",
        "end_time": f"{schedule_config.end_hour:02d}:{schedule_config.end_minute:02d}",
        "within_schedule": schedule_config.is_within_schedule(),
        "time_until_start": schedule_config.time_until_start(),
        "time_until_end": schedule_config.time_until_end(),
        "running": _logic_state.is_running(),
        "paused": schedule_config.is_paused(),
        "pause_reason": schedule_config.pause_reason(),
        "schedule_times": f"{schedule_config.start_hour:02d}:{schedule_config.start_minute:02d} - {schedule_config.end_hour:02d}:{schedule_config.end_minute:02d}",
        "trading_days": schedule_config.trading_day_names,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    feed_task = asyncio.create_task(market_broadcaster(websocket))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        feed_task.cancel()


async def market_broadcaster(websocket: WebSocket):
    try:
        while True:
            app_data = _logic_state.app_data
            if app_data and app_data.get("ws"):
                ticks = app_data["ws"].ltp()
                if ticks:
                    payload = {
                        "type": "UPDATE",
                        "diff_rows": assemble_table_rows("main", ticks, app_data),
                        "hedge_rows": assemble_table_rows("hedge", ticks, app_data),
                        "main_fresh": app_data.get("checkbox", {}).get("main", 0),
                        "hedge_fresh": app_data.get("checkbox", {}).get("hedge", 0),
                    }
                    await websocket.send_json(payload)
                    app_data["checkbox"]["main"] = 0
                    app_data["checkbox"]["hedge"] = 0
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Broadcaster Error: {e}")


def assemble_table_rows(side, ticks, app_data):
    rows = []
    subscribed = app_data.get("subscribed", {}).get(side, [])
    metadata = app_data.get("metadata", {})

    if not subscribed or not ticks:
        return rows

    half = len(subscribed) // 2

    for i in range(half):
        ce_t = subscribed[i]
        pe_t = subscribed[i + half]

        ce_m = metadata.get(ce_t)
        pe_m = metadata.get(pe_t)

        if not ce_m or not pe_m:
            continue

        c_ce = ticks.get(ce_t, ce_m["prev"])
        c_pe = ticks.get(pe_t, pe_m["prev"])

        ce_diff = round(c_ce - ce_m["prev"], 2)
        pe_diff = round(c_pe - pe_m["prev"], 2)
        total_diff = round(ce_diff + pe_diff, 2)

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
                "ce_diff_pct": round((ce_diff / ce_m["prev"]) * 100, 2) if ce_m["prev"] else 0,
                "pe_diff_pct": round((pe_diff / pe_m["prev"]) * 100, 2) if pe_m["prev"] else 0,
                "total_diff_pct": round((total_diff / (ce_m["prev"] + pe_m["prev"])) * 100, 2)
                if (ce_m["prev"] + pe_m["prev"]) else 0,
            }
        )
    return rows


@app.get("/logs")
async def get_logs():
    try:
        with open(S_LOG, "r") as f:
            lines = f.readlines()[-200:]
        return Response(content="".join(lines), media_type="text/plain")
    except Exception as e:
        logging.error(f"Error reading logs: {e}")
        return Response(content=f"Error reading logs: {e}", media_type="text/plain")


logic_router = create_logic_router()
app.include_router(logic_router, prefix="/api/logic")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
