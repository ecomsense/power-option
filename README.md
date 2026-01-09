# Option Trading Dashboard

A real-time, high-performance option trading terminal built with FastAPI and WebSockets. [cite_start]This application allows for monitoring NIFTY/BANKNIFTY/FINNIFTY option chains, visualizing premium data via TradingView Lightweight Charts, and executing multi-leg strategies with automated order slicing[cite: 1, 2, 13].

## 📁 Project Structure

```text
.
├── data/               # Market master files, logs, and local settings
├── factory/            # Configuration templates
├── requirements.txt    # Python dependencies
└── src/                # Application source code
    ├── main.py         # FastAPI entry point
    ├── api.py          # Broker API & Order slicing logic
    ├── wsocket.py      # WebSocket management
    ├── static/         # Frontend assets (dashboard.js, style.css)
    └── templates/      # HTML UI (index.html)
