import pytest
import os
import sys
from httpx import AsyncClient, ASGITransport

os.environ["SKIP_PID_LOCK"] = "1"
sys.path.insert(0, "src")

from main import app


class TestPages:
    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_root_page(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_dashboard_page(self, client):
        response = await client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_sleeping_page(self, client):
        response = await client.get("/sleeping")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Market" in response.text

    @pytest.mark.asyncio
    async def test_logs_endpoint(self, client):
        response = await client.get("/logs")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_memory_endpoint(self, client):
        response = await client.get("/api/memory")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "schedule_enabled" in data

    @pytest.mark.asyncio
    async def test_websocket_endpoint(self, client):
        async with client.stream("GET", "/ws") as response:
            assert response.status_code == 101  # WebSocket upgrade


class TestState:
    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_state_singleton(self):
        from state import _logic_state, get_logic_state
        assert _logic_state is get_logic_state()

    @pytest.mark.asyncio
    async def test_state_initial_values(self):
        from state import LogicState
        state = LogicState()
        assert state.running == False
        assert state.started_at == None
        assert state.startup_data == None
        assert state.app_data == None
        assert state.ws_client == None

    @pytest.mark.asyncio
    async def test_state_is_running(self):
        from state import LogicState
        state = LogicState()
        assert state.is_running() == False
        state.running = True
        assert state.is_running() == True

    @pytest.mark.asyncio
    async def test_state_is_paused(self):
        from state import LogicState
        from datetime import datetime, timedelta
        state = LogicState()
        state.paused = True
        state.pause_until = datetime.now() + timedelta(seconds=10)
        assert state.is_paused() == True