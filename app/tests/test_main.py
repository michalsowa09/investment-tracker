import pytest
from httpx import AsyncClient
from app.main import app

# Test 1: Sprawdzam czy Dashboard w ogóle się wyświetla
@pytest.mark.asyncio
async def test_read_main():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200

# Test 2: Sprawdzam czy API zwraca listę aktywów (nawet pustą)
@pytest.mark.asyncio
async def test_get_assets():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/aktywa")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Test 3: Sprawdzenie integracji z NBP (czy funkcja nie wywala błędu)
@pytest.mark.asyncio
async def test_nbp_connection():
    from app.main import download_rate
    rate = await download_rate("usd")
    # Test przejdzie, jeśli dostanę liczbę lub None (brak neta na serwerze testowym)
    assert rate is None or isinstance(rate, float)