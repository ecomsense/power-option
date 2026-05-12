# Power Option - Agent Context

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 CONTROLLER (main.py)                        │
│  - APScheduler for auto start/stop within schedule          │
│  - PID lock to prevent multiple instances                   │
│  - HTTP Basic Auth                                          │
│  - Serves sleeping.html or logic.html based on schedule     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 LOGIC APP                                   │
│  - Trading session (TickRunner, Strategy, Wserver)          │
│  - State stored in src/state.py (LogicState)                 │
│  - Start/Stop/Pause via /api/logic/* endpoints              │
└─────────────────────────────────────────────────────────────┘
```

## Schedule (hardcoded in ScheduleConfig class)

| Setting | Value |
|---------|-------|
| Start | 09:15 IST (00:05 for dev testing) |
| End | 15:31 IST |
| Days | Mon-Fri |

## UI Structure

### Header (shared)
```html
<div class='app-header'>
  <div class='header-left'>
    <span class='logo'>⚡</span>
    <span class='title'>Power Option</span>
  </div>
  <div class='header-right'>
    <button class='icon-btn'>⚙️</button>
    <button class='icon-btn'>📋</button>
    <button class='icon-btn'>🌙</button>
  </div>
</div>
```

### Footer (shared)
```html
<footer class='app-footer'>
  Made with <span class='heart'>❤</span> by <a href='https://ecomsense.in'>ecomsense.in</a>
</footer>
```

## CSS Classes

| Class | Purpose |
|-------|---------|
| `.app-header` | Header bar with flex space-between |
| `.header-left` | Left side: logo + title |
| `.header-right` | Right side: icon buttons |
| `.icon-btn` | Action buttons (⚙️📋🌙) |
| `.main-body` | Flex container for main content |
| `.modal` / `.modal-content` | Modal overlays |
| `.schedule-card` | Schedule display on sleeping page |
| `.app-footer` | Sticky footer with branding |

## Route Structure

| Path | Description |
|------|-------------|
| `/` | Root - sleeping or logic page based on schedule |
| `/api/schedule` | Schedule info, within_schedule, times |
| `/api/logic/start` | Start trading session |
| `/api/logic/stop` | Stop trading session |
| `/api/logic/status` | Running, paused, pause_reason |
| `/api/logic/settings` | Read/write settings.yml |
| `/admin/logs` | Server log content |
| `/ws` | WebSocket for real-time data |

## Server

**IP**: 65.20.75.117 | **User**: trader

### Commands
```bash
# Check status
systemctl --user status fastapi_app.service

# Restart (ONLY use systemctl - NEVER start uvicorn directly)
systemctl --user restart fastapi_app.service

# Logs
tail -50 /home/trader/no_env/power-option/data/log.txt

# Check API
curl -s http://127.0.0.1:8000/api/schedule
curl -s http://127.0.0.1:8000/api/logic/status
```

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Controller, ScheduleConfig, routes |
| `src/logic_app.py` | Trading session start/stop |
| `src/state.py` | LogicState singleton |
| `src/api.py` | Broker API integration |
| `src/wsocket.py` | WebSocket manager |
| `src/symbols.py` | Trading symbols from broker |
| `src/static/style.css` | Shared CSS for both pages |
| `src/static/dashboard.js` | Main UI logic |
| `templates/sleeping.html` | Countdown page |
| `templates/index.html` | Trading charts + dashboard |

## Order Codes

- `LE`/`SE` - Buy/Sell (immediate execution)
- `LX`/`SX` - Buy/Sell Square (Stoxxo-reviewed, delayed execution)

## Checkbox IDs

Format: `cb-{table}-{type}-{strike}` e.g., `cb-main-ce-22000`

## WebSocket

- Real-time market data via KiteTicker
- Streaming option chain prices
- Order update notifications

## Known Issues

| Issue | Status |
|-------|--------|
| nginx WebSocket 403 | Not fixed yet |
| sys.exit(1) crash handling | Pending architecture decision |

## Issues

- `issue`: refactor: remove unused imports and variables
- `pre: scripts/*.sh`: N/A
- `commit`: refactor: remove unused imports and variables
- `post: scripts/*.sh`: N/A

**Commit:** 47e1cdb (also 3b38593 for revert of _ prefix change)
**Revert:** git reset --hard 1eea502