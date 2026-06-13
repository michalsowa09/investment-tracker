import pytest
import asyncio
from app.database import engine
from app.models import Base

@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    # To polecenie stworzy tabele w czystej bazie GitHuba przed testami
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Opcjonalnie: usuwanie tabel po testach
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)