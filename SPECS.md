# Power Option - Specifications

## Project Overview
Real-time option trading terminal for NIFTY/BANKNIFTY/FINNIFTY with WebSocket streaming, automated order slicing, and TradingView charts.

## Directory Structure
```
power-option/
├── factory/              # Configuration templates
├── data/                # Runtime state (logs, credentials)
├── tests/               # Unit/integration tests
├── requirements.txt    # Python dependencies
└── src/
    ├── main.py         # FastAPI entry point, webhook endpoints
    ├── api.py          # Broker API integration
    ├── constants.py   # Singleton configurations
    ├── symbols.py    # Trading symbols from broker
    ├── wsocket.py     # WebSocket management
    ├── static/        # Frontend JS/CSS
    │   ├── dashboard.js   # Main UI logic
    │   ├── toggle.js
    │   ├── dropdown.js
    │   └── style.css
    └── templates/     # HTML templates
        └── index.html
```

## Key Patterns

### Order Codes
- `LE`/`SE` - Buy/Sell (immediate execution)
- `LX`/`SX` - Buy/Sell Square (Stoxxo-reviewed, delayed execution)

### API Endpoints
- `POST /order_place` - Batch order (multiple trading symbols)
- `POST /order_place_one` - Single order (for X codes to send one-by-one)
- `POST /update-subscription` - Update option chain
- `WebSocket /ws` - Real-time data streaming

### Frontend Flow
1. `mainSquare()` / `hedgeSquare()` → `placeSquareOrder()` → sends one-by-one to `/order_place_one`
2. `mainFire()` / `hedgeFire()` → `placeOrder()` → batch to `/order_place`

### Checkbox IDs
Format: `cb-{table}-{type}-{strike}` e.g., `cb-main-ce-22000`, `cb-hedge-pe-23500`

## Server Info
- User: `trader`
- IP: `65.20.75.117`
- Path: `/home/trader/no_env/power-option`
- Service: `fastapi_app.service` (systemd managed)

## CRITICAL RULES
### NEVER start uvicorn directly
- ALWAYS use `systemctl restart fastapi_app` to restart the service
- NEVER run `uvicorn main:app` or `python -m uvicorn` directly via ssh
- If the app won't start, check `journalctl -u fastapi_app -n 20` for errors
- Use `systemctl status fastapi_app` to verify it's running

### NEVER upload files directly to server
- DON'T use scp, rsync, or any other file transfer method
- ALWAYS commit changes locally to git, then pull on the server
- This ensures all changes are tracked and reproducible

### ALWAYS send logic app errors to data/log.txt
- Trading/business logic errors go to data/log.txt (visible in UI)
- Main app/system errors go to low-level logging (journalctl)
- Keep business errors visible to users, system errors hidden

## Key Data Structures

### SYMBOL_LOOKUP
Lookup table in `app.state.SYMBOL_LOOKUP` for resolving (strike, type) → trading symbol. Used by order endpoints to parse checkbox IDs.

### Order ID Parsing
Checkbox IDs format: `cb-{table}-{type}-{strike}` e.g., `cb-main-ce-22000`
Parsed as: `["cb", "main", "ce", "22000"]` → type=CE, strike=22000

### Broker
Zerodha Kite API with WebSocket via KiteTicker for real-time market data.