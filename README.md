# Power Option

A real-time, high-performance option trading terminal built with FastAPI and WebSockets. Monitors NIFTY/BANKNIFTY/FINNIFTY option chains, visualizes premium data via TradingView Lightweight Charts, and executes multi-leg strategies with automated order slicing.

## Features

- Real-time option chain monitoring with live price updates via WebSocket
- Automated trading session management (auto start/stop within market hours)
- NIFTY, BANKNIFTY, FINNIFTY support
- Multi-leg strategy execution with order slicing
- PID lock to prevent multiple instances
- HTTP Basic Authentication
- TradingView Lightweight Charts integration

## Setup

### 1. Clone and Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows
git clone https://github.com/ecomsense/power-option
cd power-option
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

Copy the example config and fill in your credentials:

```bash
cp factory/power-option.yml data/power-option.yml
```

Required settings in `data/power-option.yml`:
- Broker API credentials (api_key, api_secret, totp_secret)
- Trading parameters (symbols, lot sizes, strike ranges)

### 4. Set Environment Variables

```bash
export HTTP_AUTH="username:password"   # Basic auth for UI
export SKIP_PID_LOCK="0"               # Set to "1" to skip PID lock (dev only)
```

### 5. Deploy as Systemd Service

```bash
# Copy service file (adjust paths as needed)
cp factory/fastapi_app.service ~/.config/systemd/user/

# Enable and start
systemctl --user daemon-reload
systemctl --user enable fastapi_app.service
systemctl --user start fastapi_app.service
```

## Running the Application

**Always use systemd to manage the service** (never run uvicorn directly):

```bash
systemctl --user status fastapi_app.service  # Check status
systemctl --user restart fastapi_app.service  # Restart after changes
systemctl --user stop fastapi_app.service    # Stop
```

## Project Structure

```
power-option/
├── data/                  # Runtime data (config, logs, state)
├── factory/               # Configuration templates
├── scripts/               # Utility scripts
├── src/                   # Application source code
│   ├── static/            # Frontend assets (JS, CSS)
│   ├── templates/         # HTML templates
│   ├── api.py             # Broker API integration & order slicing
│   ├── constants.py       # Configuration & path constants
│   ├── logic_app.py       # Trading session management
│   ├── main.py            # FastAPI entry point & routes
│   ├── state.py           # LogicState singleton
│   ├── symbols.py         # Trading symbols
│   ├── webhook.py         # Webhook notifications
│   ├── wsocket.py         # WebSocket management
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
└── pyproject.toml         # Project metadata
```

## API Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/` | GET | Root - serves sleeping or dashboard based on schedule |
| `/api/schedule` | GET | Schedule info (start/end times, within_schedule) |
| `/api/memory` | GET | Memory usage statistics |
| `/api/logic/start` | POST | Start trading session |
| `/api/logic/stop` | POST | Stop trading session |
| `/api/logic/status` | GET | Session status (running, paused) |
| `/api/logic/pause` | POST | Pause session with reason |
| `/api/logic/resume` | POST | Resume paused session |
| `/api/logic/settings` | GET/POST | Read/write settings.yml |
| `/ws` | WS | WebSocket for real-time updates |
| `/logs` | GET | Server log content |

## Schedule

Trading runs automatically Mon-Fri within market hours:

| Setting | Value |
|---------|-------|
| Start | 09:15 IST |
| End | 15:31 IST |
| Days | Mon-Fri |

The application auto-starts and auto-stops within this window. Outside hours, a countdown page is shown.

## Server Deployment

| Setting | Value |
|---------|-------|
| IP | 65.20.75.117 |
| User | trader |
| Service | fastapi_app.service |

```bash
# Check API status
curl -s http://127.0.0.1:8000/api/schedule
curl -s http://127.0.0.1:8000/api/logic/status

# View logs
tail -50 data/log.txt
```

## Development

### Running Locally

```bash
cd src
python main.py
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `HTTP_AUTH` | Basic auth credentials (format: user:pass) |
| `SKIP_PID_LOCK` | Set to "1" to disable PID lock check |

### Order Codes

| Code | Action |
|------|--------|
| `LE` / `SE` | Buy / Sell (immediate execution) |
| `LX` / `SX` | Buy / Sell Square (Stoxxo-reviewed, delayed) |