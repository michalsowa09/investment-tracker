import pytest
from app.database import engine
from app.models import Base


# Usuwamy stąd funkcję event_loop - niech pytest-asyncio sam ją sobie robi
@pytest.fixture(autouse=True)  # Domyślny zasięg to "function"
async def setup_database():
    # 1. Przed każdym testem twórz tabele
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Tu wykonuje się test

    # 2. Po każdym teście czyść bazę
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)