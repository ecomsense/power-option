# Power Option - Project Documentation

## Overview
A real-time options trading dashboard built with FastAPI for Indian stock market (Zerodha broker).

## Project Structure

```
power-option/
├── src/
│   ├── main.py          # FastAPI server, WebSocket, order endpoints
│   ├── api.py           # Zerodha auth & historical data
│   ├── symbols.py       # Download/cache option instruments
│   ├── wsocket.py       # WebSocket manager for live ticks
│   ├── constants.py     # Config, logging, paths
│   ├── utils.py         # Helper utilities
│   ├── templates/
│   │   └── index.html   # Main dashboard UI
│   └── static/
│       ├── dashboard.js # Table rendering, order placement
│       ├── dropdown.js  # Cascading dropdowns
│       ├── toggle.js    # Buy/Sell toggle
│       └── style.css    # Styling
├── factory/
│   ├── symbols.yml      # Symbol config (BANKNIFTY, SENSEX, NIFTY)
│   └── settings.yml    # Webhook URL, credentials
└── data/
    ├── CE/             # Call options CSV files
    ├── PE/             # Put options CSV files
    └── NFO.json, BFO.json  # Raw instrument data
```

## Key Endpoints

- `GET /` - Dashboard page
- `GET /get-expiries/{basename}` - Get expiries for symbol
- `GET /get-strikes/{basename}/{expiry}` - Get strike prices
- `POST /update-subscription` - Subscribe to options
- `POST /order_place` - Place orders via webhook
- `WS /ws` - Real-time price updates

## Data Flow

1. Startup: Downloads option chain from Kite API → stores in `data/CE/`, `data/PE/`
2. WebSocket: Connects to Zerodha for live tick data
3. User selects: Symbol → Expiry → Strike range
4. Server subscribes to options → broadcasts to UI every second
5. "Fire" sends entry orders, "Square" sends exit orders via webhook to `https://stoxxo.com`

## Features

- **Diff Table**: 14 columns showing price change from previous close
- **Hedge Table**: 6 columns showing live LTP
- Checkboxes to select strikes for orders
- Toggle between BUY/SELL mode
- Chart showing cumulative diff over time

## Configuration

- `factory/symbols.yml` - Define symbols (BANKNIFTY, SENSEX, NIFTY)
- `factory/settings.yml` - Webhook URL, timeout, logging

## Dependencies

- FastAPI, Uvicorn
- pandas, kiteconnect, zerodha (stock_brokers)
- httpx, pendulum, lightweight-charts