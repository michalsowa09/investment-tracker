import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_read_main():
    # ASGITransport to najbezpieczniejszy sposób testowania FastAPI
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
    from app.main import download_rate
    # Sprawdzamy czy integracja z NBP nie rzuca błędami kodu
    rate = await download_rate("usd")
    assert rate is None or isinstance(rate, float)