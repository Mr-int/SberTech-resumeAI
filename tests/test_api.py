import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["gigachat_stub"] is True


@pytest.mark.asyncio
async def test_messenger_chat_stub(client):
    payload = {
        "message": {"text": "Помоги составить резюме программиста"},
    }
    response = await client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["stub"] is True
    assert "reply" in data
    assert "[STUB]" in data["reply"]["text"]
