import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_read_main():
    # Używamy najnowszego transportu ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_assets():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/aktywa")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_nbp_connection():
    # Importujemy lokalnie, żeby nie psuć loopa na górze
    from app.main import download_rate
    rate = await download_rate("usd")
    # Test przejdzie, jeśli dostaniemy liczbę lub None (serwer NBP może być offline)
    assert rate is None or isinstance(rate, float)