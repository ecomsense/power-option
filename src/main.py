from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn


from constants import O_SETG, logging
from symbols import dump, Symbols
from utils import dict_from_yml
from api import Helper


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # download necessary masters
        dump()
        # Unpack settings into instance attributes
        symbol_settings = dict_from_yml("name", O_SETG["base"])
        default_symbol = Symbols(**symbol_settings)

        filtered = default_symbol.new_chain(59251, full_chain=True)
        print(filtered)
        # Store the authenticated API instance in app.state
        # This performs the "login once" action
        app.state.api = Helper.api()

        logging.info("Login Successful - HAPPY TRADING")
        yield
    except Exception as e:
        logging.error(f"Startup login Error {e}")
        yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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


if __name__ == "__main__":
    # Specify the file and app object as a string for 'reload' to work
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
