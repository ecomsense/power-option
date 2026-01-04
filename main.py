from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from py5paisa import FivePaisaClient
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuration and 5paisa Client Setup
# Replace with your actual credentials
cred = {
    "APP_NAME": "YOUR_APP_NAME",
    "APP_SOURCE": "YOUR_APP_SOURCE",
    "USER_ID": "YOUR_USER_ID",
    "PASSWORD": "YOUR_PASSWORD",
    "USER_KEY": "YOUR_USER_KEY",
    "ENCRYPTION_KEY": "YOUR_ENCRYPTION_KEY",
}
client = FivePaisaClient(cred=cred)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def hospitals_connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    with open("templates/index.html") as f:
        return HTMLResponse(content=f.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.hospitals_connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Logic to handle subscription to specific strikes
            # and broadcasting market feed from 5paisa
            await websocket.send_text(f"Msg was: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Order Slicing Logic
def slice_order(scrip_code, qty, side, price):
    FREEZE_QTY = 1800  # Example for NIFTY
    orders = []
    while qty > 0:
        current_slice = min(qty, FREEZE_QTY)
        # client.place_order(OrderType='B', Exchange='N', ExchangeType='D', ScripCode=scrip_code, Qty=current_slice, Price=price)
        orders.append({"scrip": scrip_code, "qty": current_slice})
        qty -= current_slice
    return orders


if __name__ == "__main__":
    # Specify the file and app object as a string for 'reload' to work
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
