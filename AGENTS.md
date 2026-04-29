# Power Option - Agent Guidelines

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

---

## Troubleshooting Checklist

When the app fails to start or crashes, check these in order:

### 1. Port 8000 Already in Use
```bash
# Check if something is using port 8000
fuser 8000/tcp
# Kill if needed
sudo fuser -k 8000/tcp
```
- Error: `address already in use`

### 2. PID File Permission Issues
```bash
# Check ownership
ls -la /home/trader/no_env/power-option/data/app.pid
# If owned by root, delete it
sudo rm /home/trader/no_env/power-option/data/app.pid
```
- Error: `PermissionError: Permission denied: 'app.pid'`
- Root-owned PID files cause startup crashes

### 3. Log File Issues
```bash
# Check if log file exists and is writable
ls -la /home/trader/no_env/power-option/data/log.txt
# If missing, create
touch /home/trader/no_env/power-option/data/log.txt
```
- Error: `No such file or directory: 'log.txt'`

### 4. systemd Service Errors
```bash
# Check journal for errors
journalctl --user -u fastapi_app.service -n 20 --no-pager
# Check status
systemctl --user status fastapi_app.service
```
- Error codes: `status=1/FAILURE`, `status=3/NOTIMPLEMENTED`

### 5. Broker Authentication Failures
```bash
# Check logs for broker errors
tail -50 /home/trader/no_env/power-option/data/log.txt | grep -i 'auth\|zerodha\|error'
```
- Error: `sys.exit(1)` in broker library
- The app should handle this gracefully (not crash)

### 6. WebSocket Connection Issues
```bash
# Check nginx proxy
curl -s http://127.0.0.1:8000/ws
# Test if app responds
curl -s http://127.0.0.1:8000/
```
- Error: `403 Forbidden` - nginx blocking WebSocket

---

## Code Fixes Verification

Temporary vs Permanent fixes - use checklist above:

| Issue | Fix Type | Permanent? |
|-------|----------|------------|
| Port 8000 in use | Kill process | Yes |
| Root-owned PID | Delete file | Yes (if app runs as trader) |
| Missing log file | Create file | Check file permissions |
| sys.exit(1) crash | Handle SystemExit in api.py | Need your approval for trading_app change |
| nginx WebSocket 403 | Config nginx | Not implemented yet |

---

## Session History (AI Session - Apr 29 2026)

### Issues Found and Resolutions

1. **Root-owned app.pid file**
   - Error: `PermissionError: Permission denied: 'app.pid'`
   - Cause: Previous run created file as root user
   - Fix: `sudo rm /home/trader/no_env/power-option/data/app.pid`
   - Resolution: Permanent - new PID created as trader user

2. **Systemd service incorrect paths**
   - Error: `No such file or directory` for python and working directory
   - Cause: Service file had `/home/trader/power-option/` instead of `/home/trader/no_env/power-option/`
   - Fix: Updated `factory/fastapi_app.service` with correct paths
   - Resolution: Permanent

3. **sys.exit(1) from broker library causing crash loop**
   - Error: Broker authentication failures causing `SystemExit: 1` in zerodha.py
   - Cause: External broker issues (not code related at this time)
   - Fix: Discussed trading_app architecture but user deferred implementation
   - Resolution: Pending - user to decide on architecture changes

4. **Port 8000 in use**
   - Error: `address already in use`
   - Fix: `sudo fuser -k 8000/tcp`
   - Resolution: Temporary - process cleanup

### Always Update AGENTS.md with Issues and Resolutions
- Document issues found and how they were resolved
- Mark fixes as Temporary or Permanent
- Note if external steps were required (outside code changes)
- This helps track whether solutions worked permanently