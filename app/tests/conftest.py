import pytest
import asyncio
from app.database import engine
from app.models import Base

# To mówi pytestowi, żeby użył odpowiedniej wtyczki asynchronicznej
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    # Tworzymy tabele przed testami
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Czyścimy bazę po testach
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)