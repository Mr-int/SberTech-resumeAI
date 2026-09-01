import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def stub_gigachat(monkeypatch):
    from app.api import dependencies

    monkeypatch.setenv("GIGACHAT_USE_STUB", "true")
    monkeypatch.setenv("GIGACHAT_AUTH_KEY", "")
    monkeypatch.setenv("GIGACHAT_API_KEY", "")
    get_settings.cache_clear()
    dependencies.get_gigachat_client.cache_clear()


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


@pytest.mark.asyncio
async def test_messenger_chat_rejects_profanity(client):
    payload = {"message": {"text": "Составь резюме, я хуй знает кем работать"}}
    response = await client.post("/api/v1/chat", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Модерация" in detail
    assert "грубая лексика" in detail
    assert "сообщение" in detail
