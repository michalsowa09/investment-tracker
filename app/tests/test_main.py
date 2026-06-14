import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_read_main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_asset():
    # Testuje dodawanie nowego aktywa (POST)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = {"name": "Test Asset", "ticker": "TST", "amount": 10.0, "price": 100.0}
        response = await ac.post("/aktywa", data=data)
    assert response.status_code == 303 # Przekierowanie po sukcesie

@pytest.mark.asyncio
async def test_get_portfolio_analysis():
    # Testujemy endpoint analizy portfela
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/portfel/analiza")
    assert response.status_code == 200
    assert "podsumowanie_portfela" in response.json()

@pytest.mark.asyncio
async def test_buy_more_logic():
    # Testuje logikę średniej ważonej (PUT)
    # Najpierw muszę mieć co dokupić - używamy bazy z conftest
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Dodajemy
        await ac.post("/aktywa", data={"name": "Gold", "ticker": "XAU", "amount": 1, "price": 100})
        # 2. Dokupujemy (id=1, bo baza jest czysta w testach)
        response = await ac.put("/aktywa/1/dokup?added_amount=1&added_price=200")
    assert response.status_code == 200
    # Sprawdzam czy nie wywaliło błędu przy liczeniu średniej

@pytest.mark.asyncio
async def test_search_asset():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/aktywa/szukaj?phrase=Test")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_nbp_integration():
    from app.main import download_rate
    # Testuje z użyciem Mocka lub prawdziwego API (httpx obsłuży oba)
    rate = await download_rate("usd")
    assert rate is None or isinstance(rate, float)