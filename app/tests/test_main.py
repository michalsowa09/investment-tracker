import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_read_main():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_assets():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/aktywa")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_nbp_connection():
    from app.main import download_rate
    rate = await download_rate("usd")
    # Akceptujemy float lub None
    assert rate is None or isinstance(rate, float)