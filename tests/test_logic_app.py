import pytest
import os
import sys
from httpx import AsyncClient, ASGITransport

os.environ["SKIP_PID_LOCK"] = "1"
sys.path.insert(0, "src")

from main import app


class TestLogicApp:
    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_start_logic(self, client):
        response = await client.post("/api/logic/start")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_status_when_stopped(self, client):
        await client.post("/api/logic/stop")
        response = await client.get("/api/logic/status")
        assert response.status_code == 200
        data = response.json()
        assert data["running"] == False

    @pytest.mark.asyncio
    async def test_stop_logic(self, client):
        await client.post("/api/logic/start")
        response = await client.post("/api/logic/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_cannot_stop_when_not_running(self, client):
        await client.post("/api/logic/stop")
        response = await client.post("/api/logic/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_stopped"

    @pytest.mark.asyncio
    async def test_order_place_requires_running(self, client):
        response = await client.post(
            "/api/logic/order_place",
            json={"orders": ["cb-main-ce-22000"], "quantity": 1, "order_code": "LE", "tag": "main"}
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_update_subscription_requires_running(self, client):
        response = await client.post(
            "/api/logic/update-subscription",
            json={"side": "main", "basename": "NIFTY", "expiry": "2026-05-01", "ce_start": 22000, "pe_start": 22000, "num_of_strikes": 5}
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_settings_endpoint_get(self, client):
        response = await client.get("/api/logic/settings")
        assert response.status_code == 200
        data = response.json()
        assert "webhook_url" in data or "status" in data

    @pytest.mark.asyncio
    async def test_trading_status_endpoint(self, client):
        response = await client.get("/api/logic/trading-status")
        assert response.status_code == 200
        data = response.json()
        assert "trading_active" in data
        assert "countdown_label" in data


class TestSymbols:
    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_get_symbols(self, client):
        response = await client.get("/api/logic/symbols")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_expiries(self, client):
        response = await client.get("/api/logic/expiries/NIFTY")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_strikes(self, client):
        import pendulum
        expiry = pendulum.now("Asia/Kolkata").add(days=7).format("YYYY-MM-DD")
        response = await client.get(f"/api/logic/strikes/NIFTY/{expiry}")
        assert response.status_code == 200
        data = response.json()
        assert "CE" in data
        assert "PE" in data